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



def test_merge_all_behavior():
    scheduler = TestScheduler()
    inner = scheduler.create_cold_observable(
        on_next(100, 1),
        on_next(130, 2),
        on_next(220, 3),
        on_completed(300)
    )
    xs = scheduler.create_cold_observable(
        on_next(50, inner),
        on_next(150, inner),
        on_completed(300)
    )
    
    result = scheduler.start(lambda: xs.pipe(operators.merge_all()))
    assert result.messages == [
        on_next(350, 1),
        on_next(380, 2),
        on_next(450, 1),
        on_next(470, 3),
        on_next(480, 2),
        on_next(570, 3),
        on_completed(650)
    ]
