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

from util.client import algod_client
from util.account import AccountManager
from util.state_decode import decode_state


class TestCounter:
    def setup_method(self):
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
            "2_counter.teal",
            "clear.teal",
            algod_client.suggested_params(),
            StateSchema(num_uints=1, num_byte_slices=0),
            StateSchema(num_uints=0, num_byte_slices=0),
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
                txn=ApplicationCallTxn(
                    sender=address,
                    sp=algod_client.suggested_params(),
                    index=self.app_id,
                    on_complete=OnComplete.NoOpOC.real,
                    app_args=["increment_counter"],
                ),
                signer=txn_signer,
            )
        )
        atc.execute(algod_client, 5).tx_ids[0]

        global_state = decode_state(
            algod_client.application_info(self.app_id)["params"]["global-state"]
        )

        return global_state
