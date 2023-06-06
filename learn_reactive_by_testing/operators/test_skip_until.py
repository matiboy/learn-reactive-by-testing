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



def test_skip_until_value():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        *[on_next(110+i*100, i) for i in range(10)],
        on_completed(800)
    )
    until = scheduler.create_hot_observable(
        on_next(450, 'a'),
        on_next(550, 'a'),
        on_completed(650),
    )
    
    observer = scheduler.start(lambda: xs.pipe(operators.skip_until(
        until
    )))
    assert observer.messages == [
        on_next(510, 4),
        on_next(610, 5),
        on_next(710, 6),
        on_completed(800)
    ]
    assert xs.subscriptions == [
        subscribe(200,800)
    ]
    # Unsubscribes from the decision making observable immediately
    assert until.subscriptions == [
        subscribe(200, 450)
    ]
