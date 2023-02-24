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



def test_merge_behavior():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        on_completed(200)
    )
    ys = scheduler.create_cold_observable(
        on_next(250, 42),
        on_completed(300)
    )

    result = scheduler.start(lambda: reactivex.merge(xs, ys))
    assert result.messages == [
        on_next(450, 42),
        on_completed(500)
    ]

def test_merge_behavior_never_end():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
    )
    ys = scheduler.create_cold_observable(
        on_next(250, 42),
        on_completed(300)
    )

    result = scheduler.start(lambda: reactivex.merge(xs, ys))
    assert result.messages == [
        on_next(450, 42),
    ]