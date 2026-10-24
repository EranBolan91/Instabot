import sys
import threading

from PySide6.QtCore import QObject, Signal


class LogBridge(QObject):
    """Copies everything printed to stdout/stderr into a Qt signal.

    The bots report progress with print(). The original streams still get
    the text, so the console keeps working. Emitting from a worker thread is
    safe: Qt queues the signal to the GUI thread.
    """

    text_written = Signal(str, str, bool)  # text, thread name, is stderr

    def __init__(self, parent=None):
        super().__init__(parent)
        self._originals = None
        self._tees = None

    def install(self):
        if self._originals is not None:
            return
        self._originals = (sys.stdout, sys.stderr)
        self._tees = (_TeeStream(sys.stdout, self, False), _TeeStream(sys.stderr, self, True))
        sys.stdout, sys.stderr = self._tees

    def uninstall(self):
        if self._originals is None:
            return
        # only put the old streams back if nobody replaced ours in the meantime
        if sys.stdout is self._tees[0]:
            sys.stdout = self._originals[0]
        if sys.stderr is self._tees[1]:
            sys.stderr = self._originals[1]
        self._originals = None
        self._tees = None


class _TeeStream:
    def __init__(self, original, bridge, is_error):
        self._original = original
        self._bridge = bridge
        self._is_error = is_error

    def write(self, text):
        if self._original is not None:
            self._original.write(text)
        if text:
            try:
                self._bridge.text_written.emit(text, threading.current_thread().name, self._is_error)
            except RuntimeError:
                pass  # the bridge was deleted while the app shuts down
        return len(text)

    def flush(self):
        if self._original is not None:
            self._original.flush()

    def __getattr__(self, name):
        return getattr(self._original, name)
