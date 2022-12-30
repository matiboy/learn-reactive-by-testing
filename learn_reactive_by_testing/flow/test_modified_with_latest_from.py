from reactivex.notification import OnError
from reactivex.testing import ReactiveTest, TestScheduler
from reactivex.testing.subscription import Subscription
from reactivex import operators, interval, concat, combine_latest, of

on_next = ReactiveTest.on_next
on_error = ReactiveTest.on_error
on_completed = ReactiveTest.on_completed
subscribe = ReactiveTest.subscribe


# The goal is to modify the source emissions but emitting the modified version _along_ with the source ones, without running into race conditions


def test_using_map():
    scheduler = TestScheduler()

    source = scheduler.create_hot_observable(
        on_next(100, 5),
        on_next(250, 10),
        on_next(350, 100),
    )

    def create():
        return source.pipe(
            operators.map(lambda x: (str(x), x))
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, ('10', 10)),
        on_next(350, ('100', 100)),
    ]
    assert source.subscriptions == [Subscription(200, 1000)]

def test_using_share_and_with_latest_from():
    scheduler = TestScheduler()

    source = scheduler.create_hot_observable(
        on_next(100, 5),
        on_next(250, 10),
        on_next(350, 100),
    )
    shared_source = source.pipe(
        operators.share()
    )
    modified_source = shared_source.pipe(
        operators.map(str)
    )

    def create():
        return modified_source.pipe(
            operators.with_latest_from(shared_source)
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, ('10', 10)),
        on_next(350, ('100', 100)),
    ]

    assert source.subscriptions == [Subscription(200, 1000)]

def test_using_share_and_with_latest_from_more_complex_modification():
    scheduler = TestScheduler()

    source = scheduler.create_hot_observable(
        on_next(100, 5),
        on_next(250, 10),
        on_next(350, 100),
    )
    shared_source = source.pipe(
        operators.share()
    )
    modified_source = shared_source.pipe(
        operators.scan(lambda acc, x: acc + x, 0)
    )

    def create():
        return modified_source.pipe(
            operators.with_latest_from(shared_source)
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, (10, 10)),
        on_next(350, (110, 100)),
    ]

    assert source.subscriptions == [Subscription(200, 1000)]



def test_without_share():
    scheduler = TestScheduler()

    source = scheduler.create_hot_observable(
        on_next(100, 5),
        on_next(250, 10),
        on_next(350, 100),
    )
    modified_source = source.pipe(
        operators.scan(lambda acc, x: acc + x, 0)
    )

    def create():
        return modified_source.pipe(
            operators.with_latest_from(source)
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, (10, 10)),
        on_next(350, (110, 100)),
    ]

    assert source.subscriptions == [Subscription(200, 1000), Subscription(200, 1000)]



def test_without_share_dispose():
    scheduler = TestScheduler()

    source = scheduler.create_hot_observable(
        on_next(100, 5),
        on_next(250, 10),
        on_next(350, 100),
    )
    modified_source = source.pipe(
        operators.scan(lambda acc, x: acc + x, 0)
    )

    def create():
        return modified_source.pipe(
            operators.with_latest_from(source),
            operators.take(2)
        )

    results = scheduler.start(create)

    assert results.messages == [
        on_next(250, (10, 10)),
        on_next(350, (110, 100)),
        on_completed(350),
    ]

    assert source.subscriptions == [Subscription(200, 350), Subscription(200, 350)]

