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


def test_catch_ignore_errors_but_once_only():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(90, 42), on_error(100, Exception("Yo"))
    )

    result = scheduler.start(
        lambda: xs.pipe(
            operators.catch(
                lambda exc, source: reactivex.concat(reactivex.timer(50), source)
            )
        )
    )
    assert result.messages == [
        on_next(290, 42),
        on_next(350, 0),
        on_next(440, 42),
        on_error(450, Exception("Yo")),
    ]


def test_catch_ignore_errors_forever():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(90, 42), on_error(100, Exception("Yo"))
    )

    def create():
        return xs.pipe(
            operators.catch(
                lambda exc, source: reactivex.concat(
                    reactivex.timer(50).pipe(operators.ignore_elements())
                )
            ),
            operators.repeat(),
        )

    result = scheduler.start(create)
    assert result.messages == [
        on_next(290, 42),
        on_next(440, 42),
        on_next(590, 42),
        on_next(740, 42),
        on_next(890, 42),
    ]
