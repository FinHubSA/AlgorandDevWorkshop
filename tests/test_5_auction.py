from base64 import b64decode
from time import sleep, time

from algosdk.account import address_from_private_key
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
from util.client import algod_client, indexer_client
from util.account import AccountManager
from util.state_decode import decode_state

UNIT_NAME = "TEST"
ASSET_NAME = "My Test Ticket"
END_TIMESTAMP = int(time() + 1)
BASE_PRICE = 100_000
BUYOUT_PRICE = 1_000_000


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

    # def test_create_auction(self) -> None:
    #     asset_id = self._create_nft(self.seller_txn_signer)

    #     box_name_bytes = self._create_auction(self.seller_txn_signer, asset_id)

    #     asset_holding = algod_client.account_asset_info(self.app_address, asset_id)[
    #         "asset-holding"
    #     ]

    #     assert asset_holding["amount"] == 1

    #     global_state = decode_state(
    #         algod_client.application_info(self.app_id)["params"]["global-state"]
    #     )

    #     assert global_state["auctions_created"] == 1
    #     assert global_state["live_auctions"] == 1

    #     local_state = decode_state(
    #         algod_client.account_application_info(self.seller_address, self.app_id)[
    #             "app-local-state"
    #         ]["key-value"]
    #     )

    #     assert local_state["auctions_created"] == 1
    #     assert local_state["live_auctions"] == 1
    #     assert local_state["auctions_won"] == 0

    #     box = algod_client.application_box_by_name(
    #         self.app_id,
    #         box_name_bytes,
    #     )

    #     box_name = b64decode(box["name"])

    #     assert encode_address(box_name[:32]) + str(
    #         int.from_bytes(box_name[32:], "big")
    #     ) == self.seller_address + str(asset_id)

    #     box_value = b64decode(box["value"])

    #     box_end_timestamp = int.from_bytes(box_value[:8], "big")
    #     box_buyout_price = int.from_bytes(box_value[8:16], "big")
    #     box_current_price = int.from_bytes(box_value[16:24], "big")
    #     box_current_bidder = box_value[24:]

    #     assert box_end_timestamp == END_TIMESTAMP
    #     assert box_buyout_price == BUYOUT_PRICE
    #     assert box_current_price == BASE_PRICE
    #     assert box_current_bidder == bytes(32)

    # def test_place_bid(self) -> None:
    #     sp = algod_client.suggested_params()
    #     sp.flat_fee = True

    #     asset_id = self._create_nft(self.seller_txn_signer)

    #     box_name_bytes = self._create_auction(self.seller_txn_signer, asset_id)

    #     bid_price = BASE_PRICE * 2

    #     self._place_bid(
    #         self.bidder_txn_signer_1,
    #         asset_id,
    #         bid_price,
    #     )

    #     asset_holding = algod_client.account_asset_info(
    #         self.bidder_address_1, asset_id
    #     )["asset-holding"]

    #     assert asset_holding["amount"] == 0

    #     box = algod_client.application_box_by_name(
    #         self.app_id,
    #         box_name_bytes,
    #     )

    #     box_value = b64decode(box["value"])

    #     box_end_timestamp = int.from_bytes(box_value[:8], "big")
    #     box_buyout_price = int.from_bytes(box_value[8:16], "big")
    #     box_current_price = int.from_bytes(box_value[16:24], "big")
    #     box_current_bidder = encode_address(box_value[24:])

    #     assert box_end_timestamp == END_TIMESTAMP
    #     assert box_buyout_price == BUYOUT_PRICE
    #     assert box_current_price == bid_price
    #     assert box_current_bidder == self.bidder_address_1

    #     self._forward_time(2)

    #     # settle

    # def test_place_bid_buyout(self) -> None:
    #     sp = algod_client.suggested_params()
    #     sp.flat_fee = True

    #     asset_id = self._create_nft(self.seller_txn_signer)

    #     box_name_bytes = self._create_auction(self.seller_txn_signer, asset_id)

    #     seller_balance_before: int = algod_client.account_info(self.seller_address)[
    #         "amount"
    #     ]

    #     bid_price = BUYOUT_PRICE

    #     self._place_bid(
    #         self.bidder_txn_signer_1,
    #         asset_id,
    #         bid_price,
    #         [asset_id],
    #         [self.seller_address],
    #     )

    #     asset_holding = algod_client.account_asset_info(
    #         self.bidder_address_1, asset_id
    #     )["asset-holding"]

    #     assert asset_holding["amount"] == 1

    #     seller_balance_after: int = algod_client.account_info(self.seller_address)[
    #         "amount"
    #     ]

    #     assert seller_balance_after - seller_balance_before == bid_price

    #     global_state = decode_state(
    #         algod_client.application_info(self.app_id)["params"]["global-state"]
    #     )

    #     assert global_state["auctions_created"] == 1
    #     assert global_state["live_auctions"] == 0

    #     local_state = decode_state(
    #         algod_client.account_application_info(self.seller_address, self.app_id)[
    #             "app-local-state"
    #         ]["key-value"]
    #     )

    #     assert local_state["auctions_created"] == 1
    #     assert local_state["live_auctions"] == 0
    #     assert local_state["auctions_won"] == 0

    #     local_state = decode_state(
    #         algod_client.account_application_info(self.bidder_address_1, self.app_id)[
    #             "app-local-state"
    #         ]["key-value"]
    #     )

    #     assert local_state["auctions_created"] == 0
    #     assert local_state["live_auctions"] == 0
    #     assert local_state["auctions_won"] == 1

    #     try:
    #         algod_client.application_box_by_name(
    #             self.app_id,
    #             box_name_bytes,
    #         )
    #     except AlgodHTTPError as e:
    #         assert e.code == 404

    # def test_place_bid_two_bidders(self) -> None:
    #     sp = algod_client.suggested_params()
    #     sp.flat_fee = True

    #     asset_id = self._create_nft(self.seller_txn_signer)

    #     box_name_bytes = self._create_auction(self.seller_txn_signer, asset_id)

    #     bid_price_1 = BASE_PRICE * 2

    #     self._place_bid(
    #         self.bidder_txn_signer_1,
    #         asset_id,
    #         bid_price_1,
    #     )

    #     bid_price_2 = BASE_PRICE * 3

    #     self._place_bid(
    #         self.bidder_txn_signer_2,
    #         asset_id,
    #         bid_price_2,
    #         accounts=[self.bidder_address_1],
    #     )

    #     # TODO: assert that seller got paid

    #     asset_holding = algod_client.account_asset_info(
    #         self.bidder_address_2, asset_id
    #     )["asset-holding"]

    #     assert asset_holding["amount"] == 0

    #     box = algod_client.application_box_by_name(
    #         self.app_id,
    #         box_name_bytes,
    #     )

    #     box_value = b64decode(box["value"])

    #     box_end_timestamp = int.from_bytes(box_value[:8], "big")
    #     box_buyout_price = int.from_bytes(box_value[8:16], "big")
    #     box_current_price = int.from_bytes(box_value[16:24], "big")
    #     box_current_bidder = encode_address(box_value[24:])

    #     assert box_end_timestamp == END_TIMESTAMP
    #     assert box_buyout_price == BUYOUT_PRICE
    #     assert box_current_price == bid_price_2
    #     assert box_current_bidder == self.bidder_address_2

    # def test_place_bid_buyout_two_bidders(self) -> None:
    #     sp = algod_client.suggested_params()
    #     sp.flat_fee = True

    #     asset_id = self._create_nft(self.seller_txn_signer)

    #     box_name_bytes = self._create_auction(self.seller_txn_signer, asset_id)

    #     seller_balance_before: int = algod_client.account_info(self.seller_address)[
    #         "amount"
    #     ]

    #     bid_price_1 = BASE_PRICE * 2

    #     self._place_bid(
    #         self.bidder_txn_signer_1,
    #         asset_id,
    #         bid_price_1,
    #     )

    #     seller_balance_after: int = algod_client.account_info(self.seller_address)[
    #         "amount"
    #     ]

    #     assert seller_balance_after - seller_balance_before == 0

    #     bid_price_2 = BUYOUT_PRICE

    #     self._place_bid(
    #         self.bidder_txn_signer_2,
    #         asset_id,
    #         bid_price_2,
    #         [asset_id],
    #         [self.bidder_address_1, self.seller_address],
    #     )

    #     asset_holding = algod_client.account_asset_info(
    #         self.bidder_address_2, asset_id
    #     )["asset-holding"]

    #     assert asset_holding["amount"] == 1

    #     seller_balance_after: int = algod_client.account_info(self.seller_address)[
    #         "amount"
    #     ]

    #     assert seller_balance_after - seller_balance_before == bid_price_2

    #     try:
    #         algod_client.application_box_by_name(
    #             self.app_id,
    #             box_name_bytes,
    #         )
    #     except AlgodHTTPError as e:
    #         assert e.code == 404

    # def _create_nft(
    #     self,
    #     signer: AccountTransactionSigner,
    #     unit_name: str = UNIT_NAME,
    #     asset_name: str = ASSET_NAME,
    # ) -> int:
    #     address = address_from_private_key(signer.private_key)

    #     atc = AtomicTransactionComposer()
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=AssetCreateTxn(
    #                 sender=address,
    #                 sp=algod_client.suggested_params(),
    #                 total=1,
    #                 decimals=0,
    #                 default_frozen=False,
    #                 unit_name=unit_name,
    #                 asset_name=asset_name,
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     tx_id = atc.execute(algod_client, 5).tx_ids[0]
    #     asset_id: int = algod_client.pending_transaction_info(tx_id)["asset-index"]

    #     return asset_id

    # def _create_auction(
    #     self,
    #     signer: AccountTransactionSigner,
    #     asset_id: int,
    #     end_timestamp: int = END_TIMESTAMP,
    #     base_price: int = BASE_PRICE,
    #     buyout_price: int = BUYOUT_PRICE,
    # ) -> bytes:
    #     sp = algod_client.suggested_params()
    #     sp.flat_fee = True

    #     sender = address_from_private_key(signer.private_key)

    #     atc = AtomicTransactionComposer()
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=ApplicationOptInTxn(sender=sender, sp=sp, index=self.app_id),
    #             signer=signer,
    #         )
    #     )
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=PaymentTxn(
    #                 sender=sender,
    #                 sp=sp,
    #                 receiver=self.app_address,
    #                 amt=140900,  # box MBR + opt-in
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=ApplicationNoOpTxn(
    #                 sender=sender,
    #                 sp=sp,
    #                 index=self.app_id,
    #                 app_args=["opt_in_asset", 0],  # 0 is the index of asset_id
    #                 foreign_assets=[asset_id],
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=AssetTransferTxn(
    #                 sender=sender,
    #                 sp=sp,
    #                 receiver=self.app_address,
    #                 amt=1,
    #                 index=asset_id,
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     sp.fee = sp.min_fee * 6
    #     box_name_bytes = decode_address(sender) + asset_id.to_bytes(8, "big")
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=ApplicationNoOpTxn(
    #                 sender=sender,
    #                 sp=sp,
    #                 index=self.app_id,
    #                 app_args=[
    #                     "create_auction",
    #                     end_timestamp,
    #                     base_price,
    #                     buyout_price,
    #                 ],
    #                 boxes=[
    #                     (
    #                         0,
    #                         box_name_bytes,
    #                     )
    #                 ],
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     atc.execute(algod_client, 5)

    #     return box_name_bytes

    # def _place_bid(
    #     self,
    #     signer: AccountTransactionSigner,
    #     asset_id: int,
    #     bid_price: int,
    #     assets: list = None,
    #     accounts: list = None,
    #     asset_opt_in: bool = True,
    #     app_opt_in: bool = True,
    # ) -> None:
    #     sp = algod_client.suggested_params()
    #     sp.flat_fee = True
    #     sp.fee = 10_000

    #     address = address_from_private_key(signer.private_key)
    #     box_name_bytes = decode_address(address) + asset_id.to_bytes(8, "big")

    #     atc = AtomicTransactionComposer()
    #     if asset_opt_in:
    #         atc.add_transaction(
    #             TransactionWithSigner(
    #                 txn=AssetOptInTxn(
    #                     sender=address,
    #                     sp=sp,
    #                     index=asset_id,
    #                 ),
    #                 signer=signer,
    #             )
    #         )
    #     if app_opt_in:
    #         atc.add_transaction(
    #             TransactionWithSigner(
    #                 txn=ApplicationOptInTxn(sender=address, sp=sp, index=self.app_id),
    #                 signer=signer,
    #             )
    #         )
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=PaymentTxn(
    #                 sender=address,
    #                 sp=sp,
    #                 receiver=self.app_address,
    #                 amt=bid_price,
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=ApplicationNoOpTxn(
    #                 sender=address,
    #                 sp=sp,
    #                 index=self.app_id,
    #                 app_args=["place_bid", box_name_bytes],
    #                 boxes=[(0, box_name_bytes)],
    #                 foreign_assets=assets,
    #                 accounts=accounts,
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     atc.execute(algod_client, 5)

    # def _settle(self, signer: AccountTransactionSigner, box_name_bytes: bytes) -> None:
    #     address = address_from_private_key(signer.private_key)

    #     atc = AtomicTransactionComposer()
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=ApplicationNoOpTxn(
    #                 sender=address,
    #                 sp=algod_client.suggested_params(),
    #                 index=self.app_id,
    #                 app_args=["settle"],
    #                 boxes=[
    #                     (
    #                         0,
    #                         box_name_bytes,
    #                     )
    #                 ],
    #             ),
    #             signer=signer,
    #         )
    #     )
    #     tx_id = atc.execute(algod_client, 5).tx_ids[0]

    # def _get_balance(self, address: str) -> int:
    #     resp = algod_client.account_info(address)
    #     ...

    # def _forward_time(self, seconds: int) -> None:
    #     sleep(seconds)
    #     address = address_from_private_key(self.manager_txn_signer.private_key)
    #     sp = algod_client.suggested_params()

    #     atc = AtomicTransactionComposer
    #     atc.add_transaction(
    #         TransactionWithSigner(
    #             txn=PaymentTxn(sender=address, sp=sp, receiver=address, amt=0),
    #             signer=self.manager_txn_signer,
    #         )
    #     )
    #     atc.execute(algod_client, 5)
