import functools
import threading
import time
from typing import Optional
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import Observable, operators
import reactivex
from reactivex import timer, throw
from reactivex.disposable import CompositeDisposable, Disposable, SerialDisposable
from reactivex.scheduler import CurrentThreadScheduler, TimeoutScheduler, ThreadPoolScheduler
from typing import Optional
from reactivex import abc

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
    

def timer(first: float, period: float, scheduler: Optional[abc.SchedulerBase] = None) -> Observable[int]:
    """Generates an observable sequence that produces a value after due time and then after each period.

    Args:
        first: Relative time in seconds for the first value to be produced.
        period: Relative time in seconds for the subsequent values to be produced.
        scheduler: [Optional] Scheduler to run the timer on.

    Returns:
        An observable sequence that produces a value after due time and then each period.
    """
    timer_scheduler = scheduler or TimeoutScheduler.singleton()
    def subscribe(observer: abc.ObserverBase[int], scheduler_: Optional[abc.SchedulerBase] = None) -> abc.DisposableBase:
        _scheduler = scheduler_ or CurrentThreadScheduler.singleton()
        is_disposed = False
        lock = threading.Lock()
        count = 0
        start = timer_scheduler.now

        def get_is_disposed() -> bool:
            with lock:
                return is_disposed
        
        def set_is_disposed():
            nonlocal is_disposed
            with lock:
                is_disposed = True

        def on_next(_s, state) -> None:
            nonlocal timer_scheduler
            observer.on_next(state)

        def action(scheduler: abc.SchedulerBase, state: int) -> None:
            nonlocal count
            disposed = get_is_disposed()
            if disposed:
                return
            _scheduler.schedule(on_next, count)
            count += 1
            if period:
                timer_scheduler.schedule_absolute(start + timer_scheduler.to_timedelta(first + count * period), action)

        timer_scheduler.schedule_relative(first, action)
        return Disposable(set_is_disposed)

    return Observable(subscribe)

def test_timer_multiple_subs():
    scheduler = TestScheduler()
    observer = scheduler.create_observer()
    observer2 = scheduler.create_observer()
    xs = timer(10, 200, scheduler=scheduler)
    sub = CompositeDisposable()
    sub.add(xs.subscribe(observer, scheduler=scheduler))
    scheduler.schedule_absolute(250, lambda *_: sub.add(xs.subscribe(observer2)))
    scheduler.schedule_absolute(800, lambda *_: sub.dispose())
    

    scheduler.start()

    assert observer.messages == [
        on_next(10, 0),
        on_next(210, 1),
        on_next(410, 2),
        on_next(610, 3),
    ]
    assert observer2.messages == [
        on_next(260, 0),
        on_next(460, 1),
        on_next(660, 2),
    ]

def test_timer_multiple_subs_no_virtualtime():
    scheduler = ThreadPoolScheduler(5)
    xs = reactivex.timer(0.1, 0.3) # Leave it to a default TimeoutScheduler or not, won't matter 
    # xs = timer(0.1, 0.3, scheduler=scheduler)
    messages = []
    sub = CompositeDisposable()
    def record(k, x):
        nonlocal messages
        messages.append((scheduler.now, k, x, threading.current_thread().name))
    sub.add(xs.subscribe(functools.partial(record, "FIRST"), scheduler=scheduler))
    time.sleep(0.25)
    sub.add(xs.subscribe(functools.partial(record, "SECOND"), scheduler=scheduler))
    time.sleep(2)
    # would need to check time and thread which are not always the same, but it works fine
    assert messages == []
