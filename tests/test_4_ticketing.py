from base64 import b64decode

from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import (
    ApplicationNoOpTxn,
    AssetOptInTxn,
    PaymentTxn,
    StateSchema,
)
from util.app import deploy_app
from util.client import algod_client
from util.account import AccountManager
from util.state_decode import decode_state


class TestTicketing:
    def setup_method(self) -> None:
        """Create account(s) and app before each test."""

        account_manager = AccountManager()

        (
            self.manager_address,
            self.manager_txn_signer,
        ) = account_manager.create_new_funded_account()
        (
            self.user_address,
            self.user_txn_signer,
        ) = account_manager.create_new_funded_account()

        self.app_id, self.app_address = deploy_app(
            self.manager_txn_signer,
            "4_ticketing.teal",
            "clear.teal",
            algod_client.suggested_params(),
            StateSchema(num_uints=2, num_byte_slices=0),
            StateSchema(num_uints=0, num_byte_slices=0),
        )

        # Cover MBR of contract.
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=PaymentTxn(
                    sender=self.manager_address,
                    sp=algod_client.suggested_params(),
                    receiver=self.app_address,
                    amt=200_000,
                ),
                signer=self.manager_txn_signer,
            )
        )
        atc.execute(algod_client, 5)

    def test_create_ticket(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        total = 1000
        price = 1_000_000

        asset_id = self._create_ticket(
            self.manager_address,
            self.manager_txn_signer,
            total,
            unit_name,
            asset_name,
            price,
        )
        asset_params = algod_client.asset_info(asset_id)["params"]

        assert asset_params["creator"] == self.app_address
        assert asset_params["decimals"] == 0
        assert asset_params["total"] == total
        assert asset_params["name"] == asset_name
        assert asset_params["unit-name"] == unit_name

        global_state = decode_state(
            algod_client.application_info(self.app_id)["params"]["global-state"]
        )

        assert global_state["ticket_price"] == price

    def test_update_ticket_price(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        total = 1000
        price = 1_000_000

        self._create_ticket(
            self.manager_address,
            self.manager_txn_signer,
            total,
            unit_name,
            asset_name,
            price,
        )

        new_price = 2_000_000

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationNoOpTxn(
                    sender=self.manager_address,
                    sp=algod_client.suggested_params(),
                    index=self.app_id,
                    app_args=["update_ticket_price", new_price],
                ),
                signer=self.manager_txn_signer,
            )
        )
        atc.execute(algod_client, 5)

        global_state = decode_state(
            algod_client.application_info(self.app_id)["params"]["global-state"]
        )

        assert global_state["ticket_price"] == new_price

    def test_buy_ticket(self) -> None:
        unit_name = "TEST"
        asset_name = "My Test Ticket"
        total = 1000
        price = 1_000_000

        asset_id = self._create_ticket(
            self.manager_address,
            self.manager_txn_signer,
            total,
            unit_name,
            asset_name,
            price,
        )

        sp = algod_client.suggested_params()
        sp.flat_fee = True
        amount = 3

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=AssetOptInTxn(
                    sender=self.user_address,
                    sp=sp,
                    index=asset_id,
                ),
                signer=self.user_txn_signer,
            )
        )
        atc.add_transaction(
            TransactionWithSigner(
                txn=PaymentTxn(
                    sender=self.user_address,
                    sp=sp,
                    receiver=self.app_address,
                    amt=price * amount,
                ),
                signer=self.user_txn_signer,
            )
        )

        sp.fee = sp.min_fee * 4

        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationNoOpTxn(
                    sender=self.user_address,
                    sp=sp,
                    index=self.app_id,
                    app_args=["buy_ticket", amount],
                    foreign_assets=[asset_id],
                ),
                signer=self.user_txn_signer,
            )
        )
        atc.execute(algod_client, 5)

        asset_holding = algod_client.account_asset_info(self.user_address, asset_id)[
            "asset-holding"
        ]

        assert asset_holding["amount"] == amount

    def _create_ticket(
        self,
        address: str,
        signer: AccountTransactionSigner,
        total: int,
        unit_name: str,
        asset_name: str,
        price: int,
    ) -> int:
        sp = algod_client.suggested_params()
        sp.flat_fee = True
        sp.fee = sp.min_fee * 2

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationNoOpTxn(
                    sender=address,
                    sp=sp,
                    index=self.app_id,
                    app_args=["create_ticket", total, unit_name, asset_name, price],
                ),
                signer=signer,
            )
        )
        tx_id = atc.execute(algod_client, 5).tx_ids[0]
        logs: list[bytes] = algod_client.pending_transaction_info(tx_id)["logs"]

        return int.from_bytes(b64decode(logs.pop()), "big")
