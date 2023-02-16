from pytest import Session


def pytest_sessionstart(session: Session) -> None:
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    ...


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    ...
