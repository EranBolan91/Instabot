from PySide6.QtWidgets import QMessageBox


def ask(parent, title, text, confirm_text="Delete"):
    """Confirmation for destructive actions. Cancel is the default button.

    Call it as ``confirm.ask(...)`` (not ``from ... import ask``), so tests
    can replace it.
    """
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(text)
    confirm_button = box.addButton(confirm_text, QMessageBox.DestructiveRole)
    confirm_button.setProperty("variant", "danger")
    cancel_button = box.addButton("Cancel", QMessageBox.RejectRole)
    box.setDefaultButton(cancel_button)
    box.exec()
    return box.clickedButton() is confirm_button
