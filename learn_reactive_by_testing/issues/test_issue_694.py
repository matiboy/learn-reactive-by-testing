import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex
import threading

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_issue_694_no_map():
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
