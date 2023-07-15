from reactivex.scheduler import EventLoopScheduler, ThreadPoolScheduler
from reactivex import timer, operators
from threading import Thread, current_thread
import queue
import time
import asyncio


def _test_event_loop_scheduler():
    scheduler = EventLoopScheduler(
        thread_factory=lambda target: Thread(
            name="test_event_loop_scheduler", target=target, daemon=True
        )
    )
    print(scheduler)

    def wait_a_while(x):
        print(x, current_thread().name, time.monotonic())
        time.sleep(0.2)

    timer(0.1, 0.1).pipe(
        operators.do_action(lambda x: print(current_thread().name, time.monotonic())),
        operators.take(10),
    ).subscribe(wait_a_while, scheduler=scheduler)

    time.sleep(2)


def test_event_loop_scheduler_with_share():
    scheduler_1 = EventLoopScheduler(
        thread_factory=lambda t: Thread(target=t, name="t_1", daemon=True)
    )
    scheduler_2 = EventLoopScheduler(
        thread_factory=lambda t: Thread(target=t, name="t_2", daemon=True)
    )
    scheduler_3 = EventLoopScheduler(
        thread_factory=lambda t: Thread(target=t, name="t_3")
    )

    def wait_a_while(x):
        print(f"--- {x} {current_thread().name}")
        time.sleep(0.2)

    a = timer(0.1, 0.1).pipe(
        operators.do_action(lambda x: print(f"ACTION {x} {current_thread().name}")),
        operators.publish(),
    )

    a.pipe(
        operators.observe_on(scheduler_1),
    ).subscribe(wait_a_while)
    a.pipe(operators.map(lambda x: f"@{x}")).subscribe(wait_a_while)

    s = a.connect(scheduler=scheduler_3)

    time.sleep(2)

    s.dispose()
    time.sleep(0.1)
    scheduler_3.dispose()


def _test_event_loop_scheduler_with_share():
    scheduler_1 = ThreadPoolScheduler(max_workers=1)
    scheduler_2 = ThreadPoolScheduler(max_workers=1)
    scheduler_3 = ThreadPoolScheduler(max_workers=1)

    def wait_a_while(x):
        print("---", x, current_thread().name, time.monotonic())
        time.sleep(0.2)

    a = timer(0.1, 0.1).pipe(
        operators.do_action(
            lambda x: print("YA", current_thread().name, time.monotonic())
        ),
        operators.take(10),
        operators.publish(),
    )

    a.subscribe(wait_a_while, scheduler=scheduler_1)
    a.subscribe(wait_a_while, scheduler=scheduler_2)

    a.connect(scheduler=scheduler_3)

    time.sleep(0.5)


def consumer(q):
    while item := q.get():
        print("CON", current_thread().name, item(), time.monotonic())
        time.sleep(0.5)


def _test_queue_based():
    q = queue.Queue()
    consumer_thread = Thread(target=consumer, args=(q,), name="CONSUMER")
    consumer_thread.start()

    timer(0.1, 0.1).pipe(
        operators.do_action(
            lambda x: print("YOLO", x, current_thread().name, time.monotonic())
        ),
        operators.take(10),
    ).subscribe(
        lambda x: q.put(lambda: print("ITEM", x, current_thread().name)),
    )

    a = 0


if "__main__" == __name__:
    # _test_event_loop_scheduler()
    # _test_event_loop_scheduler_with_share()
    # _test_queue_based()
    test_event_loop_scheduler_with_share()
    print("DONE")
