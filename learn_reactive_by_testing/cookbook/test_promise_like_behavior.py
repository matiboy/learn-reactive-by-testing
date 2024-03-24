import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of
import reactivex
import pytest
import concurrent.futures

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_multiple_time_execution():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(50, 42), on_completed(100)
    )

    result = scheduler.start(lambda: reactivex.concat(xs, xs))

    assert result.messages == [
        on_next(250, 42),
        on_next(350, 42),
        on_completed(400)
    ]

    assert xs.subscriptions == [
        Subscription(200, 300),
        Subscription(300, 400),
    ]


def test_single_time_execution():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_next(50, 42), on_completed(100)
    )
    ys = xs.pipe(
        operators.replay(1)
    ).auto_connect()

    result = scheduler.start(lambda: reactivex.concat(ys, ys))

    assert result.messages == [
        on_next(250, 42),
        on_next(300, 42),
        on_completed(300)
    ]

    assert xs.subscriptions == [
        Subscription(200, 300),
    ]

@pytest.mark.asyncio
async def test_single_time_with_future_and_asyncio_execution():
    counter = 0
    def inc(_):
        nonlocal counter
        counter += 1

    xs = reactivex.just(42).pipe(
        operators.do_action(on_next=inc)
    )
    ys = xs.pipe(
        operators.replay(1)
    ).auto_connect().pipe(
        operators.to_future(),
    )
    await ys
    assert ys.result() == 42
    assert counter == 1

