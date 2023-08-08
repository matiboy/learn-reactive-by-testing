from concurrent.futures import wait
from threading import current_thread
import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of
import reactivex
from reactivex.scheduler import ThreadPoolScheduler, EventLoopScheduler
from reactivex import timer, throw
import pytest
import random

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_event_and_threadpool():
    loop = EventLoopScheduler()
    pool = ThreadPoolScheduler(max_workers=10)

    source = reactivex.timer(0.1, 0.1).pipe(operators.take(10))

    source.pipe(
        operators.observe_on(loop),
        operators.do_action(lambda x: print("START BLOCK", time.sleep(0.3))),
        operators.do_action(lambda x: print("END BLOCK")),
    ).subscribe(lambda x: print("BLOCK"))

    def do_in_parallel(x):
        a = pool.executor.submit(
            lambda: print(
                "A", x, current_thread().name, time.sleep(random.randrange(1, 10) / 10)
            )
        )
        b = pool.executor.submit(
            lambda: print(
                "B", x, current_thread().name, time.sleep(random.randrange(1, 10) / 10)
            )
        )
        wait([a, b])
        return x

    source = source.pipe(
        operators.observe_on(loop),
        operators.do_action(
            lambda x: print(
                "LOOP",
                x,
                time.time(),
                current_thread().name,
            )
        ),
        operators.map(do_in_parallel),
    )

    source.subscribe(lambda x: print("SUB", x, current_thread().name), scheduler=loop)
    time.sleep(4)
    assert False
