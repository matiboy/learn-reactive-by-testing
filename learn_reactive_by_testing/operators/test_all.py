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



def test_all_yes():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        *[on_next(110+i*100, i) for i in range(10)],
        on_completed(800)
    )
    
    observer = scheduler.start(lambda: xs.pipe(operators.all(lambda x: x < 10e3)))
    assert observer.messages == [
        on_next(800, True),
        on_completed(800)
    ]

def test_all_no():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        *[on_next(110+i*100, i) for i in range(7)],
        on_completed(800)
    )
    def is_less_than(x):
        return x < 5
    observer = scheduler.start(lambda: xs.pipe(operators.all(is_less_than)))
    assert observer.messages == [
        on_next(610, False),  # Note: as soon as one item doesn't pass the test, completes
        on_completed(610)
    ]

def test_all_never_ends():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        *[on_next(110+i*100, i) for i in range(5)],
    )
    
    observer = scheduler.start(lambda: xs.pipe(operators.all(lambda x: x < 10e3)))
    assert observer.messages == []
