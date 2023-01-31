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


def test_process_list_in_chunks_throttled():
    scheduler = TestScheduler()
    my_list = list(range(20))

    t = reactivex.timer(0, 100, scheduler=scheduler)
    def process(item):
        return scheduler.create_cold_observable(
            on_completed(50)
        )
    per_chunk = 6
    def create():
        return t.pipe(
            operators.take_while(lambda i: len(my_list) > (i+1) * per_chunk, inclusive=True),
            operators.flat_map(lambda i: reactivex.merge(
                *[
                    process(k).pipe(
                        operators.concat(reactivex.just(k))
                    ) for k in my_list[i*per_chunk:(i+1)*per_chunk]
                ]
            ).pipe(
                operators.reduce(lambda acc, x: acc + [x], [])
            ))
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, [0,1,2,3,4,5]),
        on_next(350, [6,7,8,9,10,11]),
        on_next(450, [12,13,14,15,16,17]),
        on_next(550, [18,19]),
        on_completed(550)
    ]
