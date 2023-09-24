import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of
import reactivex
from reactivex import timer, throw
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


# def test_timer_with_interval():
#     scheduler = TestScheduler()
#     source = reactivex.timer(10, 200, scheduler=scheduler)
#     result = scheduler.start(lambda: source)
#     assert result.messages == [
#         on_next(210, 0),
#         on_next(410, 1),
#         on_next(610, 2),
#         on_next(810, 3),
#     ]


def test_timer_with_interval_multiple():
    scheduler = TestScheduler()
    source = reactivex.timer(10, 200, scheduler=scheduler)
    observer_1 = scheduler.create_observer()
    observer_2 = scheduler.create_observer()
    s1 = source.subscribe(observer_1)
    scheduler.advance_by(20)
    s2 = source.subscribe(observer_2)
    scheduler.schedule_absolute(1000, lambda *_: s2.dispose() or s1.dispose())
    scheduler.start()
    assert observer_1.messages == [
        on_next(210, 0),
        on_next(410, 1),
        on_next(610, 2),
        on_next(810, 3),
    ]


def test_timer_just_prints():
    source = reactivex.timer(30, 1)
    s = source.subscribe(lambda x: print(x, time.time()))
    print("moving on", time.time())
    time.sleep(35)
    print("after sleep", time.time())
    s.dispose()
    print("after dispose")
    s = source.subscribe(lambda x: print(x, time.time()))
    time.sleep(35)
    s.dispose()


def test_interval_repeat():
    scheduler = TestScheduler()
    source = reactivex.interval(250, scheduler=scheduler)
    result = scheduler.start(
        lambda: source.pipe(
            operators.take(2),
            operators.repeat(),
        )
    )
    assert result.messages == [
        on_next(450, 0),
        on_next(700, 1),
        on_next(950, 0),
    ]


def test_timer_with_interval_repeat():
    scheduler = TestScheduler()
    source = reactivex.timer(10, 200, scheduler=scheduler)
    result = scheduler.start(
        lambda: source.pipe(
            operators.take(2),
            operators.repeat(),
        )
    )
    assert result.messages == [
        on_next(210, 0),
        on_next(410, 1),
        on_next(420, 0),
        on_next(620, 1),
        on_next(630, 0),
        on_next(830, 1),
        on_next(840, 0),
    ]


def test_timer_with_interval_repeat_and_delay():
    scheduler = TestScheduler()
    source = reactivex.timer(10, 200, scheduler=scheduler)
    result = scheduler.start(
        lambda: source.pipe(
            operators.take(2),
            operators.delay_subscription(30, scheduler=scheduler),
            operators.repeat(),
        )
    )
    assert result.messages == [
        on_next(210, 0),
        on_next(410, 1),
        on_next(450, 0),
        on_next(650, 1),
        on_next(690, 0),
        on_next(890, 1),
        on_next(930, 0),
    ]


# def test_timer_no_interval_repeat():
#     scheduler = TestScheduler()
#     source = reactivex.timer(230, scheduler=scheduler)
#     result = scheduler.start(lambda: source.pipe(operators.repeat()))
#     assert result.messages == [
#         on_next(430, 0),
#         on_next(660, 0),
#         on_next(890, 0),
#     ]
