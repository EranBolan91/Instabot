import os
import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from ui.theme.palette import color, load_stylesheet


def create_app(argv=None):
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    configure_app(app)
    return app


def configure_app(app):
    # re-applying the stylesheet restyles every existing widget, which is slow
    if app.property("instabot_configured"):
        return
    app.setProperty("instabot_configured", True)
    # QSettings() with no arguments uses these names
    app.setOrganizationName("Instabot")
    app.setApplicationName("Instabot")
    app.setStyle("Fusion")

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    app.setPalette(_dark_palette())
    app.setStyleSheet(load_stylesheet("dark"))


# Fusion draws some things (checkbox marks, focus frames, dialogs) from the
# palette rather than the stylesheet, so it has to match the theme too.
def _dark_palette():
    palette = QPalette()
    roles = {
        QPalette.Window: "bg",
        QPalette.WindowText: "text",
        QPalette.Base: "raised",
        QPalette.AlternateBase: "surface",
        QPalette.Text: "text",
        QPalette.Button: "surface",
        QPalette.ButtonText: "text",
        QPalette.ToolTipBase: "raised",
        QPalette.ToolTipText: "text",
        QPalette.PlaceholderText: "muted",
        QPalette.Highlight: "accent",
        QPalette.Link: "accent",
    }
    for role, token in roles.items():
        palette.setColor(role, QColor(color(token)))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, QColor(color("disabled")))
    return palette


def run():
    # imported here so create_app() works without building any widgets
    from ui.core.log_bridge import LogBridge
    from ui.main_window import MainWindow

    app = create_app()
    log_bridge = LogBridge()
    log_bridge.install()
    window = MainWindow(log_bridge=log_bridge)
    window.show_initial()
    code = app.exec()
    log_bridge.uninstall()

    if window.jobs.has_live_threads():
        # A stopped bot can still be inside a long time.sleep(), and Qt's
        # thread pool waits for it on exit, so the app would hang. Its Chrome
        # was already closed by JobManager.shutdown(), so exit right away.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)
    sys.exit(code)
