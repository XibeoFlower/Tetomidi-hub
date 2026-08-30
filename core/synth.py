"""
A tiny, dependency-free additive synthesizer.

It exists purely so a user can *hear* what the notes in the Edit MIDI tab
sound like — and export that as a quick test .wav — without needing a
soundfont, fluidsynth, or any extra audio library. It is not meant to sound
like a real piano; it's a sanity-check preview, not a mixdown.
"""
import wave
from typing import List

import numpy as np

from core.models import Note


class SimpleSynth:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    @staticmethod
    def _freq_for_pitch(pitch: int) -> float:
        return 440.0 * (2.0 ** ((pitch - 69) / 12.0))

    def _render_note(self, pitch: int, velocity: int, duration: float) -> np.ndarray:
        sr = self.sample_rate
        freq = self._freq_for_pitch(pitch)
        release = 0.22
        total = max(0.05, duration) + release
        n = max(1, int(total * sr))
        t = np.arange(n) / sr

        # A few decaying harmonics read as a plucked/piano-ish tone instead
        # of a flat sine, while staying cheap to compute.
        harmonics = ((1.0, 1.0), (2.0, 0.5), (3.0, 0.25), (4.0, 0.12), (5.0, 0.06))
        signal = np.zeros(n, dtype=np.float64)
        for mult, amp in harmonics:
            signal += amp * np.sin(2.0 * np.pi * freq * mult * t)

        # Fast attack, exponential decay across the note, linear fade over
        # the release tail so cut-off notes never click.
        attack_n = max(1, int(0.004 * sr))
        env = np.empty(n, dtype=np.float64)
        env[:attack_n] = np.linspace(0.0, 1.0, attack_n)
        env[attack_n:] = 1.0
        env *= np.exp(-3.0 * t / total)
        release_n = min(n, int(release * sr))
        if release_n > 0:
            env[-release_n:] *= np.linspace(1.0, 0.0, release_n)

        velocity_gain = max(1, min(127, velocity)) / 127.0
        return signal * env * velocity_gain

    def render_notes(self, notes: List[Note], target_peak: float = 0.9) -> np.ndarray:
        if not notes:
            return np.zeros(int(0.5 * self.sample_rate), dtype=np.float64)

        end = max(n.end_time for n in notes) + 0.4
        total_samples = max(1, int(end * self.sample_rate))
        mix = np.zeros(total_samples, dtype=np.float64)

        for note in notes:
            if note.duration <= 0:
                continue
            snippet = self._render_note(note.pitch, note.velocity, note.duration)
            start_i = max(0, int(note.start_time * self.sample_rate))
            end_i = min(total_samples, start_i + len(snippet))
            if end_i <= start_i:
                continue
            mix[start_i:end_i] += snippet[: end_i - start_i]

        peak = float(np.max(np.abs(mix))) if mix.size else 0.0
        if peak > 1e-6:
            mix *= target_peak / peak
        return np.clip(mix, -1.0, 1.0)

    def render_to_wav(self, filepath: str, notes: List[Note], stereo: bool = True) -> None:
        mix = self.render_notes(notes)
        pcm16 = (mix * 32767.0).astype(np.int16)
        channels = 2 if stereo else 1
        if stereo:
            pcm16 = np.repeat(pcm16, 2)
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm16.tobytes())
