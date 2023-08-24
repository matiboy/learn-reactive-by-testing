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


def test_delay_subscription():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        *[on_next(110 + i * 100, i) for i in range(10)],
    )
    result = scheduler.start(
        lambda: xs.pipe(operators.delay_subscription(150, scheduler=scheduler))
    )
    assert result.messages == [
        on_next(460, 0),
        on_next(560, 1),
        on_next(660, 2),
        on_next(760, 3),
        on_next(860, 4),
        on_next(960, 5),
    ]
    assert xs.subscriptions == [
        subscribe(350, 1000),
    ]
