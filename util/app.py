from base64 import b64decode
from os import path

from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.logic import get_application_address
from algosdk.transaction import (
    ApplicationCreateTxn,
    OnComplete,
    StateSchema,
    SuggestedParams,
)

from util.client import algod_client, AlgodClient

BUILD_PATH_PREFIX = path.join(path.dirname(__file__), "../contracts/build/")


def deploy_app(
    txn_signer: AccountTransactionSigner,
    approval_name: str,
    clear_name: str,
    sp: SuggestedParams,
    global_schema: StateSchema,
    local_schema: StateSchema,
    client: AlgodClient = algod_client,
) -> tuple[int, str]:
    with open(BUILD_PATH_PREFIX + approval_name, "r") as approval:
        with open(BUILD_PATH_PREFIX + clear_name, "r") as clear:
            address = address_from_private_key(txn_signer.private_key)

            atc = AtomicTransactionComposer()
            atc.add_transaction(
                TransactionWithSigner(
                    txn=ApplicationCreateTxn(
                        sender=address,
                        sp=sp,
                        on_complete=OnComplete.NoOpOC.real,
                        approval_program=_compile_program(approval.read()),
                        clear_program=_compile_program(clear.read()),
                        global_schema=global_schema,
                        local_schema=local_schema,
                    ),
                    signer=txn_signer,
                )
            )
            tx_id = atc.execute(client, 5).tx_ids[0]
            app_id = client.pending_transaction_info(tx_id)["application-index"]
            app_address = get_application_address(app_id)

            return app_id, app_address


def _compile_program(source_code: str, client: AlgodClient = algod_client) -> bytes:
    compile_response = client.compile(source_code)
    return b64decode(compile_response["result"])
