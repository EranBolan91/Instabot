from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


def repolish(widget):
    """Re-apply the stylesheet after a dynamic property (e.g. "invalid") changed."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class FormField(QWidget):
    """A label, an input and a one-line message under the input.

    The message is the hint, or the error when there is one: a red border on
    the input plus the error text, instead of a popup.
    """

    def __init__(self, label, widget, hint=None, trailing=None, parent=None):
        super().__init__(parent)
        self.widget = widget
        self._hint = hint
        self._error = None

        self.label = QLabel(label)
        self.label.setObjectName("FieldLabel")
        self.label.setBuddy(widget)
        self.message = QLabel(hint or "")
        self.message.setWordWrap(True)
        self.message.setProperty("muted", True)
        self.message.setVisible(bool(hint))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        if label:
            layout.addWidget(self.label)
        if trailing is None:
            layout.addWidget(widget)
        else:
            # e.g. an "Add" button, lined up with the input rather than the label
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(widget, 1)
            row.addWidget(trailing)
            layout.addLayout(row)
        layout.addWidget(self.message)

    def error(self):
        """The error shown right now, or None."""
        return self._error

    def set_error(self, error):
        self._error = error or None
        self.widget.setProperty("invalid", bool(error))
        repolish(self.widget)
        if error:
            self.message.setObjectName("FieldError")
            self.message.setText(error)
            self.message.show()
        else:
            self.message.setObjectName("")
            self.message.setText(self._hint or "")
            self.message.setVisible(bool(self._hint))
        repolish(self.message)


class FormValidator(QObject):
    """Runs a form's checks on every edit and enables its primary button only when all pass.

    A field shows its error only after the user edited it (or after
    touch_all()), so an empty form doesn't start out red. The button is
    disabled either way.
    """

    validity_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []  # (field, check)
        self._touched = set()
        self._valid = None

    def add(self, field, check, *signals):
        """``check()`` returns an error or None; ``signals`` mean the field was edited."""
        self._rules.append((field, check))
        for signal in signals:
            signal.connect(lambda *_, field=field: self._edited(field))
        return field

    def add_check(self, check, *signals):
        """A check whose widget shows its own error (e.g. ScheduleBox), or none at all."""
        self._rules.append((None, check))
        self.watch(*signals)

    def watch(self, *signals):
        """Other changes that can change a check's result (e.g. a checkbox)."""
        for signal in signals:
            signal.connect(lambda *_: self.revalidate())

    def bind(self, button):
        self.validity_changed.connect(button.setEnabled)
        button.setEnabled(self.revalidate())

    def revalidate(self):
        valid = True
        for field, check in self._rules:
            error = check()
            if error:
                valid = False
            if field is not None:
                field.set_error(error if field in self._touched else None)
        if valid != self._valid:
            self._valid = valid
            self.validity_changed.emit(valid)
        return valid

    def is_valid(self):
        return self.revalidate()

    def touch_all(self):
        self._touched = {field for field, _ in self._rules if field is not None}
        return self.revalidate()

    def reset(self):
        self._touched.clear()
        return self.revalidate()

    def _edited(self, field):
        self._touched.add(field)
        self.revalidate()
