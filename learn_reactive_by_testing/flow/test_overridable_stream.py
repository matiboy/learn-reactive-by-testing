import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest
import reactivex
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe

def test_override_stream():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        on_next(250, 1), # should emit this override
        on_next(300, 0), # should start emitting from ys
        on_next(500, 2), # should emit this override
        on_next(510, 0), # should start emitting from ys, and ys will complete before next (without effect)
        on_next(820, 0), # should start emitting from ys again
        on_next(830, 10), # but we interrupt it with this override
        on_completed(900), # and complete
    )
    ys = scheduler.create_cold_observable(
        on_next(100, 42),
        on_next(150, 43),
        on_next(300, 0),
        on_completed(300),
    )

    def create():
        return xs.pipe(operators.flat_map_latest(lambda x: reactivex.just(x) if x != 0 else ys))
    
    observer = scheduler.start(create)

    assert observer.messages == [
        on_next(250, 1),
        on_next(400, 42),
        on_next(450, 43),
        on_next(500, 2),
        on_next(610, 42),
        on_next(660, 43),
        on_next(810, 0),
        on_next(830, 10),
        on_completed(900),
    ]

    assert ys.subscriptions == [
        subscribe(300, 500),
        subscribe(510, 810),
        subscribe(820, 830),
    ]

def test_override_stream_termination():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        on_next(210, 0), # should start emitting from ys
        on_completed(250), # and complete
    )
    ys = scheduler.create_cold_observable(
        on_next(10, 42),
        on_next(150, 43),
        on_next(300, 0),
        on_completed(300),
    )

    def create():
        return xs.pipe(operators.flat_map_latest(lambda x: reactivex.just(x) if x != 0 else ys))
    
    observer = scheduler.start(create)

    # Note that even though xs completes, flat_map continues until both outer and inner streams complete
    # See example below for a solution to that
    assert observer.messages == [
        on_next(220, 42),
        on_next(360, 43),
        on_next(510, 0),
        on_completed(510),
    ]

    assert ys.subscriptions == [
        subscribe(210, 510),
    ]


def test_override_stream_termination_take_until():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        on_next(210, 0), # should start emitting from ys
        on_completed(250), # and complete
    )
    ys = scheduler.create_cold_observable(
        on_next(10, 42),
        on_next(150, 43),
        on_next(300, 0),
        on_completed(300),
    )

    def create():
        return xs.pipe(
            operators.flat_map_latest(lambda x: reactivex.just(x) if x != 0 else ys),
            operators.take_until(
                reactivex.concat(
                    xs.pipe(operators.ignore_elements()), 
                    reactivex.just(1)
                )
            ))
    
    observer = scheduler.start(create)

    assert observer.messages == [
        on_next(220, 42),
        on_completed(250),
    ]

    assert ys.subscriptions == [
        subscribe(210, 250),
    ]
