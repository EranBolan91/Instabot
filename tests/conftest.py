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
    from PySide6.QtCore import QThreadPool

    from ui.main_window import MainWindow

    configure_app(qapp)
    windows = []

    def make(**kwargs):
        window = MainWindow(settings=settings, **kwargs)
        window.show()
        windows.append(window)
        return window

    yield make

    # Close the windows here rather than with qtbot.addWidget: pytest-qt closes
    # them before fixture cleanup, and a window with active jobs would open its
    # "Quit anyway?" dialog and wait for a click forever.
    for window in windows:
        window.jobs.shutdown()
        window.close()
        window.deleteLater()
    QThreadPool.globalInstance().waitForDone(5000)


@pytest.fixture
def log_bridge(qapp):
    """Routes print() into the Log panel, like the real app does.

    Call ``log_bridge.install()`` inside the test body: pytest replaces
    sys.stdout with its own capture when the body starts, which would drop a
    bridge installed here.
    """
    from ui.core.log_bridge import LogBridge

    bridge = LogBridge()
    yield bridge
    bridge.uninstall()
