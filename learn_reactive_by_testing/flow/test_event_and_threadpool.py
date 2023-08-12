from concurrent.futures import wait, ThreadPoolExecutor
from threading import Thread, current_thread
import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import Observable, operators, interval, concat, combine_latest, of
import reactivex
from reactivex.scheduler import ThreadPoolScheduler, EventLoopScheduler
from reactivex import timer, throw, abc
import pytest
import random

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def _test_event_and_threadpool():
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
    assert True


def test_event_and_subscriber_vs_observe_on():
    loop = EventLoopScheduler(
        thread_factory=lambda target: Thread(
            daemon=True, target=target, name="EventLoopScheduler"
        )
    )
    executor = ThreadPoolExecutor(max_workers=10)
    pool = ThreadPoolScheduler(max_workers=10)

    def factory(s, t):
        print(t)
        if t and hasattr(t, "schedule"):
            typed_t: abc.SchedulerBase = t
            typed_t.schedule(lambda *_: s.on_next(10))
            typed_t.schedule_relative(1, lambda *_: s.on_next(20))
        else:
            executor.submit(lambda: s.on_next(1))
            executor.submit(lambda: time.sleep(1) or s.on_next(2))

    source = Observable(factory)
    # source = reactivex.timer(0.1, 0.1).pipe(operators.take(10))

    # scheduler =  is passed to the factory method
    # source.pipe(
    #     operators.do_action(lambda x: print("BEFORE", x, current_thread().name)),
    #     operators.observe_on(loop),
    #     operators.do_action(lambda x: print("AFTER", x, current_thread().name)),
    # ).subscribe(lambda x: print("OUTPUT", x, current_thread().name), scheduler=loop)

    ## SHARE example
    # Here we "lose" the scheduler because of the share operator and the fact that the first subscription is without a scheduler resulting in using the default scheduler
    # source = source.pipe(
    #     operators.share()
    # )
    # source.subscribe(
    #     lambda x: print("OUTPUT WITHOUT SCHEdULER", x, current_thread().name)
    # )
    # source.subscribe(lambda x: print("OUTPUT", x, current_thread().name), scheduler=loop)

    ## SHARE example check whether subscript on helps
    # Doesn't help..., whether before or after share
    source = source.pipe(
        # operators.subscribe_on(loop),
        operators.share(),
        operators.subscribe_on(loop),
    )
    source.subscribe(
        lambda x: print("OUTPUT WITHOUT SCHEdULER", x, current_thread().name)
    )
    source.subscribe(
        lambda x: print("OUTPUT", x, current_thread().name), scheduler=loop
    )
    time.sleep(2)
    assert True


def _test_event_and_threadpool_combine():
    loop = EventLoopScheduler()
    pool = ThreadPoolScheduler(max_workers=10)

    source = reactivex.timer(0.1, 0.1).pipe(operators.take(10))

    source.pipe(
        operators.observe_on(loop),
        operators.do_action(lambda x: print("START BLOCK", time.sleep(0.3))),
        operators.do_action(lambda x: print("END BLOCK")),
    ).subscribe(lambda x: print("BLOCK"))

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
        operators.flat_map(
            lambda x: combine_latest(
                reactivex.timer(random.randint(1, 10) / 10).pipe(
                    operators.map(lambda y: "A" + str(x))
                ),
                reactivex.timer(random.randint(1, 10) / 10).pipe(
                    operators.map(lambda y: "B" + str(x))
                ),
            ).pipe(
                operators.observe_on(loop),
                operators.do_action(
                    lambda x: print(
                        "COMBINED",
                        x,
                        time.time(),
                        current_thread().name,
                    )
                ),
            )
        ),
    )

    source.subscribe(lambda x: print("SUB", x, current_thread().name), scheduler=loop)
    time.sleep(4)
    assert False
