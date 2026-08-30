from PyQt6.QtCore import QObject, pyqtSignal as Signal
from pynput import keyboard
from pynput.keyboard import Key

class HotkeyManager(QObject):
    toggle_requested = Signal()
    bound_updated = Signal(str)
    listener_unavailable = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_key = Key.f6
        self.listener = None
        self.listening_for_bind = False
        self.available = True
        self._start_listener()

    def _start_listener(self):
        try:
            self.listener = keyboard.Listener(on_press=self.on_press)
            self.listener.start()
        except Exception as e:
            # On Linux this typically means no X11/XWayland display is available,
            # or the 'libxtst6' system package is missing. Degrade gracefully
            # instead of crashing the whole app on startup — global hotkeys
            # just won't work, but the rest of the app (loading files, the
            # Play/Stop buttons, Translator, etc.) still functions normally.
            self.listener = None
            self.available = False
            self.listener_unavailable.emit(
                f"Global hotkey listener unavailable ({e.__class__.__name__}: {e}). "
                "The F6-style hotkey won't work, but you can still use the on-screen "
                "Play/Stop buttons. On Linux, try: sudo apt-get install libxtst6 libx11-6"
            )

    def _format_key_string(self, key):
        if hasattr(key, 'char') and key.char:
            return key.char
        return str(key).replace('Key.', '')

    def on_press(self, key):
        if self.listening_for_bind:
            self.current_key = key
            self.listening_for_bind = False
            self.bound_updated.emit(self._format_key_string(key))
            return

        if key == self.current_key:
            self.toggle_requested.emit()

    def start_binding(self):
        if not self.available:
            self.listener_unavailable.emit(
                "Cannot rebind hotkey — no keyboard listener is available on this system."
            )
            return
        self.listening_for_bind = True
