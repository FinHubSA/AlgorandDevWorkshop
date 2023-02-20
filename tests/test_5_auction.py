from base64 import b64decode
from time import time

from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.encoding import decode_address, encode_address
from algosdk.error import AlgodHTTPError
from algosdk.transaction import (
    ApplicationNoOpTxn,
    ApplicationOptInTxn,
    AssetCreateTxn,
    AssetOptInTxn,
    AssetTransferTxn,
    PaymentTxn,
    StateSchema,
)

from util.app import deploy_app
from util.client import algod_client
from util.account import AccountManager
from util.state_decode import decode_state


class TestAuction:
    def setup_method(self) -> None:
        """Create account(s) and app before each test."""

        account_manager = AccountManager()

        (
            self.manager_address,
            self.manager_txn_signer,
        ) = account_manager.create_new_funded_account()
        (
            self.seller_address,
            self.seller_txn_signer,
        ) = account_manager.create_new_funded_account()
        (
            self.bidder_address_1,
            self.bidder_txn_signer_1,
        ) = account_manager.create_new_funded_account()
        (
            self.bidder_address_2,
            self.bidder_txn_signer_2,
        ) = account_manager.create_new_funded_account()

        self.app_id, self.app_address = deploy_app(
            self.manager_txn_signer,
            "5_auction.teal",
            "clear.teal",
            algod_client.suggested_params(),
            StateSchema(num_uints=2, num_byte_slices=0),
            StateSchema(num_uints=3, num_byte_slices=0),
        )

        # Cover MBR of contract.
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=PaymentTxn(
                    sender=self.manager_address,
                    sp=algod_client.suggested_params(),
                    receiver=self.app_address,
                    amt=100_000,
                ),
                signer=self.manager_txn_signer,
            )
        )
        atc.execute(algod_client, 5)

    def test_create_auction(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        end_timestamp = int(time() + 5)
        base_price = 100_000
        buyout_price = 1_000_000

        asset_id = self._create_nft(
            self.seller_address, self.seller_txn_signer, unit_name, asset_name
        )

        box_name_bytes = self._create_auction(
            self.seller_address,
            self.seller_txn_signer,
            asset_id,
            end_timestamp,
            base_price,
            buyout_price,
        )
        asset_holding = algod_client.account_asset_info(self.app_address, asset_id)[
            "asset-holding"
        ]

        assert asset_holding["amount"] == 1

        global_state = decode_state(
            algod_client.application_info(self.app_id)["params"]["global-state"]
        )

        assert global_state["total_auctions"] == 1
        assert global_state["live_auctions"] == 1

        local_state = decode_state(
            algod_client.account_application_info(self.seller_address, self.app_id)[
                "app-local-state"
            ]["key-value"]
        )

        assert local_state["auctions_created"] == 1
        assert local_state["live_auctions"] == 1
        assert local_state["auctions_won"] == 0

        box = algod_client.application_box_by_name(
            self.app_id,
            box_name_bytes,
        )

        box_name = b64decode(box["name"])

        assert encode_address(box_name[:32]) + str(
            int.from_bytes(box_name[32:], "big")
        ) == self.seller_address + str(asset_id)

        box_value = b64decode(box["value"])

        box_end_timestamp = int.from_bytes(box_value[:8], "big")
        box_buyout_price = int.from_bytes(box_value[8:16], "big")
        box_current_price = int.from_bytes(box_value[16:24], "big")
        box_current_bidder = box_value[24:]

        assert box_end_timestamp == end_timestamp
        assert box_buyout_price == buyout_price
        assert box_current_price == base_price
        assert box_current_bidder == bytes(32)

    def test_place_bid(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        end_timestamp = int(time() + 5)
        base_price = 100_000
        buyout_price = 1_000_000

        sp = algod_client.suggested_params()
        sp.flat_fee = True

        asset_id = self._create_nft(
            self.seller_address, self.seller_txn_signer, unit_name, asset_name
        )

        box_name_bytes = self._create_auction(
            self.seller_address,
            self.seller_txn_signer,
            asset_id,
            end_timestamp,
            base_price,
            buyout_price,
        )

        bid_price = base_price * 2

        self._place_bid(
            self.bidder_address_1,
            self.bidder_txn_signer_1,
            0,
            asset_id,
            bid_price,
            box_name_bytes,
            [(0, box_name_bytes)],
        )

        asset_holding = algod_client.account_asset_info(
            self.bidder_address_1, asset_id
        )["asset-holding"]

        assert asset_holding["amount"] == 0

        box = algod_client.application_box_by_name(
            self.app_id,
            box_name_bytes,
        )

        box_value = b64decode(box["value"])

        box_end_timestamp = int.from_bytes(box_value[:8], "big")
        box_buyout_price = int.from_bytes(box_value[8:16], "big")
        box_current_price = int.from_bytes(box_value[16:24], "big")
        box_current_bidder = encode_address(box_value[24:])

        assert box_end_timestamp == end_timestamp
        assert box_buyout_price == buyout_price
        assert box_current_price == bid_price
        assert box_current_bidder == self.bidder_address_1

    def test_place_bid_buyout(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        end_timestamp = int(time() + 5)
        base_price = 100_000
        buyout_price = 1_000_000

        sp = algod_client.suggested_params()
        sp.flat_fee = True

        asset_id = self._create_nft(
            self.seller_address, self.seller_txn_signer, unit_name, asset_name
        )

        box_name_bytes = self._create_auction(
            self.seller_address,
            self.seller_txn_signer,
            asset_id,
            end_timestamp,
            base_price,
            buyout_price,
        )

        seller_balance_before: int = algod_client.account_info(self.seller_address)[
            "amount"
        ]

        bid_price = buyout_price

        self._place_bid(
            self.bidder_address_1,
            self.bidder_txn_signer_1,
            2,
            asset_id,
            bid_price,
            box_name_bytes,
            [(0, box_name_bytes)],
            [asset_id],
            [self.seller_address],
        )

        asset_holding = algod_client.account_asset_info(
            self.bidder_address_1, asset_id
        )["asset-holding"]

        assert asset_holding["amount"] == 1

        seller_balance_after: int = algod_client.account_info(self.seller_address)[
            "amount"
        ]

        assert seller_balance_after - seller_balance_before == bid_price

        try:
            algod_client.application_box_by_name(
                self.app_id,
                box_name_bytes,
            )
        except AlgodHTTPError as e:
            assert e.code == 404

    def test_place_bid_two(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        end_timestamp = int(time() + 5)
        base_price = 100_000
        buyout_price = 1_000_000

        sp = algod_client.suggested_params()
        sp.flat_fee = True

        asset_id = self._create_nft(
            self.seller_address, self.seller_txn_signer, unit_name, asset_name
        )

        box_name_bytes = self._create_auction(
            self.seller_address,
            self.seller_txn_signer,
            asset_id,
            end_timestamp,
            base_price,
            buyout_price,
        )

        bid_price_1 = base_price * 2

        self._place_bid(
            self.bidder_address_1,
            self.bidder_txn_signer_1,
            0,
            asset_id,
            bid_price_1,
            box_name_bytes,
            [(0, box_name_bytes)],
        )

        bid_price_2 = base_price * 3

        self._place_bid(
            self.bidder_address_2,
            self.bidder_txn_signer_2,
            1,
            asset_id,
            bid_price_2,
            box_name_bytes,
            [(0, box_name_bytes)],
            accounts=[self.bidder_address_1],
        )

        # TODO: assert that seller got paid

        asset_holding = algod_client.account_asset_info(
            self.bidder_address_2, asset_id
        )["asset-holding"]

        assert asset_holding["amount"] == 0

        box = algod_client.application_box_by_name(
            self.app_id,
            box_name_bytes,
        )

        box_value = b64decode(box["value"])

        box_end_timestamp = int.from_bytes(box_value[:8], "big")
        box_buyout_price = int.from_bytes(box_value[8:16], "big")
        box_current_price = int.from_bytes(box_value[16:24], "big")
        box_current_bidder = encode_address(box_value[24:])

        assert box_end_timestamp == end_timestamp
        assert box_buyout_price == buyout_price
        assert box_current_price == bid_price_2
        assert box_current_bidder == self.bidder_address_2

    def test_place_bid_buyout_two(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        end_timestamp = int(time() + 5)
        base_price = 100_000
        buyout_price = 1_000_000

        sp = algod_client.suggested_params()
        sp.flat_fee = True

        asset_id = self._create_nft(
            self.seller_address, self.seller_txn_signer, unit_name, asset_name
        )

        box_name_bytes = self._create_auction(
            self.seller_address,
            self.seller_txn_signer,
            asset_id,
            end_timestamp,
            base_price,
            buyout_price,
        )

        seller_balance_before: int = algod_client.account_info(self.seller_address)[
            "amount"
        ]

        bid_price_1 = base_price * 2

        self._place_bid(
            self.bidder_address_1,
            self.bidder_txn_signer_1,
            0,
            asset_id,
            bid_price_1,
            box_name_bytes,
            [(0, box_name_bytes)],
        )

        seller_balance_after: int = algod_client.account_info(self.seller_address)[
            "amount"
        ]

        assert seller_balance_after - seller_balance_before == 0

        bid_price_2 = buyout_price

        self._place_bid(
            self.bidder_address_2,
            self.bidder_txn_signer_2,
            3,
            asset_id,
            bid_price_2,
            box_name_bytes,
            [(0, box_name_bytes)],
            [asset_id],
            [self.bidder_address_1, self.seller_address],
        )

        asset_holding = algod_client.account_asset_info(
            self.bidder_address_2, asset_id
        )["asset-holding"]

        assert asset_holding["amount"] == 1

        seller_balance_after: int = algod_client.account_info(self.seller_address)[
            "amount"
        ]

        assert seller_balance_after - seller_balance_before == bid_price_2

        try:
            algod_client.application_box_by_name(
                self.app_id,
                box_name_bytes,
            )
        except AlgodHTTPError as e:
            assert e.code == 404

    def _create_nft(
        self,
        address: str,
        signer: AccountTransactionSigner,
        unit_name: str,
        asset_name: str,
    ) -> int:
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=AssetCreateTxn(
                    sender=address,
                    sp=algod_client.suggested_params(),
                    total=1,
                    decimals=0,
                    default_frozen=False,
                    unit_name=unit_name,
                    asset_name=asset_name,
                ),
                signer=signer,
            )
        )
        tx_id = atc.execute(algod_client, 5).tx_ids[0]
        asset_id: int = algod_client.pending_transaction_info(tx_id)["asset-index"]

        return asset_id

    def _create_auction(
        self,
        sender: str,
        signer: AccountTransactionSigner,
        asset_id: int,
        end_timestamp: int,
        base_price: int,
        buyout_price: int,
    ) -> bytes:
        sp = algod_client.suggested_params()
        sp.flat_fee = True

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationOptInTxn(sender=sender, sp=sp, index=self.app_id),
                signer=signer,
            )
        )
        atc.add_transaction(
            TransactionWithSigner(
                txn=PaymentTxn(
                    sender=sender,
                    sp=sp,
                    receiver=self.app_address,
                    amt=140900,  # box MBR + opt-in
                ),
                signer=signer,
            )
        )
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationNoOpTxn(
                    sender=sender,
                    sp=sp,
                    index=self.app_id,
                    app_args=["opt_in_asset", 0],  # 0 is the index of asset_id
                    foreign_assets=[asset_id],
                ),
                signer=signer,
            )
        )
        atc.add_transaction(
            TransactionWithSigner(
                txn=AssetTransferTxn(
                    sender=sender,
                    sp=sp,
                    receiver=self.app_address,
                    amt=1,
                    index=asset_id,
                ),
                signer=signer,
            )
        )
        sp.fee = sp.min_fee * 6
        box_name_bytes = decode_address(sender) + asset_id.to_bytes(8, "big")
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationNoOpTxn(
                    sender=sender,
                    sp=sp,
                    index=self.app_id,
                    app_args=[
                        "create_auction",
                        end_timestamp,
                        base_price,
                        buyout_price,
                    ],
                    boxes=[
                        (
                            0,
                            box_name_bytes,
                        )
                    ],
                ),
                signer=signer,
            )
        )
        atc.execute(algod_client, 5)

        return box_name_bytes

    def _place_bid(
        self,
        address: str,
        signer: AccountTransactionSigner,
        num_inner_txns: int,
        asset_id: int,
        bid_price: int,
        box_name_bytes: bytes,
        boxes: list = None,
        assets: list = None,
        accounts: list = None,
        asset_opt_in: bool = True,
        app_opt_in: bool = True,
    ) -> None:
        sp = algod_client.suggested_params()
        sp.flat_fee = True

        atc = AtomicTransactionComposer()
        if asset_opt_in:
            atc.add_transaction(
                TransactionWithSigner(
                    txn=AssetOptInTxn(
                        sender=address,
                        sp=sp,
                        index=asset_id,
                    ),
                    signer=signer,
                )
            )
        if app_opt_in:
            atc.add_transaction(
                TransactionWithSigner(
                    txn=ApplicationOptInTxn(sender=address, sp=sp, index=self.app_id),
                    signer=signer,
                )
            )
        atc.add_transaction(
            TransactionWithSigner(
                txn=PaymentTxn(
                    sender=address,
                    sp=sp,
                    receiver=self.app_address,
                    amt=bid_price,
                ),
                signer=signer,
            )
        )
        sp.fee = sp.min_fee * (2 + int(asset_opt_in) + int(app_opt_in) + num_inner_txns)
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationNoOpTxn(
                    sender=address,
                    sp=sp,
                    index=self.app_id,
                    app_args=["place_bid", box_name_bytes],
                    boxes=boxes,
                    foreign_assets=assets,
                    accounts=accounts,
                ),
                signer=signer,
            )
        )
        atc.execute(algod_client, 5)
