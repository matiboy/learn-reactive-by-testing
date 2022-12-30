from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
subscribe = ReactiveTest.subscribe

"""
The goal here is to combine a major observable with a secondary one as follows:

1. When major emits, emit its value together with latest from secondary
2. If major is the first to emit, wait for first from secondary
3. If secondary is the first to emit, and does not emit a second time before major emits, we must emit major + first value of secondary
"""

def version_1(major, secondary):
    return concat(
        secondary.pipe(
            operators.take(1),
            operators.ignore_elements()
        ),
        major.pipe(
            operators.with_latest_from(
                secondary
            )
        )
    )

def version_3(major, secondary):
    return concat(
        combine_latest(
            major, secondary
        ).pipe(operators.take(1)),
        major.pipe(
            operators.with_latest_from(secondary)
        )
    )

def version_4(major, secondary):
    s = secondary.pipe(
        operators.replay(1),
        operators.ref_count(),
    )
    def reduce(acc, i):
        return acc + [i]
    
    def flatten(x):
        return of(
            *[(i, x[1]) for i in x[0]]
        )

    obs = concat(
        combine_latest(
            major.pipe(
                operators.take_until(s),
                operators.reduce(reduce, []),
            ), s,
        ).pipe(
            operators.take(1),
            operators.flat_map(flatten),
        ),
        major.pipe(
            operators.with_latest_from(s)
        )
    )
    return obs


def test_v4_major_is_second():
    scheduler = TestScheduler()
    secondary = scheduler.create_hot_observable([
        on_next(150 + 50*i, i) for i in range(10)
    ])
    major = scheduler.create_hot_observable(
        on_next(310, 42),
        on_next(480, 5),
    )

    def create():
        return version_4(major, secondary)

    results = scheduler.start(create)
    assert results.messages == [
        on_next(310, (42, 3)),
        on_next(480, (5, 6)),
    ]
    assert major.subscriptions == [Subscription(200.0, 250.0), Subscription(250.0, 1000.0)]
    assert secondary.subscriptions == [Subscription(200.0, 250.0), Subscription(250.0, 1000.0)]


def test_wait_for_emission_slow_major():
    scheduler = TestScheduler()
    secondary = scheduler.create_hot_observable([
        on_next(150 + 50*i, i) for i in range(10)
    ])
    major = scheduler.create_hot_observable(
        on_next(310, 42),
        on_next(480, 5),
    )

    def create():
        return version_1(major, secondary)

    results = scheduler.start(create)
    assert results.messages == [
        on_next(310, (42, 3)),
        on_next(480, (5, 6)),
    ]


def test_v1_misses_early_emission():
    scheduler = TestScheduler()
    secondary = scheduler.create_hot_observable([
        on_next(150, 0)
    ])
    major = scheduler.create_hot_observable(
        on_next(300, 42),
        on_next(480, 5),
    )

    def create():
        return version_1(major, secondary)

    results = scheduler.start(create)
    # Not what we want
    assert results.messages == []


def test_dont_miss_early_emissions():
    scheduler = TestScheduler()
    # Let's have an observable which emits before major one does
    # How to make sure we get that as value when major finally emits
    secondary = scheduler.create_hot_observable([
        on_next(250, 0)
    ])
    major = scheduler.create_hot_observable(
        on_next(300, 42),
        on_next(480, 5),
    )
    intermediary = secondary.pipe(
        operators.replay(1),
        operators.ref_count()
    )
    def create():
        return major.pipe(
            operators.with_latest_from(
                intermediary
            )
        )



def test_replay_intermediary_slow_secondary():
    scheduler = TestScheduler()
    # Let's have an observable which emits before major one does
    # How to make sure we get that as value when major finally emits
    secondary = scheduler.create_hot_observable([
        on_next(450, 0)
    ])
    major = scheduler.create_hot_observable(
        on_next(300, 42),
        on_next(480, 5),
    )
    intermediary = secondary.pipe(
        operators.replay(1),
        operators.ref_count()
    )
    def create():
        return major.pipe(
            operators.with_latest_from(
                intermediary
            )
        )
        

    results = scheduler.start(create)
    # Not what we want, we don't get the initial major
    assert results.messages == [
        on_next(480, (5, 0)),
    ]
    # Verify that we unsubscribed one done
    assert secondary.subscriptions == [Subscription(200, 1000)]


def test_dont_miss_early_emissions_but_fail_to_dispose():
    scheduler = TestScheduler()
    # Let's have an observable which emits before major one does
    # How to make sure we get that as value when major finally emits
    secondary = scheduler.create_hot_observable([
        on_next(250, 0)
    ])
    major = scheduler.create_hot_observable(
        on_next(300, 42),
        on_next(480, 5),
    )
    intermediary = secondary.pipe(
        operators.replay(1),
    )
    intermediary.connect()
    def create():
        return major.pipe(
            operators.with_latest_from(
                intermediary
            )
        )
        

    results = scheduler.start(create)
    assert results.messages == [
        on_next(300, (42, 0)),
        on_next(480, (5, 0)),
    ]
    # This would result in an infinite subscription
    assert secondary.subscriptions == [Subscription(0)]


def test_v3_major_is_second():
    scheduler = TestScheduler()
    secondary = scheduler.create_hot_observable([
        on_next(150 + 50*i, i) for i in range(10)
    ])
    major = scheduler.create_hot_observable(
        on_next(310, 42),
        on_next(480, 5),
    )

    def create():
        return version_3(major, secondary)

    results = scheduler.start(create)
    assert results.messages == [
        on_next(310, (42, 3)),
        on_next(480, (5, 6)),
    ]
    assert major.subscriptions == [Subscription(200.0, 310.0), Subscription(310.0, 1000.0)]
    assert secondary.subscriptions == [Subscription(200.0, 310.0), Subscription(310.0, 1000.0)]


def test_v3_major_is_second():
    scheduler = TestScheduler()
    secondary = scheduler.create_hot_observable([
        on_next(150 + 50*i, i) for i in range(10)
    ])
    major = scheduler.create_hot_observable(
        on_next(310, 42),
        on_next(480, 5),
    )

    def create():
        return version_3(major, secondary)

    results = scheduler.start(create)
    assert results.messages == [
        on_next(310, (42, 3)),
        on_next(480, (5, 6)),
    ]
    assert major.subscriptions == [Subscription(200.0, 310.0), Subscription(310.0, 1000.0)]
    assert secondary.subscriptions == [Subscription(200.0, 310.0), Subscription(310.0, 1000.0)]

def test_v4_major_emits_first():
    scheduler = TestScheduler()
    # Let's have an observable which emits before major one does
    # How to make sure we get that as value when major finally emits
    secondary = scheduler.create_hot_observable([
        on_next(350, 0)
    ])
    major = scheduler.create_hot_observable(
        on_next(300, 42),
        on_next(480, 5),
    )
    
    def create():
        return version_4(major, secondary)
        

    results = scheduler.start(create)
    assert results.messages == [
        on_next(350, (42, 0)),
        on_next(480, (5, 0)),
    ]
    # Verify that we unsubscribed one done
    assert secondary.subscriptions == [
        Subscription(200, 350),
        Subscription(350, 1000)
    ]
    assert major.subscriptions == [
        Subscription(200, 350),
        Subscription(350, 1000)
    ]

def test_v4_major_emits_first_multiple():
    scheduler = TestScheduler()
    # Let's have an observable which emits before major one does
    # How to make sure we get that as value when major finally emits
    secondary = scheduler.create_hot_observable([
        on_next(350, 0),
        on_next(400, 1),
        on_next(500, 2),
    ])
    major = scheduler.create_hot_observable(
        on_next(250, 1),
        on_next(300, 2),
        on_next(320, 3),
        on_next(480, 4),
        on_next(600, 5),
        on_next(700, 6),
    )
    
    def create():
        return version_4(major, secondary)
        

    results = scheduler.start(create)
    assert results.messages == [
        on_next(350, (1, 0)),
        on_next(350, (2, 0)),
        on_next(350, (3, 0)),
        on_next(480, (4, 1)),
        on_next(600, (5, 2)),
        on_next(700, (6, 2)),
    ]
    # Verify that we unsubscribed one done
    assert secondary.subscriptions == [
        Subscription(200, 350),
        Subscription(350, 1000)
    ]
    assert major.subscriptions == [
        Subscription(200, 350),
        Subscription(350, 1000)
    ]