from os import environ
import pty
from subprocess import CompletedProcess, run


def sandbox_up() -> None:
    _call_sandbox_command("up", "dev")


def sandbox_down() -> None:
    _call_sandbox_command("down")


def sandbox_reset() -> None:
    _call_sandbox_command("reset")


def cli_mnemonic_for_account(address: str) -> str:
    """Return mnemonic for provided address."""

    process = _call_sandbox_command("goal", "account", "export", "-a", address)

    if process.stderr:
        raise RuntimeError(process.stderr.decode("utf8"))

    mnemonic = ""
    parts = process.stdout.decode("utf8").split('"')
    if len(parts) > 1:
        mnemonic = parts[1]
    if mnemonic == "":
        raise ValueError(
            "Can't retrieve mnemonic from the address: %s\nOutput: %s"
            % (address, process.stdout.decode("utf8"))
        )
    return mnemonic


def _call_sandbox_command(*args) -> CompletedProcess:
    """Call and return sandbox command composed from provided arguments."""

    return run(
        [_sandbox_executable(), *args], stdin=pty.openpty()[1], capture_output=True
    )


def _sandbox_executable() -> str:
    """Return full path to Algorand's sandbox executable."""

    return environ.get("ALGORAND_SANDBOX_PATH")
