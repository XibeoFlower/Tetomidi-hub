"""
In-app audio preview for the Edit MIDI tab.

Renders the current notes with core.synth.SimpleSynth into a temp .wav file
and plays it back with Qt's QSoundEffect, so the user can listen to a MIDI
performance directly inside the app — no soundfont, no external player.
"""
import os
import tempfile
from typing import List, Optional

from PyQt6.QtCore import QObject, QUrl, pyqtSignal as Signal

from core.models import Note
from core.synth import SimpleSynth

try:
    from PyQt6.QtMultimedia import QSoundEffect
    AUDIO_PREVIEW_AVAILABLE = True
except Exception:
    QSoundEffect = None
    AUDIO_PREVIEW_AVAILABLE = False


class AudioPreviewPlayer(QObject):
    playback_finished = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tmp_path: Optional[str] = None
        self._effect = None
        if AUDIO_PREVIEW_AVAILABLE:
            self._effect = QSoundEffect(self)
            self._effect.setVolume(0.85)
            self._effect.playingChanged.connect(self._on_playing_changed)

    def play_notes(self, notes: List[Note], bpm: float = 120.0, sample_rate: int = 44100) -> bool:
        if not AUDIO_PREVIEW_AVAILABLE or self._effect is None:
            self.error.emit(
                "QtMultimedia is not available in this Python/Qt environment, "
                "so in-app audio preview can't be played. MIDI export and "
                "Playback-tab testing still work normally."
            )
            return False
        if not notes:
            return False

        self.stop()
        try:
            path = self._render_temp_wav(notes, sample_rate)
        except Exception as e:
            self.error.emit(str(e))
            return False

        self._effect.setSource(QUrl.fromLocalFile(path))
        self._effect.play()
        return True

    def stop(self):
        if self._effect is not None and self._effect.isPlaying():
            self._effect.stop()

    def is_playing(self) -> bool:
        return self._effect.isPlaying() if self._effect is not None else False

    def shutdown(self):
        self.stop()
        self._cleanup_tmp()

    # ── internal ──────────────────────────────────────────────────────

    def _render_temp_wav(self, notes: List[Note], sample_rate: int) -> str:
        self._cleanup_tmp()
        fd, path = tempfile.mkstemp(suffix=".wav", prefix="tetomidi_preview_")
        os.close(fd)
        SimpleSynth(sample_rate=sample_rate).render_to_wav(path, notes)
        self._tmp_path = path
        return path

    def _cleanup_tmp(self):
        if self._tmp_path and os.path.exists(self._tmp_path):
            try:
                os.remove(self._tmp_path)
            except OSError:
                pass
        self._tmp_path = None

    def _on_playing_changed(self):
        if self._effect is not None and not self._effect.isPlaying():
            self.playback_finished.emit()
