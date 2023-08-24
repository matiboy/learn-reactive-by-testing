from reactivex import operators, timer
from reactivex.scheduler import EventLoopScheduler
from threading import current_thread
import time


def test_scheduler_on_timer():
    scheduler = EventLoopScheduler()
    scheduler_2 = EventLoopScheduler()

    def log(x):
        print(x, current_thread().name, scheduler._thread.name)

    timer(0, 0.1, scheduler=scheduler).pipe(
        operators.take(10),
        operators.observe_on(scheduler_2),
        operators.do_action(log),
    ).subscribe(print, scheduler=scheduler_2)
    time.sleep(2)
