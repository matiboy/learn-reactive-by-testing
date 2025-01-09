import logging
import time
import sys
import threading
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import Observable, Subject, hot, operators
from reactivex import operators as ops
import reactivex
import reactivex as rx
from reactivex import create
from reactivex import scheduler
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def test_issue_725():
    s = Subject()
    out = []
    def keep(x):
        out.append(x)
    d, i = None, 0
    def sub():
        nonlocal d, i
        if d:
            i += 1
            d.dispose()
        d = s.pipe(
            operators.buffer_with_count(3)
        ).subscribe(
            on_next=lambda x: keep((x, i)),
            on_error=lambda e: logging.info(f"on_error: {e}"),
            on_completed=lambda: logging.info("on_completed")
        )
    sub()
    threading.Timer(0.1, lambda: s.on_next(1)).start()
    threading.Timer(0.2, lambda: s.on_next(2)).start()
    threading.Timer(0.3, lambda: s.on_next(3)).start()
    threading.Timer(0.4, lambda: s.on_next(4)).start()
    threading.Timer(0.5, lambda: s.on_next(5)).start()
    threading.Timer(0.6, lambda: s.on_next(6)).start()
    threading.Timer(0.7, lambda: s.on_next(7)).start()
    threading.Timer(0.45, sub).start()
    time.sleep(1)
    print(out)


def test_issue_725_2():
    s = Subject()
    out = []
    def keep(x):
        out.append(x)
    control_subject = Subject()

    control_subject.pipe(
        operators.flat_map_latest(lambda x: s.pipe(
            operators.buffer_with_count(3),
            operators.map(lambda y: (x, y))
        )),
    ).subscribe(on_next=keep)
    control_subject.on_next(1)
    threading.Timer(0.1, lambda: s.on_next(1)).start()
    threading.Timer(0.2, lambda: s.on_next(2)).start()
    threading.Timer(0.3, lambda: s.on_next(3)).start()
    threading.Timer(0.4, lambda: s.on_next(4)).start()
    threading.Timer(0.5, lambda: s.on_next(5)).start()
    threading.Timer(0.6, lambda: s.on_next(6)).start()
    threading.Timer(0.7, lambda: s.on_next(7)).start()
    threading.Timer(0.45, lambda: control_subject.on_next(2)).start()
    time.sleep(1)
    assert out == [(1, [1, 2, 3]), (2, [5, 6, 7])]



def test_issue_725_3():
    scheduler = TestScheduler()
    source = scheduler.create_hot_observable(
        on_next(30, 1),
        on_next(70, 2),
        on_next(110, 3),
        on_next(150, 4),
        on_next(190, 5),
        on_next(230, 6),
        on_next(270, 7),
        on_next(290, 8),
    )
    control_subject = scheduler.create_hot_observable(
        on_next(10, "a"),
        on_next(170, "b") # <- after "4" has been emitted but we are still buffering
    )
    results = scheduler.start(lambda: control_subject.pipe(
        operators.flat_map_latest(lambda x: source.pipe(
            operators.buffer_with_count(3),
            operators.map(lambda y: (x, y))
        )),
    ), created=1, subscribed=2)

    assert results.messages == [
        on_next(110, ("a", [1, 2, 3])),
        on_next(270, ("b", [5, 6, 7]))
    ]
    


