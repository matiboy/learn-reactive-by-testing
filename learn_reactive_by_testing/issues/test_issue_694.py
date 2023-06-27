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


def _test_issue_694_no_map():
    import time
    from datetime import datetime, timedelta

    import reactivex as rx
    from reactivex import operators as ops, Observable
    from reactivex.scheduler import (
        ThreadPoolScheduler,
        CurrentThreadScheduler,
        NewThreadScheduler,
    )
    from reactivex.subject import Subject

    su: Observable[int] = Subject()
    su = Subject()

    c = 10
    d = 0
    thread = ThreadPoolScheduler(max_workers=c)
    scheduler = CurrentThreadScheduler()
    scheduler = NewThreadScheduler()
    lock = threading.Lock()

    def inc(x):
        nonlocal d
        with lock:
            d += x

    def print_len(x):
        print("Length of window:", x)

    items = []

    def print_item(x):
        print("APPENDING ITEM", x, items)
        items.append(x)

    def to_len(x):
        print("Got new window", x)
        return x.pipe(
            ops.do_action(print_item),
            # ops.count(),
            ops.do_action(print_len),
        )

    def wait_a_while(x):
        print("WAIT A WHILE", threading.current_thread().name)
        time.sleep(1)
        print("AFTER WAIT A WHILE", threading.current_thread().name)
        # time.sleep(0)

    su.pipe(
        ops.window_with_time_or_count(count=c, timespan=timedelta(milliseconds=10)),
        ops.flat_map(to_len),
        ops.do_action(inc),
        # start section
        ops.map(wait_a_while),
        # end section
    ).subscribe()

    for i in range(2 * c):
        start = time.time()
        print(f"Start {i}")

        time.sleep(1 / 1_000)
        su.on_next(i)
        print(f"End {i}: {time.time() - start}")
    print("D", d)
    print("Items", items)

    time.sleep(2)


def _test_issue_694_original():
    import time
    from datetime import datetime, timedelta

    import reactivex as rx
    from reactivex import operators as ops, Observable
    from reactivex.scheduler import (
        ThreadPoolScheduler,
        NewThreadScheduler,
        CurrentThreadScheduler,
        EventLoopScheduler,
        TrampolineScheduler,
    )
    from reactivex.subject import Subject

    su: Observable[int] = Subject()
    su = Subject()

    thread = ThreadPoolScheduler(max_workers=10)

    def spend_cpu_time(x=None):
        time.sleep(1)

    windows = su.pipe(
        ops.window_with_time_or_count(
            count=1_000,
            timespan=timedelta(milliseconds=1_000),
        ),
    )
    counter = 0
    last_inc = -1

    def inc(_=0):
        nonlocal counter, last_inc
        last_inc += 1
        print("INC", _, threading.current_thread().name)
        counter += 1

    windows.pipe(
        ops.flat_map(
            lambda window: window.pipe(
                ops.observe_on(CurrentThreadScheduler()),
                ops.do_action(on_next=inc),
            )
        ),
        # ops.do_action(on_next=lambda x: print("NEXT", threading.current_thread().name)),
        ops.reduce(lambda acc, x: acc + 1, 0),
        # end section
    ).subscribe(
        on_next=lambda x: print("NEXT", threading.current_thread().name, x),
        on_completed=lambda: print(
            "COUNTER: ", counter, threading.current_thread().name
        ),
    )

    for i in range(2000):
        time.sleep(1 / 1000)
        t = datetime.now()
        su.on_next(i)
    su.on_completed()

    print("Counter", counter)

    time.sleep(1)


def test_issue_694_event_loop():
    import time
    from datetime import timedelta
    from reactivex import operators as ops
    from reactivex.subject import Subject

    su = Subject()

    event_loop = EventLoopScheduler()
    v = 0

    def set_checker(x):
        nonlocal v
        v = x

    def wait_a_while(*_):
        time.sleep(10 / 1000)

    su.pipe(
        ops.window_with_time_or_count(
            count=1_000, timespan=timedelta(milliseconds=1_000)
        ),
        ops.flat_map(
            lambda window: window.pipe(
                ops.observe_on(event_loop),
                ops.count(),
            )
        ),
        ops.do_action(wait_a_while),
        ops.scan(lambda acc, x: acc + x, 0),
        # end section
    ).subscribe(on_next=set_checker)

    for i in range(2000):
        time.sleep(1 / 1000)
        su.on_next(i)

    time.sleep(2)
    assert v == 2_000
