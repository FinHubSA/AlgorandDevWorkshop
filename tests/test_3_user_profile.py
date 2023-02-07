from base64 import b64decode
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.encoding import decode_address, encode_address
from algosdk.error import AlgodHTTPError
from algosdk.transaction import (
    ApplicationCloseOutTxn,
    ApplicationNoOpTxn,
    ApplicationOptInTxn,
    PaymentTxn,
    StateSchema,
)
from util.app import deploy_app

from util.client import algod_client, indexer_client
from util.account import create_new_funded_account
from util.state_decode import decode_state


class TestUserProfile:
    def setup_method(self) -> None:
        """Create account and app before each test."""

        self.algod = algod_client()
        self.indexer = indexer_client()

        self.manager_address, self.manager_txn_signer = create_new_funded_account()
        self.user_address, self.user_txn_signer = create_new_funded_account()

        self.app_id, self.app_address = deploy_app(
            self.manager_txn_signer,
            "contracts/build/3_user_profile.teal",
            "contracts/build/clear.teal",
            self.algod.suggested_params(),
            StateSchema(1, 0),
            StateSchema(0, 1),
        )

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                PaymentTxn(
                    sender=self.manager_address,
                    sp=self.algod.suggested_params(),
                    receiver=self.app_address,
                    amt=100_000,
                ),
                self.manager_txn_signer,
            )
        )
        atc.execute(self.algod, 5)

    def test_opt_in(self) -> None:
        birthday = b"10/03/1999"
        favourite_colour = b"blue" + bytes(16)
        number_of_pets = 0
        self._opt_in(birthday, favourite_colour, number_of_pets)

        global_state = decode_state(
            self.algod.application_info(self.app_id)["params"]["global-state"]
        )

        assert global_state["users"] == 1

        local_state = decode_state(
            self.algod.account_application_info(self.user_address, self.app_id)[
                "app-local-state"
            ]["key-value"]
        )

        assert local_state["status"] == ""

        box = self.algod.application_box_by_name(
            self.app_id, decode_address(self.user_address)
        )

        assert encode_address(b64decode(box["name"])) == self.user_address

        box_value = b64decode(box["value"])

        assert box_value[:10] == birthday
        assert box_value[10:30] == favourite_colour
        assert int.from_bytes(box_value[30:], byteorder="big") == number_of_pets

    def test_close_out(self) -> None:
        birthday = b"10/03/1999"
        favourite_colour = b"blue" + bytes(16)
        number_of_pets = 0
        self._opt_in(birthday, favourite_colour, number_of_pets)

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                ApplicationCloseOutTxn(
                    sender=self.user_address,
                    sp=self.algod.suggested_params(),
                    index=self.app_id,
                    boxes=[(self.app_id, decode_address(self.user_address))],
                ),
                self.user_txn_signer,
            )
        )
        atc.execute(self.algod, 5)

        global_state = decode_state(
            self.algod.application_info(self.app_id)["params"]["global-state"]
        )

        assert global_state["users"] == 0

        try:
            decode_state(
                self.algod.account_application_info(self.user_address, self.app_id)[
                    "app-local-state"
                ]["key-value"]
            )
        except AlgodHTTPError as e:
            assert "account application info not found" in e.args[0]

        try:
            self.algod.application_box_by_name(
                self.app_id, decode_address(self.user_address)
            )
        except AlgodHTTPError as e:
            assert "box not found" in e.args[0]

    def test_update_user_info(self) -> None:
        birthday = b"10/03/1999"
        favourite_colour = b"blue" + bytes(16)
        number_of_pets = 0
        self._opt_in(birthday, favourite_colour, number_of_pets)

        birthday = b"06/02/2023"
        favourite_colour = b"red" + bytes(17)
        number_of_pets = 1

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                ApplicationNoOpTxn(
                    sender=self.user_address,
                    sp=self.algod.suggested_params(),
                    index=self.app_id,
                    app_args=[
                        "update_user_info",
                        birthday,
                        favourite_colour,
                        number_of_pets,
                    ],
                    boxes=[(self.app_id, decode_address(self.user_address))],
                ),
                self.user_txn_signer,
            )
        )
        atc.execute(self.algod, 5)

        global_state = decode_state(
            self.algod.application_info(self.app_id)["params"]["global-state"]
        )

        assert global_state["users"] == 1

        local_state = decode_state(
            self.algod.account_application_info(self.user_address, self.app_id)[
                "app-local-state"
            ]["key-value"]
        )

        assert local_state["status"] == ""

        box = self.algod.application_box_by_name(
            self.app_id, decode_address(self.user_address)
        )

        assert encode_address(b64decode(box["name"])) == self.user_address

        box_value = b64decode(box["value"])

        assert box_value[:10] == birthday
        assert box_value[10:30] == favourite_colour
        assert int.from_bytes(box_value[30:], byteorder="big") == number_of_pets

    def test_set_status(self) -> None:
        birthday = b"10/03/1999"
        favourite_colour = b"blue" + bytes(16)
        number_of_pets = 0
        self._opt_in(birthday, favourite_colour, number_of_pets)

        status = "Hello, world!"

        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                ApplicationNoOpTxn(
                    sender=self.user_address,
                    sp=self.algod.suggested_params(),
                    index=self.app_id,
                    app_args=[
                        "set_status",
                        status,
                    ],
                    boxes=[(self.app_id, decode_address(self.user_address))],
                ),
                self.user_txn_signer,
            )
        )
        atc.execute(self.algod, 5)

        local_state = decode_state(
            self.algod.account_application_info(self.user_address, self.app_id)[
                "app-local-state"
            ]["key-value"]
        )

        assert local_state["status"] == status

    def _opt_in(
        self, birthday: bytes, favourite_colour: bytes, number_of_pets: int
    ) -> None:
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                PaymentTxn(
                    sender=self.user_address,
                    sp=self.algod.suggested_params(),
                    receiver=self.app_address,
                    amt=30_500,
                ),
                self.user_txn_signer,
            )
        )
        atc.add_transaction(
            TransactionWithSigner(
                ApplicationOptInTxn(
                    sender=self.user_address,
                    sp=self.algod.suggested_params(),
                    index=self.app_id,
                    app_args=[birthday, favourite_colour, number_of_pets],
                    boxes=[(self.app_id, decode_address(self.user_address))],
                ),
                self.user_txn_signer,
            )
        )
        atc.execute(self.algod, 5)
