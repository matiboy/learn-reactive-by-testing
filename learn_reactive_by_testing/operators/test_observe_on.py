from re import sub
import threading
import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, scheduler
import reactivex
from threading import current_thread

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_observe_on_simple():
    s = scheduler.EventLoopScheduler()

    reactivex.timer(0, 0.2).pipe(operators.observe_on(s)).subscribe(
        lambda x: print(f"----- {current_thread().name} {x}")
    )
    reactivex.timer(0, 0.5).pipe(operators.observe_on(s)).subscribe(
        lambda x: print(f"///// {current_thread().name} {x}")
    )
    time.sleep(2)
    print(f"Main {current_thread().name}")


def test_observe_on_share():
    s = scheduler.EventLoopScheduler(
        thread_factory=lambda t: threading.Thread(
            target=t, daemon=True, name="Shared scheduler"
        )
    )
    s_2 = scheduler.EventLoopScheduler(
        thread_factory=lambda t: threading.Thread(
            target=t, daemon=True, name="Not shared scheduler"
        )
    )

    t = reactivex.timer(0, 0.1).pipe(operators.observe_on(s), operators.share())
    t.subscribe(lambda x: print(f"1 {current_thread().name} {x} {time.monotonic()}"))
    t.subscribe(lambda x: print(f"2 {current_thread().name} {x} {time.monotonic()}"))
    t.pipe(operators.observe_on(s_2)).subscribe(
        lambda x: print(
            f"3 {current_thread().name} {time.monotonic()} {x} {time.sleep(0.5)}"
        )
    )
    time.sleep(2)
    print(f"Main {current_thread().name}")


if __name__ == "__main__":
    # test_observe_on_simple()
    test_observe_on_share()
