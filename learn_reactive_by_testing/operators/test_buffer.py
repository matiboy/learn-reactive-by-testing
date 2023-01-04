import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe



def test_buffer_by_value():
    """
    Release buffer when value in buffer is higher than 5
    """
    scheduler = TestScheduler()
    source = scheduler.create_cold_observable(
        on_next(100, 1),
        on_next(200, 2),
        on_next(300, 3),
        on_next(400, 4),
        on_next(500, 5),
        on_next(600, 6),
    )
    shared_source = source.pipe(
        operators.share()
    )
    def filter_larger_than_5(x):
        return x[1]
    def scan_and_reset(acc, x):
        total, should_reset = acc
        if should_reset:
            total = 0
        total += x
        return [total, total > 5]

    trigger = shared_source.pipe(
        operators.scan(
            scan_and_reset, [0, False]
        ),
        operators.filter(filter_larger_than_5)
    )
    def create():
        return shared_source.pipe(operators.buffer(trigger))
    result = scheduler.start(create)

    assert result.messages == [
        on_next(500, [1,2,3]),
        on_next(700, [4, 5]),
        on_next(800, [6]),
    ]
    assert source.subscriptions == [Subscription(200, 1000)]


def test_buffer_by_value_hot_directly():
    """
    Release buffer when value in buffer is higher than 5
    """
    scheduler = TestScheduler()
    source = scheduler.create_hot_observable(
        on_next(150, 1),
        on_next(250, 2),
        on_next(350, 3),
        on_next(450, 4),
        on_next(550, 5),
        on_next(650, 6),
    )
    def filter_larger_than_5(x):
        return x[1]
    def scan_and_reset(acc, x):
        total, should_reset = acc
        if should_reset:
            total = 0
        total += x
        return [total, total > 5]

    trigger = source.pipe(
        operators.scan(
            scan_and_reset, [0, False]
        ),
        operators.filter(filter_larger_than_5)
    )
    def create():
        return source.pipe(operators.buffer(trigger))
    result = scheduler.start(create)

    assert result.messages == [
        on_next(450, [2,3,4]),
        on_next(650, [5, 6]),
    ]
    assert source.subscriptions == [Subscription(200, 1000), Subscription(200, 1000)]
    

def test_buffer_by_value_bad_subject():
    """
    Release buffer when value in buffer is higher than 5 ; This shows a race condition caused by the intermediary subject
    """
    scheduler = TestScheduler()
    source = scheduler.create_cold_observable(
        on_next(300, 1),
        on_next(310, 2),
        on_next(320, 3),
        on_next(400, 4),
        on_next(500, 5),
        on_next(600, 6),
    )
    shared_source = source.pipe(
        operators.share()
    )
    def filter_larger_than_5(x):
        return x[1]
    def scan_and_reset(acc, x):
        total, should_reset = acc
        if should_reset:
            total = 0
        total += x
        return [total, total > 5]

    middle_man = reactivex.Subject()
    shared_source.pipe(
        operators.scan(
            scan_and_reset, [0, False]
        ),
        operators.do_action(lambda x: print('Share source', x, scheduler.clock)),
        operators.filter(filter_larger_than_5)
    ).subscribe(middle_man)
    def create():
        return shared_source.pipe(
            operators.do_action(lambda x: print('Before buffer', x, scheduler.clock)),
            operators.buffer(middle_man.pipe(operators.do_action(lambda x: print('Middle man in buffer', x, scheduler.clock))))
        )
    result = scheduler.start(create)

    # Not what we wanted
    assert result.messages == [
        on_next(320, [1, 2]),
        on_next(500, [3, 4]),
        on_next(600, [5]),
    ]
    # Also it creates an infinite subscription
    assert source.subscriptions == [Subscription(0)]
