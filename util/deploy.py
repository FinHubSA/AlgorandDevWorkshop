from os import getenv

from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.v2client.algod import AlgodClient
from algosdk.mnemonic import to_private_key
from algosdk.transaction import StateSchema
from dotenv import load_dotenv

from util.app import deploy_app

load_dotenv()

if __name__ == "__main__":
    algod_address = getenv("TESTNET_ALGOD_ADDRESS")
    algod_token = getenv("ALGOD_TOKEN")
    headers = {
        "X-API-Key": algod_token,
    }

    algod_client = AlgodClient(algod_token, algod_address, headers)
    signer = AccountTransactionSigner(to_private_key(getenv("MNEMONIC")))

    print(
        deploy_app(
            signer,
            "5_auction.teal",
            "clear.teal",
            algod_client.suggested_params(),
            StateSchema(num_uints=2, num_byte_slices=0),
            StateSchema(num_uints=3, num_byte_slices=0),
            algod_client,
        )
    )
