from base64 import b64decode

from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient


def algod_client() -> AlgodClient:
    """Instantiate and return Algod client object."""

    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return AlgodClient(algod_token, algod_address)


def indexer_client() -> IndexerClient:
    """Instantiate and return Indexer client object."""

    indexer_address = "http://localhost:8980"
    indexer_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return IndexerClient(indexer_token, indexer_address)


def compile_program(source_code) -> bytes:
    compile_response = algod_client().compile(source_code)
    return b64decode(compile_response["result"])
