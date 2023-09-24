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


def test_share_multiple_connect_behavior():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        *[on_next(10 + i * 200, i) for i in range(10)],
    )
    ys = xs.pipe(operators.share())

    outcome = scheduler.start(
        lambda: reactivex.merge(
            ys,
            reactivex.timer(50, scheduler=scheduler).pipe(
                operators.flat_map(lambda _: ys.pipe(operators.map(lambda x: x + 100)))
            ),
        ).pipe(operators.take(5), operators.repeat())
    )
    assert outcome.messages == [
        on_next(210, 0),
        on_next(410, 1),
        on_next(410, 101),
        on_next(610, 2),
        on_next(610, 102),
        on_next(620, 0),
        on_next(820, 1),
        on_next(820, 101),
    ]

    assert xs.subscriptions == [
        subscribe(200, 610),
        subscribe(610, 1000),
    ]
