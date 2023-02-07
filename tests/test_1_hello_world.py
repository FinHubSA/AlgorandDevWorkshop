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

from util.client import algod_client, indexer_client
from util.account import create_new_funded_account

class TestHelloWorld:
    def setup_method(self):
        """Create account and app before each test."""

        self.algod = algod_client()
        self.indexer = indexer_client()

        self.manager_address, self.manager_txn_signer = create_new_funded_account()

        self.app_id, self.app_address = deploy_app(
            self.manager_txn_signer,
            "contracts/build/1_hello_world.teal",
            "contracts/build/clear.teal",
            self.algod.suggested_params(),
            StateSchema(0, 0),
            StateSchema(0, 0),
        )

    def test_greeting(self):
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                ApplicationCallTxn(
                    sender=self.manager_address,
                    sp=self.algod.suggested_params(),
                    index=self.app_id,
                    on_complete=OnComplete.NoOpOC.real,
                    app_args=["greeting"],
                ),
                self.manager_txn_signer,
            )
        )
        tx_id = atc.execute(self.algod, 5).tx_ids[0]
        logs: list[bytes] = self.algod.pending_transaction_info(tx_id)["logs"]

        assert len(logs) == 1
        assert b64decode(logs.pop()).decode("utf-8") == "Hello, world!"
