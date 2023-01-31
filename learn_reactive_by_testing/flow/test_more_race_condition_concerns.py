import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest
from reactivex.scheduler import ThreadPoolScheduler
import reactivex
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


# The goal is to modify the source emissions but emitting the modified version _along_ with the source ones, without running into race conditions

def test_using_share_and_with_latest_from_more_complex_modification():
    scheduler = ThreadPoolScheduler()
    outcome = []
    source = reactivex.interval(0.001)
    shared_source = source.pipe(
        operators.share()
    )
    b = shared_source.pipe(operators.do_action(lambda x: outcome.append(f'WLF {x}')))
    a = shared_source.pipe(
        operators.do_action(lambda x: outcome.append(f'MOD {x}')))
    modified_source = a.pipe(
        operators.scan(lambda acc, x: acc + x, 0)
    )

    def create():
        return modified_source.pipe(
            operators.with_latest_from(b)
        )

    create().subscribe(on_next=lambda x: outcome.append(x))

    time.sleep(0.1)

    assert outcome

