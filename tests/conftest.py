from pytest import Session

from util.sandbox import sandbox_reset


def pytest_sessionstart(session: Session) -> None:
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    print("Resetting sandbox...")
    sandbox_reset()
    print("Sandbox successfully reset")


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    ...
