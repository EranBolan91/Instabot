from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from ui.core.db_helpers import account_id, account_password, account_username
from ui.pages.base_page import BasePage
from ui.widgets.card import Card
from ui.widgets.credentials_box import CredentialsBox
from ui.widgets.form import FormField, FormValidator
from ui.widgets.proxy_box import ProxyBox
from ui.widgets.schedule_box import ScheduleBox

NO_LIMIT = -1  # a count the bots' "== limit" checks never reach


def limit_arg(value):
    """Spin box value -> bot limit argument. 0 is shown as "No limit"."""
    return value if value > 0 else NO_LIMIT


class JobPage(BasePage):
    """A page that runs a bot: account, schedule, proxy and a primary Run button.

    Subclasses build their cards, add their checks to ``self.validator``,
    call ``finish_form()`` and implement ``run_job()``.
    """

    kind = ""  # shown in the Jobs panel
    run_text = "Run"
    uses_proxy = True

    notify = Signal(str, str)  # toast text, kind

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self.validator = FormValidator(self)
        self.credentials = CredentialsBox()
        self.schedule = ScheduleBox()
        self.proxy = ProxyBox() if self.uses_proxy else None

        self.run_button = QPushButton(self.run_text)
        self.run_button.setProperty("variant", "primary")
        self.run_button.clicked.connect(self._on_run_clicked)

        self.validator.add_check(lambda: None if self.account else "Pick an account in the header first")
        self.validator.add_check(self.schedule.error, self.schedule.changed)
        if self.proxy is not None:
            self.validator.add_check(self.proxy.error, self.proxy.changed)
        if jobs is not None:
            jobs.job_finished.connect(self._on_job_finished)

    # ---------- Building ----------

    def account_card(self):
        card = Card("Account")
        card.content.addWidget(FormField("", self.credentials, "Jobs run as this account. Change it in the header."))
        return card

    def run_card(self, extra_widgets=(), with_button=True):
        card = Card("Run")
        for widget in extra_widgets:
            card.content.addWidget(widget)
        card.content.addWidget(self.schedule)
        if self.proxy is not None:
            card.content.addWidget(FormField("Proxy", self.proxy))
        if with_button:
            row = QHBoxLayout()
            row.addStretch(1)
            row.addWidget(self.run_button)
            card.content.addLayout(row)
        return card

    def finish_form(self):
        self.body_layout.addStretch(1)
        self.validator.bind(self.run_button)

    # ---------- Account ----------

    def set_account(self, row):
        super().set_account(row)
        self.credentials.set_account(row)
        self.on_account_changed(row)
        self.validator.revalidate()

    def on_account_changed(self, row):
        """Reload account-dependent data (lists, past runs)."""

    def username(self):
        return account_username(self.account) if self.account else ""

    def account_id(self):
        return account_id(self.account) if self.account else -1

    def login(self):
        """(username, password, proxy_dict), read now so a later edit can't change a queued job."""
        proxy = self.proxy.proxy_dict() if self.proxy is not None else {"proxy": "", "port": ""}
        return account_username(self.account), account_password(self.account), proxy

    # ---------- Running ----------

    def is_schedule(self):
        """The 0/1 the bots store in their statistics."""
        return int(self.schedule.is_scheduled())

    def run_job(self):
        raise NotImplementedError

    def submit(self, description, make_bot, run, on_result=None, kind=None, delay_seconds=None, notify=True):
        """Queue a job. The bot is built by ``make_bot`` on the worker thread, never here."""
        kind = kind or self.kind
        if delay_seconds is None:
            delay_seconds = self.schedule.delay_seconds()
        job = self.jobs.submit(kind, self.username(), description, make_bot, run, delay_seconds=delay_seconds,
                               on_result=on_result)
        if notify:
            if delay_seconds:
                self.notify.emit("{} job for @{} scheduled {}".format(kind, self.username(),
                                                                      self.schedule.describe()), "success")
            else:
                self.notify.emit("{} job started for @{}".format(kind, self.username()), "success")
        return job

    def _on_run_clicked(self):
        if self.validator.touch_all():
            self.run_job()

    def _on_job_finished(self, job):
        if job.account == self.username():
            self.on_account_job_finished(job)

    def on_account_job_finished(self, job):
        """A job of the current account finished: refresh what it may have changed."""
