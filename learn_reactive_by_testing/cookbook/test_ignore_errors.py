import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of
import reactivex
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_ignore_flat_map_inner_errors():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(50, 42), on_error(100, 'ABC')
    )
    ys = scheduler.create_cold_observable(
        on_next(200, 100),
        on_completed(400)
    )
    sources = [xs, ys, xs]
    def create():
        return reactivex.interval(
            30
        ).pipe(
            operators.take(3),
            operators.flat_map(lambda x: sources[x].pipe(
                operators.catch(lambda *_: reactivex.empty())
            ))
        )

    result = scheduler.start(create)

    assert result.messages == [
        on_next(280, 42),
        on_next(340, 42),
        on_next(460, 100),
        on_completed(660)
    ]

    assert xs.subscriptions == [
        Subscription(230, 330),
        Subscription(290, 390),
    ]

    assert ys.subscriptions == [
        Subscription(260, 660),
    ]