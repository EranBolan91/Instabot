"""Background jobs: every bot run goes through JobManager.

A job is two callables:
  make_bot()  -> builds the bot. Creating a bot opens Chrome, so this runs on
                 the worker thread, never on the GUI thread.
  run(bot)    -> calls the bot method; its return value goes to on_result.

Keeping them separate lets the worker hold on to the bot, so a running job
can be stopped by closing its Chrome window (bot.driver.quit()).
"""
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import count

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

SCHEDULED = "scheduled"
QUEUED = "queued"  # handed to the thread pool, waiting for a free thread
RUNNING = "running"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"

ACTIVE_STATUSES = (SCHEDULED, QUEUED, RUNNING)

# several accounts can run at the same time, like the old threading.Thread jobs
MAX_PARALLEL_JOBS = 8


@dataclass
class Job:
    id: int
    kind: str  # "HashTag", "Location", "Unfollow", ...
    account: str
    description: str  # e.g. "#sunset · 50 posts · like+follow"
    status: str
    run_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None

    @property
    def is_active(self):
        return self.status in ACTIVE_STATUSES

    @property
    def label(self):
        return "#{} {} @{}".format(self.id, self.kind, self.account)


def thread_name_for(job_id):
    return "job-{}".format(job_id)


def job_id_from_thread_name(name):
    """The job id a log line came from, or 0 for the app itself."""
    if name.startswith("job-") and name[4:].isdigit():
        return int(name[4:])
    return 0


def _quit_driver(bot):
    driver = getattr(bot, "driver", None)
    if driver is None:
        return
    try:
        driver.quit()
    except Exception as e:
        print("Stop job: closing Chrome failed:", e)


class _WorkerSignals(QObject):
    started = Signal(int)
    finished = Signal(int, object)
    failed = Signal(int, str)


class JobWorker(QRunnable):
    def __init__(self, job_id, make_bot, run):
        super().__init__()
        # JobManager keeps the reference; Qt must not delete the Python object
        self.setAutoDelete(False)
        self.job_id = job_id
        self.signals = _WorkerSignals()
        self._make_bot = make_bot
        self._run = run
        self._lock = threading.Lock()
        self._bot = None
        self._stop_requested = False

    def run(self):
        thread = threading.current_thread()
        old_name = thread.name
        # the log bridge tags every printed line with this name
        thread.name = thread_name_for(self.job_id)
        try:
            self.signals.started.emit(self.job_id)
            with self._lock:
                if self._stop_requested:
                    # stopped before a thread was free: don't open Chrome at all
                    self.signals.finished.emit(self.job_id, None)
                    return
            try:
                bot = self._make_bot()
                with self._lock:
                    self._bot = bot
                    stop = self._stop_requested
                if stop:
                    _quit_driver(bot)
                    result = None
                else:
                    result = self._run(bot)
            except Exception as e:
                traceback.print_exc()
                self.signals.failed.emit(self.job_id, "{}: {}".format(type(e).__name__, e))
            else:
                self.signals.finished.emit(self.job_id, result)
        finally:
            thread.name = old_name

    def request_stop(self, wait=False):
        """Close the bot's Chrome window. The bot's own error handling then ends the run."""
        with self._lock:
            self._stop_requested = True
            bot = self._bot
        if bot is None:
            return  # not built yet; run() quits it right after building
        if wait:
            _quit_driver(bot)
        else:
            # quitting Chrome can take a few seconds; keep the GUI responsive
            threading.Thread(target=_quit_driver, args=(bot,), daemon=True).start()


class JobManager(QObject):
    """Owns every job: schedules, starts, cancels and stops them.

    All Job objects are changed on the GUI thread only. Workers report back
    through signals.
    """

    job_added = Signal(object)
    job_updated = Signal(object)  # emitted when the status changes
    job_finished = Signal(object)  # done, failed or cancelled
    job_removed = Signal(int)

    def __init__(self, pool=None, parent=None):
        super().__init__(parent)
        self.pool = pool if pool is not None else QThreadPool.globalInstance()
        if self.pool.maxThreadCount() < MAX_PARALLEL_JOBS:
            self.pool.setMaxThreadCount(MAX_PARALLEL_JOBS)

        self.jobs = {}  # id -> Job, in submit order
        self._ids = count(1)
        self._pending = {}  # id -> (make_bot, run) for jobs not handed to the pool yet
        self._on_result = {}
        self._workers = {}  # id -> JobWorker, until its thread really ends

        # a 1-second ticker instead of one QTimer per job: QTimer can't wait more
        # than ~24 days, and wall-clock run_at survives the computer sleeping
        self._ticker = QTimer(self)
        self._ticker.setInterval(1000)
        self._ticker.timeout.connect(self._start_due_jobs)
        self._ticker.start()

    # ---------- Public API ----------

    def submit(self, kind, account, description, make_bot, run, delay_seconds=0, on_result=None):
        job = Job(next(self._ids), kind, account, description, SCHEDULED if delay_seconds > 0 else QUEUED)
        if delay_seconds > 0:
            job.run_at = datetime.now() + timedelta(seconds=delay_seconds)
        self.jobs[job.id] = job
        self._pending[job.id] = (make_bot, run)
        if on_result is not None:
            self._on_result[job.id] = on_result
        self.job_added.emit(job)
        if job.status == QUEUED:
            self._start(job)
        return job

    def cancel(self, job_id):
        """Cancel a job that hasn't started yet. Returns False if it can't be cancelled."""
        job = self.jobs.get(job_id)
        if job is None:
            return False
        if job.status == SCHEDULED:
            self._pending.pop(job_id, None)
        elif job.status == QUEUED:
            worker = self._workers.get(job_id)
            if worker is None or not self.pool.tryTake(worker):
                return self.stop(job_id)  # it started in the meantime
            self._workers.pop(job_id, None)
        else:
            return False
        self._on_result.pop(job_id, None)
        self._finish(job, CANCELLED)
        return True

    def stop(self, job_id, wait=False):
        """Stop a running job by closing its Chrome window."""
        job = self.jobs.get(job_id)
        if job is None or job.status not in (QUEUED, RUNNING):
            return False
        worker = self._workers.get(job_id)
        if worker is not None:
            worker.request_stop(wait=wait)
        self._on_result.pop(job_id, None)
        self._finish(job, CANCELLED, error="Stopped by user")
        return True

    def shutdown(self):
        """Cancel scheduled jobs and stop running ones (used when the app quits)."""
        self._ticker.stop()
        for job in list(self.jobs.values()):
            if job.status in (SCHEDULED, QUEUED):
                self.cancel(job.id)
            if job.status == RUNNING:
                self.stop(job.id, wait=True)

    def clear_finished(self):
        for job in [job for job in self.jobs.values() if not job.is_active]:
            del self.jobs[job.id]
            self.job_removed.emit(job.id)

    def get(self, job_id):
        return self.jobs.get(job_id)

    def running_count(self):
        return sum(1 for job in self.jobs.values() if job.status == RUNNING)

    def scheduled_count(self):
        return sum(1 for job in self.jobs.values() if job.status in (SCHEDULED, QUEUED))

    def active_count(self):
        return sum(1 for job in self.jobs.values() if job.is_active)

    def has_live_threads(self):
        """True while any worker thread is still inside a bot, even a stopped one."""
        return bool(self._workers)

    # ---------- Internals ----------

    def _start_due_jobs(self):
        now = datetime.now()
        for job in list(self.jobs.values()):
            if job.status == SCHEDULED and job.run_at <= now:
                self._set_status(job, QUEUED)
                self._start(job)

    def _start(self, job):
        make_bot, run = self._pending.pop(job.id)
        worker = JobWorker(job.id, make_bot, run)
        worker.signals.started.connect(self._on_worker_started)
        worker.signals.finished.connect(self._on_worker_finished)
        worker.signals.failed.connect(self._on_worker_failed)
        self._workers[job.id] = worker
        self.pool.start(worker)

    def _on_worker_started(self, job_id):
        job = self.jobs.get(job_id)
        if job is None or job.status != QUEUED:
            return  # cancelled while waiting for a thread
        job.started_at = datetime.now()
        self._set_status(job, RUNNING)

    def _on_worker_finished(self, job_id, result):
        self._workers.pop(job_id, None)
        job = self.jobs.get(job_id)
        if job is None or job.status != RUNNING:
            return  # stopped by the user: keep "cancelled", drop the result
        callback = self._on_result.pop(job_id, None)
        if callback is not None:
            try:
                callback(result)
            except Exception:
                traceback.print_exc()
        self._finish(job, DONE)

    def _on_worker_failed(self, job_id, error):
        self._workers.pop(job_id, None)
        self._on_result.pop(job_id, None)
        job = self.jobs.get(job_id)
        if job is None or job.status != RUNNING:
            return
        self._finish(job, FAILED, error=error)

    def _finish(self, job, status, error=None):
        job.finished_at = datetime.now()
        job.error = error
        self._set_status(job, status)
        self.job_finished.emit(job)

    def _set_status(self, job, status):
        job.status = status
        self.job_updated.emit(job)
