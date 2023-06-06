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
        on_next(110, 0),
        on_next(210, 1),
        on_next(310, 2),
        on_next(410, 3),
        on_next(510, 4),
        on_next(610, 5),
        on_next(710, 6),
    ]

def test_replay_multiple_connect_behavior():
    scheduler = TestScheduler()
    xs = scheduler.create_hot_observable(
        *[on_next(110+i*100, i) for i in range(10)],
    )
    
    observer = scheduler.create_observer()
    observer2 = scheduler.create_observer()
    o = xs.pipe(operators.replay())
    o.subscribe(observer, scheduler=scheduler)
    sub = o.connect()
    scheduler.schedule_absolute(400, lambda *_: sub.dispose())
    scheduler.schedule_absolute(600, lambda *_: o.connect())
    scheduler.schedule_absolute(700, lambda *_: o.subscribe(observer2, scheduler=scheduler))
    scheduler.start()
    assert observer.messages == [
        on_next(110, 0),
        on_next(210, 1),
        on_next(310, 2),
        on_next(610, 5),
        on_next(710, 6),
        on_next(810, 7),
        on_next(910, 8),
        on_next(1010, 9),
    ]
    # Late subscriber gets all values
    assert observer2.messages == [
        on_next(700.0, 0.0), on_next(700.0, 1.0), on_next(700.0, 2.0), on_next(700.0, 5.0), on_next(710.0, 6.0), on_next(810.0, 7.0), on_next(910.0, 8.0), on_next(1010.0, 9.0)
    ]
