from collections import deque
from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFontDatabase, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QVBoxLayout, QWidget)

from ui.core.jobs import job_id_from_thread_name
from ui.theme.palette import color

MAX_LINES = 5000

INFO = "info"
ERROR = "error"  # written to stderr (tracebacks, warnings)
BLOCK = "block"  # mentions a block: the account may be restricted

APP_JOB_ID = 0


def _format(token):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color(token)))
    return fmt


class LogPanel(QWidget):
    """Live view of everything the bots print, tagged by job."""

    block_detected = Signal(int, str)  # job id, line

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = deque(maxlen=MAX_LINES)  # (time, job id, text, level)
        self._partial = {}  # (thread name, is stderr) -> text after the last newline

        self._formats = {
            "time": _format("muted"),
            "tag": _format("accent"),
            INFO: _format("text"),
            ERROR: _format("warning"),
            BLOCK: _format("danger"),
        }

        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(220)
        self.filter_combo.addItem("All jobs", None)
        self.filter_combo.addItem("App (not from a job)", APP_JOB_ID)
        self.filter_combo.currentIndexChanged.connect(self._render_all)

        self.autoscroll_check = QCheckBox("Auto-scroll")
        self.autoscroll_check.setChecked(True)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear)
        copy_button = QPushButton("Copy")
        copy_button.setToolTip("Copy the visible lines")
        copy_button.clicked.connect(self.copy)

        show_label = QLabel("Show")
        show_label.setProperty("muted", True)
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.addWidget(show_label)
        toolbar.addWidget(self.filter_combo)
        toolbar.addStretch(1)
        toolbar.addWidget(self.autoscroll_check)
        toolbar.addWidget(clear_button)
        toolbar.addWidget(copy_button)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.view.setMaximumBlockCount(MAX_LINES)
        self.view.setPlaceholderText("Bot output will appear here.")
        self.view.setLineWrapMode(QPlainTextEdit.NoWrap)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addLayout(toolbar)
        layout.addWidget(self.view, 1)

    # ---------- Jobs in the filter ----------

    def add_job(self, job):
        self.filter_combo.addItem(job.label, job.id)

    def remove_job(self, job_id):
        index = self.filter_combo.findData(job_id)
        if index > 1:
            self.filter_combo.removeItem(index)

    def filter_to_job(self, job_id):
        index = self.filter_combo.findData(job_id)
        if index >= 0:
            self.filter_combo.setCurrentIndex(index)

    # ---------- Writing ----------

    def write(self, text, thread_name, is_error):
        """Slot for LogBridge.text_written. Text arrives in pieces; split it into lines."""
        key = (thread_name, is_error)
        lines = (self._partial.pop(key, "") + text).split("\n")
        if lines[-1]:
            self._partial[key] = lines[-1]
        job_id = job_id_from_thread_name(thread_name)
        for line in lines[:-1]:
            line = line.rstrip("\r")
            if line.strip():
                self.add_line(line, job_id, is_error)

    def add_line(self, text, job_id=APP_JOB_ID, is_error=False):
        if "block" in text.lower():
            level = BLOCK
        elif is_error:
            level = ERROR
        else:
            level = INFO
        entry = (datetime.now(), job_id, text, level)
        self._entries.append(entry)
        if self._matches(entry):
            self._append(entry)
        if level == BLOCK:
            self.block_detected.emit(job_id, text)

    def lines(self):
        """The visible lines, as plain text (used by tests and Copy)."""
        return self.view.toPlainText().splitlines()

    def clear(self):
        self._entries.clear()
        self._partial.clear()
        self.view.clear()

    def copy(self):
        QApplication.clipboard().setText(self.view.toPlainText())

    # ---------- Rendering ----------

    def _matches(self, entry):
        wanted = self.filter_combo.currentData()
        return wanted is None or entry[1] == wanted

    def _append(self, entry):
        when, job_id, text, level = entry
        scrollbar = self.view.verticalScrollBar()
        position = scrollbar.value()

        cursor = QTextCursor(self.view.document())
        cursor.movePosition(QTextCursor.End)
        if not self.view.document().isEmpty():
            cursor.insertBlock()
        tag = "#{}".format(job_id) if job_id else "app"
        cursor.insertText(when.strftime("%H:%M:%S") + " ", self._formats["time"])
        cursor.insertText(tag.ljust(5), self._formats["tag"])
        cursor.insertText(text, self._formats[level])

        if self.autoscroll_check.isChecked():
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(position)

    def _render_all(self):
        self.view.clear()
        for entry in self._entries:
            if self._matches(entry):
                self._append(entry)
