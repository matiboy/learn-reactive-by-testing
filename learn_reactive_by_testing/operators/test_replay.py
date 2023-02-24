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



def test_replay_behavior():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        *[on_next(110+i*100, i) for i in range(10)],
    )
    
    observer = scheduler.create_observer()
    o = xs.pipe(operators.replay())
    o.subscribe(observer, scheduler=scheduler)
    sub = o.connect()
    scheduler.schedule_absolute(800, lambda *_: sub.dispose())
    scheduler.start()
    assert observer.messages == [
        on_next(450, 42),
        on_completed(500)
    ]
