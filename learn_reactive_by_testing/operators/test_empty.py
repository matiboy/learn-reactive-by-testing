import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex
from reactivex.scheduler import TimeoutScheduler

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe



def test_empty_immediate():
    scheduler = TestScheduler()
    xs = reactivex.empty(scheduler=scheduler)
    observer = scheduler.start(lambda: xs)
    assert observer.messages == [
        on_completed(200)
    ]

def test_empty_with_delay():
    scheduler = TestScheduler()
    xs = reactivex.empty(scheduler=scheduler)
    observer = scheduler.start(lambda: xs.pipe(operators.delay_subscription(100, scheduler=scheduler)))
    assert observer.messages == [
        on_completed(300)
    ]
    

def test_empty_with_delay_subscription():
    scheduler = TestScheduler()
    xs = reactivex.empty(scheduler=scheduler)
    observer = scheduler.start(lambda: xs.pipe(operators.delay(100, scheduler=scheduler)))
    assert observer.messages == [
        on_completed(300)
    ]
