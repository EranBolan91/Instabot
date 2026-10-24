import os

# must be set before Qt is imported anywhere
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings

from ui.app import configure_app


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Run in an empty folder, so Database() creates a throwaway instabot.db there."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def settings(workdir):
    """QSettings in a temp file, so tests never touch the user's real window state."""
    return QSettings(str(workdir / "settings.ini"), QSettings.IniFormat)


@pytest.fixture
def make_window(qapp, qtbot, settings):
    from ui.main_window import MainWindow

    configure_app(qapp)

    def make():
        window = MainWindow(settings=settings)
        qtbot.addWidget(window)
        window.show()
        return window

    return make
