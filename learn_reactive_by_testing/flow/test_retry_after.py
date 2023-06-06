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

def test_make_wait_with_error():
    wait = reactivex.from_marbles('-----#', timespan=10, error=Exception('Exc'))
    using_operators = timer(50).pipe(
        operators.flat_map(lambda x: throw(Exception('Exc')))
    )

    s = TestScheduler()
    results_wait = s.start(lambda: wait)
    s = TestScheduler()
    results_operators = s.start(lambda: using_operators)

    assert results_wait.messages == results_operators.messages


def test_retry_after_delay():
    scheduler = TestScheduler()
    source1 = reactivex.from_marbles('-1-#', timespan=10)
    source2 = reactivex.from_marbles('--2---3---|', timespan=10)
    wait = reactivex.from_marbles('-----#', timespan=10) # Error after 50 ticks

    #            -1-#
    #               -----#
    #                    -1-#
    #                       -----#
    #                            --2---3---|
    # Expected   -1-------1--------2---3---|

    def sources():
        yield source1
        yield source1
        yield source2
    i = sources()

    source = reactivex.defer(lambda _: next(i))

    def create():
        return source.pipe(
            operators.catch(lambda *_: wait),
            operators.retry()
        )

    result = scheduler.start(create)

    assert result.messages == [
        on_next(210, 1),
        on_next(290, 1),
        on_next(380, 2),
        on_next(420, 3),
        on_completed(460),
    ]

    # TODO test subscriptions; that's not available when using `from_marbles` though
    # assert source1
