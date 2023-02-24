import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of
import reactivex
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


# The goal is to modify the source emissions but emitting the modified version _along_ with the source ones, without running into race conditions


def test_sequential():
    """Call sources sequentially then wrap them into a single item
    Useful for sequential API calls for example
    If they depended on each other though, might need to use flat_map
    """
    scheduler = TestScheduler()

    source_1 = scheduler.create_cold_observable(
        on_next(100, 5),
        on_completed(120)
    )

    source_2 = scheduler.create_cold_observable(
        on_next(80, 42),
        on_completed(150)
    )

    def create():
        return concat(
            source_1, source_2
        ).pipe(
            operators.to_list()
        )

    result = scheduler.start(create)

    assert result.messages == [
        on_next(470, [5, 42]),
        on_completed(470)
    ]