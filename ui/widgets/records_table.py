"""Sortable table of DB rows (past runs, statistics), with named column headers."""
from datetime import datetime
from typing import NamedTuple

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QTableView, QVBoxLayout, QWidget)

from ui.core.db_helpers import as_int

TEXT, NUMBER, BOOL, DATE = range(4)
SORT_ROLE = Qt.UserRole + 1
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"  # what models/*.py store


class Column(NamedTuple):
    title: str
    index: int  # position in the DB row tuple
    kind: int = TEXT


def _date_key(value):
    try:
        return datetime.strptime(str(value), DATE_FORMAT)
    except ValueError:
        return datetime.min


class RecordsModel(QAbstractTableModel):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = list(columns)
        self._rows = []

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = list(rows or [])
        self.endResetModel()

    def row_at(self, row):
        return self._rows[row]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section].title
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        column = self.columns[index.column()]
        value = self._rows[index.row()][column.index]
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if column.kind == BOOL:
                return "Yes" if as_int(value) else "No"
            return "" if value is None else str(value)
        if role == SORT_ROLE:
            if column.kind in (NUMBER, BOOL):
                return as_int(value)
            if column.kind == DATE:
                return _date_key(value)
            return "" if value is None else str(value).lower()
        if role == Qt.TextAlignmentRole and column.kind == NUMBER:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None


class RecordsFilter(QSortFilterProxyModel):
    """Text search over every column, plus an optional "only this account" filter."""

    def __init__(self, account_index=None, parent=None):
        super().__init__(parent)
        self.setSortRole(SORT_ROLE)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)
        self._account_index = account_index
        self._account = None

    def set_account(self, username):
        self._account = username
        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        if self._account is not None and self._account_index is not None:
            if self.sourceModel().row_at(source_row)[self._account_index] != self._account:
                return False
        return super().filterAcceptsRow(source_row, source_parent)


class RecordsTable(QWidget):
    def __init__(self, columns, empty_text="Nothing here yet.", account_index=None, searchable=False, parent=None):
        super().__init__(parent)
        self.model = RecordsModel(columns, self)
        self.proxy = RecordsFilter(account_index, self)
        self.proxy.setSourceModel(self.model)
        self._account = None

        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setShowGrid(False)
        self.view.setWordWrap(False)
        self.view.verticalHeader().hide()
        self.view.verticalHeader().setDefaultSectionSize(32)
        header = self.view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        date_columns = [i for i, column in enumerate(self.model.columns) if column.kind == DATE]
        if date_columns:
            # newest first
            self.view.sortByColumn(date_columns[0], Qt.DescendingOrder)

        self.empty_label = QLabel(empty_text)
        self.empty_label.setProperty("muted", True)
        self.empty_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search = None
        self.account_check = None
        if searchable:
            self.search = QLineEdit()
            self.search.setPlaceholderText("Filter")
            self.search.setClearButtonEnabled(True)
            self.search.textChanged.connect(self.proxy.setFilterFixedString)
            self.account_check = QCheckBox("Only the current account")
            self.account_check.toggled.connect(self._apply_account)
            toolbar = QHBoxLayout()
            toolbar.addWidget(self.search, 1)
            toolbar.addWidget(self.account_check)
            layout.addLayout(toolbar)

        layout.addWidget(self.view, 1)
        layout.addWidget(self.empty_label)
        self._update_empty()

    def set_rows(self, rows):
        self.model.set_rows(rows)
        self.view.resizeColumnsToContents()
        self._update_empty()

    def set_account(self, username):
        self._account = username
        self._apply_account()

    def visible_rows(self):
        return self.proxy.rowCount()

    def cell(self, row, column):
        return self.proxy.data(self.proxy.index(row, column))

    def _apply_account(self):
        only_account = self.account_check is not None and self.account_check.isChecked()
        self.proxy.set_account(self._account if only_account else None)
        self._update_empty()

    def _update_empty(self):
        has_rows = self.model.rowCount() > 0
        self.view.setVisible(has_rows)
        self.empty_label.setVisible(not has_rows)
