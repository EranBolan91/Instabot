from datetime import datetime

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
                               QStackedLayout, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTableView,
                               QVBoxLayout, QWidget)

from ui.core.jobs import CANCELLED, DONE, FAILED, QUEUED, RUNNING, SCHEDULED
from ui.theme.palette import color

COLUMNS = ("Status", "Kind", "Account", "Description", "Run at", "Duration", "")
STATUS_COLUMN, ACTIONS_COLUMN = 0, len(COLUMNS) - 1
RUN_AT_COLUMN, DURATION_COLUMN = 4, 5

STATUS_COLORS = {
    SCHEDULED: "warning",
    QUEUED: "muted",
    RUNNING: "accent",
    DONE: "success",
    FAILED: "danger",
    CANCELLED: "muted",
}

NO_TIME = "–"


def format_delta(delta):
    seconds = max(0, int(delta.total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        return "{}d {:02d}h".format(days, hours)
    if hours:
        return "{}h {:02d}m {:02d}s".format(hours, minutes, seconds)
    if minutes:
        return "{}m {:02d}s".format(minutes, seconds)
    return "{}s".format(seconds)


def run_at_text(job, now=None):
    now = now or datetime.now()
    if job.status == SCHEDULED:
        return "in " + format_delta(job.run_at - now)
    if job.started_at:
        return job.started_at.strftime("%H:%M:%S")
    if job.status == QUEUED:
        return "waiting for a thread"
    return job.run_at.strftime("%d/%m %H:%M") if job.run_at else NO_TIME


def duration_text(job, now=None):
    if not job.started_at:
        return NO_TIME
    end = job.finished_at or now or datetime.now()
    return format_delta(end - job.started_at)


class JobsModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._jobs)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        job = self._jobs[index.row()]
        column = index.column()
        if role == Qt.UserRole:
            return job
        if role == Qt.DisplayRole:
            return (job.status.capitalize(), job.kind, "@" + job.account, job.description,
                    run_at_text(job), duration_text(job), "")[column]
        if role == Qt.ToolTipRole:
            if column == STATUS_COLUMN and job.error:
                return job.error
            if column == RUN_AT_COLUMN and job.run_at:
                return job.run_at.strftime("Scheduled for %d/%m/%Y %H:%M:%S")
            if column == 3:
                return job.description
        return None

    def add_job(self, job):
        row = len(self._jobs)
        self.beginInsertRows(QModelIndex(), row, row)
        self._jobs.append(job)
        self.endInsertRows()

    def update_job(self, job):
        row = self.row_of(job.id)
        if row >= 0:
            self.dataChanged.emit(self.index(row, 0), self.index(row, len(COLUMNS) - 1))

    def remove_job(self, job_id):
        row = self.row_of(job_id)
        if row >= 0:
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._jobs[row]
            self.endRemoveRows()

    def refresh_times(self):
        if self._jobs:
            self.dataChanged.emit(self.index(0, RUN_AT_COLUMN), self.index(len(self._jobs) - 1, DURATION_COLUMN))

    def row_of(self, job_id):
        for row, job in enumerate(self._jobs):
            if job.id == job_id:
                return row
        return -1

    def job_at(self, row):
        return self._jobs[row]

    def jobs(self):
        return list(self._jobs)


class StatusChipDelegate(QStyledItemDelegate):
    """Draws the status as a small colored pill."""

    def paint(self, painter, option, index):
        job = index.data(Qt.UserRole)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else None
        if style:
            style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        text = job.status.capitalize()
        chip_color = QColor(color(STATUS_COLORS[job.status]))
        metrics = option.fontMetrics
        height = metrics.height() + 6
        rect = QRectF(option.rect.x() + 8, option.rect.center().y() - height / 2 + 0.5,
                      metrics.horizontalAdvance(text) + 20, height)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        background = QColor(chip_color)
        background.setAlpha(45)
        painter.setPen(Qt.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, height / 2, height / 2)
        painter.setPen(chip_color)
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(option.fontMetrics.horizontalAdvance("Cancelled") + 40, max(size.height(), 32))


class JobsPanel(QWidget):
    """Table of every job, with live countdowns and Cancel / Stop buttons."""

    job_activated = Signal(int)  # double-clicked: show this job's log
    summary_changed = Signal(str)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.model = JobsModel(self)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(STATUS_COLUMN, StatusChipDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(34)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        # sized for its Cancel/Stop button; ResizeToContents only sees the empty text
        header.setSectionResizeMode(ACTIONS_COLUMN, QHeaderView.Fixed)
        header.resizeSection(ACTIONS_COLUMN, 110)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.doubleClicked.connect(lambda index: self.job_activated.emit(self.model.job_at(index.row()).id))

        self.empty_label = QLabel("No jobs yet. Jobs you run or schedule will show up here.")
        self.empty_label.setProperty("muted", True)
        self.empty_label.setAlignment(Qt.AlignCenter)

        self._stack = QStackedLayout()
        self._stack.addWidget(self.empty_label)
        self._stack.addWidget(self.table)

        hint = QLabel("Double-click a job to see its log.")
        hint.setProperty("muted", True)
        self.clear_button = QPushButton("Clear finished")
        self.clear_button.clicked.connect(self.manager.clear_finished)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.addWidget(hint)
        toolbar.addStretch(1)
        toolbar.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addLayout(toolbar)
        layout.addLayout(self._stack, 1)

        # countdowns and durations change every second
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.model.refresh_times)
        self._timer.start()

        manager.job_added.connect(self._on_job_added)
        manager.job_updated.connect(self._on_job_updated)
        manager.job_removed.connect(self._on_job_removed)
        self._update_summary()

    def summary_text(self):
        parts = []
        running = self.manager.running_count()
        waiting = self.manager.scheduled_count()
        if running:
            parts.append("{} running".format(running))
        if waiting:
            parts.append("{} scheduled".format(waiting))
        return "Jobs ({})".format(", ".join(parts)) if parts else "Jobs"

    def action_button(self, job_id):
        """The Cancel/Stop button of a job's row, or None."""
        row = self.model.row_of(job_id)
        holder = self.table.indexWidget(self.model.index(row, ACTIONS_COLUMN)) if row >= 0 else None
        return holder.button if holder is not None else None

    def _on_job_added(self, job):
        self.model.add_job(job)
        self._update_actions(job)
        self._update_summary()

    def _on_job_updated(self, job):
        self.model.update_job(job)
        self._update_actions(job)
        self._update_summary()

    def _on_job_removed(self, job_id):
        self.model.remove_job(job_id)
        # rows below moved up; rebuild their buttons
        for job in self.model.jobs():
            self._update_actions(job)
        self._update_summary()

    def _update_actions(self, job):
        index = self.model.index(self.model.row_of(job.id), ACTIONS_COLUMN)
        old = self.table.indexWidget(index)
        if old is not None:
            # Qt deletes the replaced widget later; hide it now so it never lingers
            old.hide()
        if job.status in (SCHEDULED, QUEUED):
            button = QPushButton("Cancel")
            button.clicked.connect(lambda checked=False, job_id=job.id: self.manager.cancel(job_id))
        elif job.status == RUNNING:
            button = QPushButton("Stop")
            button.setProperty("variant", "danger")
            button.clicked.connect(lambda checked=False, job_id=job.id: self._confirm_stop(job_id))
        else:
            button = None
        if button is not None:
            # wrap it, so the button keeps its own height inside the row
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(6, 2, 6, 2)
            holder_layout.addWidget(button)
            self.table.setIndexWidget(index, holder)
            holder.button = button
        else:
            self.table.setIndexWidget(index, None)

    def _confirm_stop(self, job_id):
        job = self.manager.get(job_id)
        if job is None:
            return
        answer = QMessageBox.question(
            self, "Stop job",
            "Stop job #{} ({}) for @{}?\n\nIts Chrome window is closed right away, so the bot stops "
            "in the middle of its run.".format(job.id, job.kind, job.account))
        if answer == QMessageBox.Yes:
            self.manager.stop(job_id)

    def _update_summary(self):
        has_jobs = self.model.rowCount() > 0
        self._stack.setCurrentWidget(self.table if has_jobs else self.empty_label)
        self.clear_button.setEnabled(any(not job.is_active for job in self.model.jobs()))
        self.summary_changed.emit(self.summary_text())
