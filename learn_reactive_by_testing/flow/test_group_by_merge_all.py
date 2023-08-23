import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of
import reactivex
from reactivex import timer, throw
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_group_by_modify_merge_all():
    scheduler = TestScheduler()

    source = scheduler.create_hot_observable(
        [on_next(200 + 10 * i, i) for i in range(10)]
    )

    def create():
        return source.pipe(
            operators.group_by(lambda x: x % 3),
            operators.map(
                lambda x: x.pipe(
                    operators.filter(lambda y: bool(y % 2)),
                    operators.map(
                        lambda y: "Group: " + str(x.key) + " Value: " + str(y)
                    ),
                )
            ),
            operators.merge_all(),
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(210, "Group: 1 Value: 1"),
        on_next(230, "Group: 0 Value: 3"),
        on_next(250, "Group: 2 Value: 5"),
        on_next(270, "Group: 1 Value: 7"),
        on_next(290, "Group: 0 Value: 9"),
    ]
