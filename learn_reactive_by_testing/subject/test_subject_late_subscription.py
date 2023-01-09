import time
from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, Subject
from reactivex.subject import BehaviorSubject
import reactivex
import pytest

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe

def test_subscribe_to_subject_after_it_emitted():
    scheduler = TestScheduler()
    subject = Subject()
    scheduler.schedule_relative(100, lambda *_: subject.on_next(1))
    scheduler.schedule_relative(300, lambda *_: subject.on_next(3))

    result = scheduler.start(lambda: subject)

    assert result.messages == [
        on_next(300, 3)
    ]


def test_subscribe_to_behavior_subject_after_it_emitted():
    scheduler = TestScheduler()
    subject = BehaviorSubject(20)
    scheduler.schedule_relative(100, lambda *_: subject.on_next(1))
    scheduler.schedule_relative(300, lambda *_: subject.on_next(3))

    result = scheduler.start(lambda: subject)

    assert result.messages == [
        on_next(200, 1),
        on_next(300, 3)
    ]