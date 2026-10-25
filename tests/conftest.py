import os

# must be set before Qt is imported anywhere
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings

from ui.app import configure_app


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    """A test key for saved passwords, so tests never touch the real system password store."""
    from cryptography.fernet import Fernet

    from utils import crypto

    monkeypatch.setenv(crypto.ENV_KEY, Fernet.generate_key().decode())
    crypto.reset()
    yield
    crypto.reset()


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
    from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool

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
    # deleteLater() only runs from the event loop; delete them now so later tests stay fast
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


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


@pytest.fixture
def confirm_yes(monkeypatch):
    """Answer "yes" to every destructive-action confirmation."""
    asked = []

    def ask(parent, title, text, confirm_text="Delete"):
        asked.append(title)
        return True

    monkeypatch.setattr("ui.widgets.confirm.ask", ask)
    return asked


@pytest.fixture
def themed(qapp, workdir):
    """The real theme, and a throwaway database, for widget and dialog tests."""
    configure_app(qapp)
    return qapp
