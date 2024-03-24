import functools
import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex
from reactivex.scheduler import EventLoopScheduler
import threading

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_issue_702_fail():
    result = []
    reactivex.range(100_000).pipe(
        operators.buffer_with_time_or_count(timespan=0.001, count=10_000),
    ).subscribe(on_next=lambda x: result.extend(x))

    time.sleep(2)
    assert result == list(range(100_000))


def test_issue_702_event_loop():
    event_loop = EventLoopScheduler()
    result = []
    reactivex.range(100_000).pipe(
        operators.buffer_with_time_or_count(timespan=0.001, count=10_000),
    ).subscribe(on_next=lambda x: result.extend(x), scheduler=event_loop)

    time.sleep(2)
    assert result == list(range(100_000))
