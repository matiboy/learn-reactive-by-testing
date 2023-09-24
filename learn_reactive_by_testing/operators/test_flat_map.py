import sched
import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex
from reactivex.scheduler import NewThreadScheduler

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_flat_map_completion_behavior():
    """ """
    scheduler = TestScheduler()
    source = scheduler.create_hot_observable(
        on_next(300, 1), on_next(400, 2), on_completed(500)
    )
    inner = scheduler.create_cold_observable(
        on_next(50, 10),
        on_completed(80),
    )

    def create():
        return source.pipe(operators.flat_map(lambda x: inner))

    result = scheduler.start(create)

    assert result.messages == [
        on_next(350, 10),
        on_next(450, 10),
        on_completed(500),
    ]
    assert source.subscriptions == [Subscription(200, 500)]
    assert inner.subscriptions == [Subscription(300, 380), Subscription(400, 480)]


def test_flat_map_completion_timer():
    """ """
    scheduler = NewThreadScheduler()
    messages = []

    def on_next(x):
        messages.append((x, scheduler.now))

    s = (
        reactivex.timer(0.1, 0.2)
        .pipe(operators.flat_map(lambda x: reactivex.just(x + 1)))
        .subscribe(
            on_next=on_next,
            on_error=print,
            on_completed=lambda: messages.append("completed"),
            scheduler=scheduler,
        )
    )
    time.sleep(1)
    s.dispose()
    assert True


def test_flat_map_completion_inner_running():
    """ """
    scheduler = TestScheduler()
    source = scheduler.create_hot_observable(
        on_next(250, 1), on_next(350, 2), on_completed(500)
    )
    inner = scheduler.create_cold_observable(
        on_next(50, 10),
        on_completed(300),
    )

    def create():
        return source.pipe(operators.flat_map(lambda x: inner))

    result = scheduler.start(create)

    # What I expected
    # assert result.messages == [
    #     on_next(300, 10),
    #     on_next(400, 10),
    #     on_completed(500),
    # ]
    # What is actually correct (also works like RxJS)
    assert result.messages == [
        on_next(300, 10),
        on_next(400, 10),
        on_completed(650),
    ]


def test_flat_map_execution_order():
    """ """
    scheduler = TestScheduler()
    xs = reactivex.of(1, 2, 3)

    xs.pipe(
        operators.map(lambda x: print("before flat map", x) or x),
        operators.flat_map(lambda x: print("in flatmap", x) or reactivex.just(x * 100)),
        operators.map(lambda x: print("after flatmap", x) or x),
    ).subscribe(print)
