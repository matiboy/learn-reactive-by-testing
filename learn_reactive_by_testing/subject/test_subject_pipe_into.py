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

def test_pipe_into_subject_message():
    scheduler = TestScheduler()
    subject = Subject()
    obs = scheduler.create_hot_observable(
        on_next(300, 42)
    )
    records = []
    def record(x):
        records.append(on_next(scheduler.clock, x))
    obs.subscribe(subject, scheduler=scheduler)
    subject.subscribe(on_next=record)
    results = scheduler.start(lambda: obs)
    assert records == [
        on_next(300, 42)
    ]

def test_pipe_into_subject_multiple():
    scheduler = TestScheduler()
    subject = Subject()
    obs = scheduler.create_hot_observable(
        on_next(300, 42)
    )
    obs2 = scheduler.create_hot_observable(
        on_next(350, 100)
    )
    records = []
    def record(x):
        records.append(on_next(scheduler.clock, x))
    obs.subscribe(subject, scheduler=scheduler)
    obs2.subscribe(subject, scheduler=scheduler)
    subject.subscribe(on_next=record)
    scheduler.start()
    assert records == [
        on_next(300, 42),
        on_next(350, 100),
    ]

def test_pipe_into_subject_multiple_after_complete():
    """Note that completing one obs which "feeds" into the subject also completes the subject"""
    scheduler = TestScheduler()
    subject = Subject()
    obs = scheduler.create_hot_observable(
        on_next(300, 42),
        on_completed(320)
    )
    obs2 = scheduler.create_hot_observable(
        on_next(310, 100),
        on_next(350, 100),
    )
    records = []
    def record(x=None):
        notification = on_next(scheduler.clock, x) if x else on_completed(scheduler.clock)
        records.append(notification)
    obs.subscribe(subject, scheduler=scheduler)
    obs2.subscribe(subject, scheduler=scheduler)
    subject.subscribe(on_next=record, on_error=record, on_completed=record)
    scheduler.start()
    assert records == [
        on_next(300, 42),
        on_next(310, 100),
        on_completed(320),
    ]