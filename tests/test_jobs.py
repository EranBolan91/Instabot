"""Phase 2: jobs, Jobs panel and Log panel, with fake bots (Chrome never opens)."""
import threading

import pytest

from ui.core.jobs import CANCELLED, DONE, FAILED, RUNNING, SCHEDULED, JobManager, job_id_from_thread_name
from ui.widgets.jobs_panel import format_delta

WAIT_MS = 5000


class FakeDriver:
    def __init__(self):
        self.closed = threading.Event()

    def quit(self):
        self.closed.set()


class FakeBot:
    """Stands in for a real bot: has a .driver and prints its progress."""

    instances = []

    def __init__(self, username):
        self.username = username
        self.driver = FakeDriver()
        self.thread_name = None
        FakeBot.instances.append(self)

    def work(self, steps=2):
        self.thread_name = threading.current_thread().name
        for step in range(steps):
            print("fake bot {} step {}".format(self.username, step + 1))
        return "result of " + self.username

    def wait_until_stopped(self):
        print("fake bot waiting")
        if not self.driver.closed.wait(10):
            raise AssertionError("never stopped")
        raise RuntimeError("chrome not reachable")  # what selenium does after quit()


@pytest.fixture(autouse=True)
def _reset_bots():
    FakeBot.instances.clear()


def _submit(window, run, delay=0, on_result=None, username="alice"):
    return window.jobs.submit("Test", username, "fake job", make_bot=lambda: FakeBot(username), run=run,
                              delay_seconds=delay, on_result=on_result)


def test_job_runs_off_the_gui_thread_and_reports_its_result(make_window, qtbot, log_bridge):
    window = make_window(log_bridge=log_bridge)
    log_bridge.install()
    results = []
    job = _submit(window, lambda bot: bot.work(), on_result=results.append)

    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)
    assert results == ["result of alice"]
    bot = FakeBot.instances[0]
    assert bot.thread_name == "job-{}".format(job.id)
    assert threading.current_thread().name == "MainThread"
    assert job.started_at and job.finished_at


def test_job_prints_reach_the_log_panel_tagged_with_the_job(make_window, qtbot, log_bridge):
    window = make_window(log_bridge=log_bridge)
    log_bridge.install()
    job = _submit(window, lambda bot: bot.work())
    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)
    qtbot.waitUntil(lambda: any("step 2" in line for line in window.log_panel.lines()), timeout=WAIT_MS)

    lines = [line for line in window.log_panel.lines() if "fake bot alice" in line]
    assert len(lines) == 2
    assert all("#{}".format(job.id) in line for line in lines)


def test_log_filter_shows_one_job(make_window, qtbot, log_bridge):
    window = make_window(log_bridge=log_bridge)
    log_bridge.install()
    first = _submit(window, lambda bot: bot.work(), username="alice")
    second = _submit(window, lambda bot: bot.work(), username="bob")
    qtbot.waitUntil(lambda: first.status == DONE and second.status == DONE, timeout=WAIT_MS)
    qtbot.waitUntil(lambda: sum("fake bot" in line for line in window.log_panel.lines()) == 4, timeout=WAIT_MS)

    window.show_job_log(second.id)
    lines = window.log_panel.lines()
    assert lines and all("bob" in line for line in lines)

    window.log_panel.filter_combo.setCurrentIndex(0)  # All jobs
    assert sum("fake bot" in line for line in window.log_panel.lines()) == 4


def test_failing_job_is_marked_failed(make_window, qtbot):
    window = make_window()

    def explode(bot):
        raise ValueError("selector not found")

    job = _submit(window, explode)
    qtbot.waitUntil(lambda: job.status == FAILED, timeout=WAIT_MS)
    assert "selector not found" in job.error
    assert "failed" in window.status_label.text()
    assert window.toast.isVisible()


def test_scheduled_job_waits_then_runs(make_window, qtbot):
    window = make_window()
    job = _submit(window, lambda bot: bot.work(), delay=1)
    assert job.status == SCHEDULED
    assert not FakeBot.instances  # Chrome would not be open yet
    assert window.jobs_panel.action_button(job.id).text() == "Cancel"

    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)


def test_cancelled_scheduled_job_never_runs(make_window, qtbot):
    window = make_window()
    job = _submit(window, lambda bot: bot.work(), delay=3600)
    assert "1 scheduled" in window.jobs_dock.windowTitle()

    window.jobs_panel.action_button(job.id).click()
    assert job.status == CANCELLED
    assert window.jobs_panel.action_button(job.id) is None
    qtbot.wait(1200)  # past a ticker tick
    assert not FakeBot.instances
    assert window.jobs_dock.windowTitle() == "Jobs"


def test_stopping_a_running_job_closes_chrome_and_keeps_it_cancelled(make_window, qtbot):
    window = make_window()
    finished = []
    window.jobs.job_finished.connect(finished.append)
    job = _submit(window, lambda bot: bot.wait_until_stopped())

    qtbot.waitUntil(lambda: job.status == RUNNING, timeout=WAIT_MS)
    assert window.running_label.text() == "1 running"
    assert window.jobs_panel.action_button(job.id).text() == "Stop"

    assert window.jobs.stop(job.id)
    qtbot.waitUntil(lambda: not window.jobs.has_live_threads(), timeout=WAIT_MS)
    assert FakeBot.instances[0].driver.closed.is_set()
    # the bot crashed after its Chrome closed, but the job stays "cancelled"
    assert job.status == CANCELLED
    assert finished == [job]
    assert window.running_label.text() == "0 running"


def test_several_jobs_run_in_parallel(make_window, qtbot):
    window = make_window()
    jobs = [_submit(window, lambda bot: bot.wait_until_stopped(), username=name) for name in ("a", "b", "c")]
    qtbot.waitUntil(lambda: all(job.status == RUNNING for job in jobs), timeout=WAIT_MS)
    assert window.jobs.running_count() == 3
    for job in jobs:
        window.jobs.stop(job.id)


def test_clear_finished_removes_only_finished_jobs(make_window, qtbot):
    window = make_window()
    done = _submit(window, lambda bot: bot.work())
    waiting = _submit(window, lambda bot: bot.work(), delay=3600)
    qtbot.waitUntil(lambda: done.status == DONE, timeout=WAIT_MS)

    window.jobs_panel.clear_button.click()
    assert window.jobs.get(done.id) is None
    assert window.jobs_panel.model.rowCount() == 1
    assert window.jobs_panel.action_button(waiting.id).text() == "Cancel"
    assert window.log_panel.filter_combo.findData(done.id) == -1


def test_block_lines_are_highlighted_and_toasted(make_window, qtbot, log_bridge):
    window = make_window(log_bridge=log_bridge)
    log_bridge.install()
    blocked = []
    window.log_panel.block_detected.connect(lambda job_id, line: blocked.append(job_id))

    job = _submit(window, lambda bot: print("User: alice has been blocked.\nSection: Hashtag"))
    qtbot.waitUntil(lambda: blocked == [job.id], timeout=WAIT_MS)
    assert window.toast.isVisible()
    assert "@alice" in window.toast.text()


def test_job_manager_without_a_window(qapp, qtbot):
    from PySide6.QtCore import QThreadPool

    manager = JobManager(pool=QThreadPool())
    job = manager.submit("Test", "alice", "fake", make_bot=lambda: FakeBot("alice"), run=lambda bot: bot.work(1))
    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)
    manager.pool.waitForDone(WAIT_MS)


def test_thread_names_map_to_job_ids():
    assert job_id_from_thread_name("job-12") == 12
    assert job_id_from_thread_name("MainThread") == 0
    assert job_id_from_thread_name("job-x") == 0


@pytest.mark.parametrize("seconds, text", [(5, "5s"), (125, "2m 05s"), (3725, "1h 02m 05s"), (90000, "1d 01h")])
def test_format_delta(seconds, text):
    from datetime import timedelta

    assert format_delta(timedelta(seconds=seconds)) == text
