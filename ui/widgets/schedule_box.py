from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

from utils.schedule import ScheduleCalc
from ui.core import validators

_CALC = ScheduleCalc()
UNITS = (("minutes", _CALC.MINUTES), ("hours", _CALC.HOURS), ("days", _CALC.DAYS))


class ScheduleBox(QWidget):
    """"Schedule action" toggle with a delay: N minutes, hours or days.

    delay_seconds() uses ScheduleCalc, the same calculation the old tabs used,
    so schedules behave exactly as before.
    """

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.check = QCheckBox("Schedule for later")
        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 100000)
        self.value_spin.setValue(30)
        self.unit_combo = QComboBox()
        for text, unit in UNITS:
            self.unit_combo.addItem(text, unit)
        self.start_label = QLabel("Start in")
        self.start_label.setProperty("muted", True)
        self.error_label = QLabel()
        self.error_label.setObjectName("FieldError")
        self.error_label.hide()

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.check)
        row.addSpacing(12)
        row.addWidget(self.start_label)
        row.addWidget(self.value_spin)
        row.addWidget(self.unit_combo)
        row.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(row)
        layout.addWidget(self.error_label)

        self.check.toggled.connect(self._update)
        self.value_spin.valueChanged.connect(self._update)
        self.unit_combo.currentIndexChanged.connect(self._update)
        self._update()

    def is_scheduled(self):
        return self.check.isChecked()

    def unit(self):
        return self.unit_combo.currentData()

    def value(self):
        return self.value_spin.value()

    def set_delay(self, value, unit):
        self.value_spin.setValue(value)
        self.unit_combo.setCurrentIndex(self.unit_combo.findData(unit))

    def delay_seconds(self):
        """0 when not scheduled."""
        if not self.is_scheduled():
            return 0
        amounts = {unit: 0 for _, unit in UNITS}
        amounts[self.unit()] = self.value()
        return _CALC.calc_schedule_time(self.unit(), amounts[_CALC.MINUTES], amounts[_CALC.HOURS],
                                        amounts[_CALC.DAYS])

    def describe(self):
        """e.g. "in 2 hours", for toasts."""
        value = self.value()
        unit = self.unit_combo.currentText()
        return "in {} {}".format(value, unit[:-1] if value == 1 else unit)

    def error(self):
        if self.is_scheduled():
            return validators.positive(self.value(), "The delay")
        return None

    def _update(self):
        scheduled = self.is_scheduled()
        for widget in (self.start_label, self.value_spin, self.unit_combo):
            widget.setEnabled(scheduled)
        error = self.error()
        self.error_label.setText(error or "")
        self.error_label.setVisible(bool(error))
        self.changed.emit()
