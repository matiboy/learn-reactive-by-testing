import operator
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators
import reactivex
import reactivex as rx
from reactivex import create

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


def test_issue_695():
    def f(o, s):
        o.on_next(1)
        o.on_next(3)
        o.on_completed()

    def g(o, s):
        o.on_next(2)
        o.on_next(4)
        o.on_completed()

    a = create(f)
    b = create(g)

    c = rx.zip(a, b)

    c.subscribe(on_next=print, on_error=print, on_completed=lambda: print("Completed"))
    print("Ok")
