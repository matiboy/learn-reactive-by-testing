import logging
import math
import sys
import threading
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import Observable, operators
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


def test_issue_713():
    import time

    import reactivex
    from reactivex import operators as ops
    from reactivex.scheduler import ThreadPoolScheduler

    start = time.time()

    pool_scheduler = ThreadPoolScheduler(5)
    messages = []

    def log(message):
        with threading.Lock():
            messages.append(f"{round(time.time() - start , 1)}: {message}")

    def intense_calculation(value):
        time.sleep(2)
        return f"Computed for {value}"
    
    # Create an Observable
    source = reactivex.from_(["Alpha", "Beta", "Gamma"])
    
    source.pipe(
        ops.flat_map(lambda s: reactivex.from_future(pool_scheduler.executor.submit(intense_calculation, s))),
    ).subscribe(
        on_next=lambda s: log(
            f"Processed {s} on {threading.current_thread().name}"
        ),
        on_error=lambda e: log(f"ERROR {e}"),
        on_completed=lambda: log("Process complete!"),
    )

    
    time.sleep(3)
    log("End")

