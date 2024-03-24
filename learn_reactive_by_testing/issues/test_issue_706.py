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


def test_issue_706():
    scheduler = TestScheduler()
    messages = [
        on_next(200 + (i + 1) * 10, x)
        for i, x in enumerate([1, 2, 3, 2, 4, 5, 0, 2, 1, 3, 4, 5, 2, 2, 1, 4, 5])
    ]
    print(messages)
    numbers = scheduler.create_hot_observable(messages)

    numbers_shared = numbers.pipe(operators.share())

    def create():
        return numbers_shared.pipe(
            operators.window_toggle(
                numbers_shared.pipe(
                    operators.do_action(lambda x: print("start", x)),
                    operators.filter(lambda x: x == 1),
                ),
                lambda _: numbers_shared.pipe(
                    operators.do_action(lambda x: print("end", x)),
                    operators.filter(lambda x: x == 5),
                ),
            ),
            operators.flat_map(lambda window: window.pipe(operators.to_list())),
        )

    results = scheduler.start(create=create)

    assert results.messages == [
        on_next(260, [1, 2, 3, 2, 4, 5]),
        on_next(320, [1, 3, 4, 5]),
        on_next(370, [1, 4, 5]),
    ]


def test_issue_706_run_scan():
    messages = reactivex.from_list(
        [1, 2, 3, 2, 4, 5, 0, 3, 4, 2, 1, 3, 4, 5, 2, 2, 1, 4, 5]
    )

    def handle(acc, x):
        if x == 5:
            return acc[1] + [x], []
        if x == 1 or len(acc[1]) > 0:
            return None, acc[1] + [x]
        return None, []

    outcome = messages.pipe(
        operators.scan(
            lambda acc, x: (acc[1] + [x], [])
            if x == 5
            else ((None, acc[1] + [x]) if (x == 1 or len(acc[1]) > 0) else (None, [])),
            (None, []),
        ),
        operators.filter(lambda x: x[0] is not None),
        operators.map(lambda x: x[0]),
        operators.to_list(),
    ).run()

    assert outcome == [
        [1, 2, 3, 2, 4, 5],
        [1, 3, 4, 5],
        [1, 4, 5],
    ]


# @pytest.mark.run_this_test
def test_issue_706_run_custom():
    def list_from_to(start_number, end_number):
        lock = threading.Lock()
        current_values = []
        is_on = False

        def operator(source):
            def subscribe(observer, scheduler=None):
                def on_next(value):
                    nonlocal is_on
                    with lock:
                        if value == start_number:
                            is_on = True
                        if is_on:
                            current_values.append(value)
                        if value == end_number:
                            is_on = False
                            observer.on_next(list(current_values))
                            current_values.clear()

                return source.subscribe(
                    on_next=on_next,
                    on_completed=observer.on_completed,
                    on_error=observer.on_error,
                    scheduler=scheduler,
                )

            return Observable(subscribe)

        return operator

    messages = reactivex.from_list(
        [1, 2, 3, 2, 4, 5, 0, 3, 4, 2, 1, 3, 4, 5, 2, 2, 1, 4, 5]
    )

    outcome = messages.pipe(list_from_to(1, 5), operators.to_list()).run()
    assert outcome == [
        [1, 2, 3, 2, 4, 5],
        [1, 3, 4, 5],
        [1, 4, 5],
    ]


# @pytest.mark.run_this_test
def test_issue_706_run():
    messages = reactivex.from_list(
        [1, 2, 3, 2, 4, 5, 0, 3, 4, 200, 1, 3, 4, 5, 2, 2, 1, 4, 5]
    )

    numbers_shared = messages.pipe(operators.share())

    outcome = numbers_shared.pipe(
        operators.do_action(
            lambda x: print("NUMBER", x, threading.current_thread().name)
        ),
        operators.window_toggle(
            numbers_shared.pipe(
                # operators.do_action(lambda x: print("start", x)),
                operators.filter(lambda x: x == 1),
            ),
            lambda _: numbers_shared.pipe(
                # operators.do_action(lambda x: print("end", x)),
                operators.filter(lambda x: x == 5),
            ),
        ),
        operators.flat_map(lambda window: window.pipe(operators.to_list())),
        operators.do_action(
            lambda x: print("AFTER FLAT", x, threading.current_thread().name)
        ),
        operators.to_list(),
    ).run()

    print(outcome)
    return

    messages = reactivex.from_list(
        [1, 2, 3, 2, 4, 5, 0, 3, 4, 2, 1, 3, 4, 5, 2, 2, 1, 4, 5]
    )
    numbers_shared = messages.pipe(operators.share())
    numbers_shared.pipe(
        ops.window_toggle(
            numbers_shared.pipe(
                ops.filter(lambda x: x == 1),
            ),
            lambda _: numbers_shared.pipe(
                ops.filter(lambda x: x == 5),
            ),
        ),
        ops.flat_map(lambda window: window.pipe(ops.to_list())),
        ops.to_list(),
    ).subscribe(print)
