from base64 import b64decode
from time import sleep
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.logic import get_application_address
from algosdk.transaction import (
    ApplicationCreateTxn,
    ApplicationDeleteTxn,
    ApplicationCallTxn,
    ApplicationUpdateTxn,
    OnComplete,
    StateSchema,
    SuggestedParams,
    wait_for_confirmation,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from util.client import algod_client, compile_program, indexer_client


def deploy_app(
    txn_signer: AccountTransactionSigner,
    approval_path: str,
    clear_path: str,
    sp: SuggestedParams,
    global_schema: StateSchema,
    local_schema: StateSchema,
) -> tuple[int, str]:
    with open(approval_path, "r") as approval:
        with open(clear_path, "r") as clear:
            address = address_from_private_key(txn_signer.private_key)

            atc = AtomicTransactionComposer()
            atc.add_transaction(
                TransactionWithSigner(
                    ApplicationCreateTxn(
                        sender=address,
                        sp=sp,
                        on_complete=OnComplete.NoOpOC.real,
                        approval_program=compile_program(approval.read()),
                        clear_program=compile_program(clear.read()),
                        global_schema=global_schema,
                        local_schema=local_schema,
                    ),
                    txn_signer,
                )
            )
            tx_id = atc.execute(algod_client(), 5).tx_ids[0]
            app_id = algod_client().pending_transaction_info(tx_id)["application-index"]
            app_address = get_application_address(app_id)

            return app_id, app_address


def call_app(
    client: AlgodClient,
    private_key: str,
    app_id: int,
    on_complete: OnComplete,
    app_args: list = None,
    accounts: list = None,
    foreign_assets: list = None,
):
    # declare sender
    sender = address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = ApplicationCallTxn(
        sender=sender,
        sp=params,
        on_complete=on_complete,
        index=app_id,
        app_args=app_args,
        accounts=accounts,
        foreign_assets=foreign_assets,
    )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transaction(signed_txn)

    # await confirmation
    wait_for_confirmation(client, tx_id, 5)

    return get_application_logs(indexer_client(), app_id, tx_id)


def update_app(
    client: AlgodClient,
    private_key: str,
    approval_program: bytes,
    clear_program: bytes,
    app_id: int,
):
    # define sender as creator
    sender = address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = ApplicationUpdateTxn(
        sender,
        params,
        app_id,
        approval_program,
        clear_program,
    )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transaction(signed_txn)

    # await confirmation
    wait_for_confirmation(client, tx_id, 5)

    print("Updated app with app_id: ", app_id)


def delete_app(
    client: AlgodClient,
    private_key: str,
    app_id: int,
):
    # define sender as creator
    sender = address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = ApplicationDeleteTxn(
        sender,
        params,
        app_id,
    )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transaction(signed_txn)

    # await confirmation
    wait_for_confirmation(client, tx_id, 5)

    print("Deleted app with app_id: ", app_id)


def get_application_logs(indexer: IndexerClient, app_id: int, tx_id: str):
    # sleep because indexer takes a while to catch up
    sleep(1)

    log_return = indexer.application_logs(application_id=app_id, txid=tx_id)
    log: str

    if log_return.get("log-data"):
        for log in log_return["log-data"][0]["logs"]:
            print("----------")
            decoded_log = b64decode(log)
            if decoded_log.startswith(b"151f7c75"):
                decoded_log = decoded_log.split(b"151f7c75", 1)[1]
                try:
                    val = int.from_bytes(decoded_log, byteorder="big")
                except:
                    val = decoded_log.decode("utf-8")
                return val
