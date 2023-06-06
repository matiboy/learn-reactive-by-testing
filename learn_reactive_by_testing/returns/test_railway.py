from returns import result
from unittest.mock import MagicMock, call

def test_railway():
    outcome = result.Success('abc')
    success = MagicMock().return_value(5)
    failure = MagicMock().return_value(42)
    outcome.alt(failure).map(success)
    assert failure.call_count == 0
    assert success.call_count == 1
    assert success.call_args == call('abc')