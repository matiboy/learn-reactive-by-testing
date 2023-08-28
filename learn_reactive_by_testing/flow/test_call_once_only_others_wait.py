import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import Observable, operators, interval, concat, combine_latest, of
import reactivex
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_call_init_once_within_timeframe():
    scheduler = TestScheduler()

    init_count = 0

    def factory(observer, s):
        nonlocal init_count
        init_count += 1
        s.schedule_relative(100, lambda *_: observer.on_next(42))
        s.schedule_relative(100, lambda *_: observer.on_completed())

    xs = (
        Observable(factory)
        .pipe(
            operators.take(1),
            operators.replay(1),
        )
        .auto_connect()
    )

    observer = scheduler.create_observer()
    observer2 = scheduler.create_observer()

    xs.subscribe(observer, scheduler=scheduler)
    scheduler.advance_by(50)
    xs.subscribe(observer2, scheduler=scheduler)

    scheduler.start()

    assert init_count == 1
    assert observer.messages == [
        on_next(100, 42),
        on_completed(100),
    ]
    assert observer2.messages == observer.messages


def test_call_init_once_after_timeframe():
    scheduler = TestScheduler()

    init_count = 0

    def factory(observer, s):
        nonlocal init_count
        init_count += 1
        s.schedule_relative(100, lambda *_: observer.on_next(42))
        s.schedule_relative(100, lambda *_: observer.on_completed())

    xs = (
        Observable(factory)
        .pipe(
            operators.take(1),
            operators.replay(1),
        )
        .auto_connect()
    )

    observer = scheduler.create_observer()
    observer2 = scheduler.create_observer()

    xs.subscribe(observer, scheduler=scheduler)
    scheduler.advance_by(200)
    xs.subscribe(observer2, scheduler=scheduler)

    scheduler.start()

    assert init_count == 1
    assert observer.messages == [
        on_next(100, 42),
        on_completed(100),
    ]
    assert observer2.messages == [
        on_next(200, 42),
        on_completed(200),
    ]


def test_call_init_using_side_effect():
    scheduler = TestScheduler()

    init_count = 0

    def inc(*_):
        nonlocal init_count
        init_count += 1

    xs = (
        reactivex.timer(100, scheduler=scheduler)
        .pipe(operators.do_action(inc), operators.take(1), operators.replay(1))
        .auto_connect()
    )

    observer = scheduler.create_observer()
    observer2 = scheduler.create_observer()

    xs.subscribe(observer, scheduler=scheduler)
    scheduler.advance_by(200)
    xs.subscribe(observer2, scheduler=scheduler)

    scheduler.start()

    assert init_count == 1
    assert observer.messages == [
        on_next(100, 0),
        on_completed(100),
    ]
    assert observer2.messages == [
        on_next(200, 0),
        on_completed(200),
    ]
