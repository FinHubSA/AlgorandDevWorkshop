from base64 import b64decode
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import (
    ApplicationCallTxn,
    OnComplete,
    StateSchema,
)
from util.app import deploy_app

from util.client import algod_client
from util.account import AccountManager


class TestHelloWorld:
    def setup_method(self):
        """Create account(s) and app before each test."""

        (
            self.manager_address,
            self.manager_txn_signer,
        ) = AccountManager().create_new_funded_account()

        self.app_id, self.app_address = deploy_app(
            self.manager_txn_signer,
            "1_hello_world.teal",
            "clear.teal",
            algod_client.suggested_params(),
            StateSchema(num_uints=0, num_byte_slices=0),
            StateSchema(num_uints=0, num_byte_slices=0),
        )

    def test_greeting(self):
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                txn=ApplicationCallTxn(
                    sender=self.manager_address,
                    sp=algod_client.suggested_params(),
                    index=self.app_id,
                    on_complete=OnComplete.NoOpOC.real,
                    app_args=["greeting"],
                ),
                signer=self.manager_txn_signer,
            )
        )
        tx_id = atc.execute(algod_client, 5).tx_ids[0]
        logs: list[bytes] = algod_client.pending_transaction_info(tx_id)["logs"]

        assert len(logs) == 1
        assert b64decode(logs.pop()).decode("utf-8") == "Hello, world!"

# a function that does xyz