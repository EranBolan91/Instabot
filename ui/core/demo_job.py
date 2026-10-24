"""A fake bot for trying the Jobs and Log panels without opening Chrome.

Temporary: remove it in phase 4, once the pages run the real bots.
"""
import threading

STEPS = 8
STEP_SECONDS = 1.5


class _DemoDriver:
    def __init__(self):
        self.closed = threading.Event()

    def quit(self):
        self.closed.set()


class DemoBot:
    def __init__(self, username):
        self.username = username
        self.driver = _DemoDriver()

    def run(self):
        for step in range(1, STEPS + 1):
            print("Demo: {} -- step {}/{}".format(self.username, step, STEPS))
            if self.driver.closed.wait(STEP_SECONDS):
                print("Demo: Chrome was closed, stopping")
                return step
        print("Demo: finished all steps")
        return STEPS
