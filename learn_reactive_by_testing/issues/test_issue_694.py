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


def test_issue_694():
    import time
    from datetime import timedelta
    from reactivex import operators as ops
    from reactivex.subject import Subject

    su = Subject()

    lock = threading.Lock()
    v = 0

    def set_checker(x):
        nonlocal v
        v = x
        lock.release()  # <-- unlock only at the very end of the function executions caused by window's on_completed() call

    def wait_a_while(*_):
        time.sleep(10 / 1000)

    su.pipe(
        ops.window_with_time_or_count(
            count=1_000, timespan=timedelta(milliseconds=1_000)
        ),
        ops.flat_map(
            lambda window: window.pipe(
                ops.do_action(
                    on_completed=lock.acquire
                ),  # <-- lock as soon as window is completed
                ops.count(),
            )
        ),
        ops.do_action(wait_a_while),
        ops.scan(lambda acc, x: acc + x, 0),
        # end section
    ).subscribe(on_next=set_checker)

    for i in range(2000):
        time.sleep(1 / 1000)
        while lock.locked():
            pass  # <-- wait until the lock is released on the other thread
        su.on_next(i)

    time.sleep(2)
    assert v == 2_000


def test_issue_694_fail():
    import time
    from datetime import datetime, timedelta
    import reactivex as rx
    from reactivex import operators as ops
    from reactivex.subject import Subject

    su = Subject()
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
