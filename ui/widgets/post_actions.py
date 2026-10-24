from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout, QWidget

from ui.widgets.comment_input import CommentInput
from ui.widgets.distribution_picker import DistributionPicker
from ui.widgets.form import FormField


class PostActions(QWidget):
    """LIKE / FOLLOW / COMMENT for each post, as on the old Hash Tag and Location tabs.

    The comments are only editable while COMMENT is on, and the distribution
    list only while FOLLOW is on.
    """

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.like_check = QCheckBox("Like")
        self.follow_check = QCheckBox("Follow the author")
        self.comment_check = QCheckBox("Comment")
        self.comment_input = CommentInput()
        self.distribution = DistributionPicker()

        checks = QWidget()
        checks_layout = QHBoxLayout(checks)
        checks_layout.setContentsMargins(0, 0, 0, 0)
        checks_layout.setSpacing(24)
        for check in (self.like_check, self.follow_check, self.comment_check):
            checks_layout.addWidget(check)
        checks_layout.addStretch(1)
        self.actions_field = FormField("What to do on each post", checks, "Choose one or more.")
        self.comments_field = FormField("Comments", self.comment_input)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.actions_field)
        layout.addWidget(self.distribution)
        layout.addWidget(self.comments_field)

        for check in (self.like_check, self.follow_check, self.comment_check):
            check.toggled.connect(self._update)
        self.comment_input.changed.connect(self.changed.emit)
        self.distribution.changed.connect(self.changed.emit)
        self._update()

    def set_account(self, row):
        self.distribution.set_account(row)

    # the bots take 0/1 ints for each action
    def like(self):
        return int(self.like_check.isChecked())

    def follow(self):
        return int(self.follow_check.isChecked())

    def comment(self):
        return int(self.comment_check.isChecked())

    def split_comment(self):
        """The comment list the bots take, or "" when not commenting (as the old tabs passed)."""
        return self.comment_input.comments() if self.comment() else ""

    def describe(self):
        names = [name for name, on in (("like", self.like()), ("follow", self.follow()), ("comment", self.comment()))
                 if on]
        return "+".join(names)

    def actions_error(self):
        if not (self.like() or self.follow() or self.comment()):
            return "Choose at least one: like, follow or comment"
        return None

    def comments_error(self):
        if self.comment() and not self.comment_input.comments():
            return "Write at least one comment, or turn off Comment"
        return None

    def _update(self):
        self.comment_input.setEnabled(self.comment_check.isChecked())
        self.distribution.set_available(self.follow_check.isChecked())
        self.changed.emit()
