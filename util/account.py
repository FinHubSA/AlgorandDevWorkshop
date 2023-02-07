from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.mnemonic import to_private_key
from algosdk.transaction import PaymentTxn

from util.client import algod_client, indexer_client
from util.sandbox import cli_mnemonic_for_account


def create_new_funded_account() -> tuple[str, AccountTransactionSigner]:
    private, address = generate_account()
    transaction_signer = AccountTransactionSigner(private)
    _fund_account(address)
    return address, transaction_signer


def _fund_account(
    receiver_address: str,
    initial_funds=1_000_000_000,
) -> None:
    """Fund provided `address` with `initial_funds` amount of microAlgos."""

    funding_address = _initial_funds_address()

    atc = AtomicTransactionComposer()
    atc.add_transaction(
        TransactionWithSigner(
            PaymentTxn(
                sender=funding_address,
                sp=algod_client().suggested_params(),
                receiver=receiver_address,
                amt=initial_funds,
            ),
            AccountTransactionSigner(
                to_private_key(cli_mnemonic_for_account(funding_address))
            ),
        )
    )
    atc.execute(algod_client(), 5)


def _initial_funds_address() -> str:
    """Get the address of initially created account having enough funds.
    Such an account is used to transfer initial funds to the accounts
    created in tests.
    """

    return next(
        (
            account.get("address")
            for account in indexer_client().accounts().get("accounts", [{}, {}])
            if account.get("created-at-round") == 0
            and account.get("status") == "Online"
        ),
        None,
    )
