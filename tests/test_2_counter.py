from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.error import AlgodHTTPError
from algosdk.transaction import (
    ApplicationCallTxn,
    OnComplete,
    StateSchema,
)
from util.app import deploy_app

from util.client import algod_client, indexer_client
from util.account import create_new_funded_account
from util.state_decode import decode_state


class TestCounter:
    def setup_method(self):
        """Create account and app before each test."""

        self.algod = algod_client()
        self.indexer = indexer_client()

        self.manager_address, self.manager_txn_signer = create_new_funded_account()
        self.user_address, self.user_txn_signer = create_new_funded_account()

        self.app_id, self.app_address = deploy_app(
            self.manager_txn_signer,
            "contracts/build/2_counter.teal",
            "contracts/build/clear.teal",
            self.algod.suggested_params(),
            StateSchema(1, 0),
            StateSchema(0, 0),
        )

    def test_increment_counter_as_manager(self):
        global_state = self._increment_counter(
            self.manager_address, self.manager_txn_signer
        )
        assert global_state["counter"] == 1

        global_state = self._increment_counter(
            self.manager_address, self.manager_txn_signer
        )
        assert global_state["counter"] == 2

        global_state = self._increment_counter(
            self.manager_address, self.manager_txn_signer
        )
        assert global_state["counter"] == 3

        global_state = self._increment_counter(
            self.manager_address, self.manager_txn_signer
        )
        assert global_state["counter"] == 3

    def test_increment_counter_as_non_manager(self):
        try:
            self._increment_counter(self.user_address, self.user_txn_signer)
        except AlgodHTTPError as e:
            assert "assert failed" in e.args[0]

    def _increment_counter(self, address: str, txn_signer: AccountTransactionSigner):
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                ApplicationCallTxn(
                    sender=address,
                    sp=self.algod.suggested_params(),
                    index=self.app_id,
                    on_complete=OnComplete.NoOpOC.real,
                    app_args=["increment_counter"],
                ),
                txn_signer,
            )
        )
        atc.execute(self.algod, 5).tx_ids[0]

        global_state = decode_state(
            self.algod.application_info(self.app_id)["params"]["global-state"]
        )

        return global_state
