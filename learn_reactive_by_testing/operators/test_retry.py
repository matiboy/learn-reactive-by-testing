import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_retry_with_count():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(90, 42), on_error(100, Exception("Yo"))
    )

    result = scheduler.start(
        lambda: xs.pipe(
            operators.retry(2)
        )
    )
    assert result.messages == [
        on_next(290, 42),
        on_next(390, 42),
        on_error(400, Exception("Yo")),
    ]

def test_retry_with_count_when_complete():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(90, 42), on_completed(200)
    )

    result = scheduler.start(
        lambda: xs.pipe(
            operators.retry(),
            operators.repeat()
        )
    )
    assert result.messages == [
        on_next(290, 42),
        on_next(490, 42),
        on_next(690, 42),
        on_next(890, 42),
    ]

