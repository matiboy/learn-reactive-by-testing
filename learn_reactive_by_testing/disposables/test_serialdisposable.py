import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, disposable
import reactivex

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe



def test_serial():
    scheduler = TestScheduler()
    xs = scheduler.create_cold_observable(
        *[on_next(10+i*100, i) for i in range(10)],
        on_completed(380)
    )
    sub = disposable.SerialDisposable()
    observer_1 = scheduler.create_observer()
    sub.set_disposable(xs.subscribe(observer_1))
    scheduler.schedule_absolute(250, lambda *_: sub.set_disposable(xs.subscribe(observer_1)))
    
    scheduler.start()
    assert observer_1.messages == [
        on_next(10, 0),
        on_next(110, 1),
        on_next(210, 2),
        on_next(260, 0),
        on_next(360, 1),
        on_next(460, 2),
        on_next(560, 3),
        on_completed(630),
    ]
    assert xs.subscriptions == [
        subscribe(0,250),
        subscribe(250, 630)
    ]
