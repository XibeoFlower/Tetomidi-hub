"""
Spectral Onset Parser — zero dependency (không cần torch/transkun).
Dùng numpy + scipy để phát hiện onset và ước lượng pitch.
Phù hợp khi:
- User không cài được torch (máy yếu, không có GPU)
- Audio không phải piano solo (TransKun yếu với non-piano)
"""
import numpy as np
import scipy.signal
from scipy.fft import rfft, rfftfreq
import mido
from pathlib import Path


class SpectralOnsetEngine:
    """
    Zero-dependency spectral onset + pitch estimation.
    Không cần torch, không cần transkun. Chỉ cần numpy + scipy + mido.
    """

    def __init__(self,
                 sr: int = 44100,
                 hop_length: int = 512,
                 n_fft: int = 2048,
                 onset_threshold: float = 0.35,
                 min_note_duration: float = 0.05,
                 max_note_duration: float = 2.0):
        self.sr = sr
        self.hop_length = hop_length
        self.n_fft = n_fft
        self.onset_threshold = onset_threshold
        self.min_note_duration = min_note_duration
        self.max_note_duration = max_note_duration

        # Piano range: A0 (21) -> C8 (108)
        self.min_midi = 21
        self.max_midi = 108

    def transcribe(self, audio: np.ndarray, output_mid: str) -> dict:
        """
        audio: numpy array 1D, đã ở 44100Hz mono
        output_mid: đường dẫn file .mid đầu ra
        """
        # 1. Tính spectral flux
        flux, times = self._spectral_flux(audio)

        # 2. Detect onsets
        onsets = self._detect_onsets(flux, times)

        # 3. Ước lượng pitch và duration cho mỗi onset
        notes = self._extract_notes(audio, onsets)

        # 4. Ghi MIDI
        self._write_midi(notes, output_mid)

        return {
            "engine": "Spectral Onset",
            "notes_detected": len(notes),
            "output": output_mid,
        }

    def _spectral_flux(self, audio: np.ndarray):
        """Tính spectral flux — đo thay đổi năng lượng theo thời gian."""
        f, t, Zxx = scipy.signal.stft(
            audio,
            fs=self.sr,
            nperseg=self.n_fft,
            noverlap=self.n_fft - self.hop_length,
            boundary='zeros'
        )
        magnitude = np.abs(Zxx)

        # Positive difference only
        diff = np.diff(magnitude, axis=1)
        flux = np.maximum(diff, 0).sum(axis=0)

        # Normalize về [0, 1]
        if flux.max() > 0:
            flux = (flux - flux.min()) / (flux.max() - flux.min() + 1e-8)

        return flux, t[1:]  # t[1:] vì diff mất 1 frame đầu

    def _detect_onsets(self, flux: np.ndarray, times: np.ndarray):
        """Peak picking trên spectral flux."""
        # Smooth
        window = max(3, int(0.02 * self.sr / self.hop_length))
        if window % 2 == 0:
            window += 1
        smoothed = scipy.signal.savgol_filter(flux, window, 2)

        # Tìm local maxima
        min_distance = int(self.min_note_duration * self.sr / self.hop_length)
        peaks, properties = scipy.signal.find_peaks(
            smoothed,
            height=self.onset_threshold,
            distance=max(min_distance, 3),
            prominence=0.05
        )
        return times[peaks]

    def _extract_notes(self, audio: np.ndarray, onsets: np.ndarray):
        """Ước lượng pitch và duration cho mỗi onset."""
        notes = []
        for i, onset_time in enumerate(onsets):
            start_sample = int(onset_time * self.sr)

            # Frame để estimate pitch: 100ms sau onset
            end_sample = min(start_sample + int(0.1 * self.sr), len(audio))
            frame = audio[start_sample:end_sample]
            if len(frame) < 512:
                continue

            pitch = self._estimate_pitch(frame)
            if pitch is None:
                continue

            # Duration: đến onset tiếp theo hoặc max duration
            if i + 1 < len(onsets):
                duration = min(onsets[i + 1] - onset_time, self.max_note_duration)
            else:
                duration = self.max_note_duration

            duration = max(duration, self.min_note_duration)
            notes.append((onset_time, duration, pitch))

        return notes

    def _estimate_pitch(self, frame: np.ndarray):
        """Harmonic Product Spectrum (HPS) để tìm f0."""
        # Zero-pad để có độ phân giải tần số tốt hơn
        n = len(frame)
        padded = np.zeros(n * 4)
        padded[:n] = frame

        spectrum = np.abs(rfft(padded))
        freqs = rfftfreq(len(padded), 1.0 / self.sr)

        # Chỉ xét range piano: 27.5Hz (A0) -> 4186Hz (C8)
        valid = (freqs >= 27.5) & (freqs <= 4186.0)
        spectrum = spectrum[valid]
        freqs = freqs[valid]

        if len(spectrum) == 0 or spectrum.max() < 1e-6:
            return None

        # HPS: nhân spectrum với bản thân decimated
        hps = spectrum.copy()
        for h in range(2, 5):
            decimated = spectrum[::h]
            hps[:len(decimated)] *= decimated

        # Tìm peak
        peak_idx = np.argmax(hps)
        f0 = freqs[peak_idx]

        # Convert to MIDI note number
        midi_note = int(round(69 + 12 * np.log2(f0 / 440.0)))

        if self.min_midi <= midi_note <= self.max_midi:
            return midi_note
        return None

    def _write_midi(self, notes: list, output_path: str):
        """Ghi notes ra file MIDI dùng mido."""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set tempo: 120 BPM = 500000 microseconds/beat
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))

        ticks_per_beat = mid.ticks_per_beat
        # 120 BPM -> 1 beat = 0.5s -> ticks_per_second = ticks_per_beat * 2
        ticks_per_second = ticks_per_beat * 2

        last_time = 0.0
        for onset, duration, pitch in sorted(notes, key=lambda x: x[0]):
            delta_tick = int((onset - last_time) * ticks_per_second)
            delta_tick = max(delta_tick, 0)

            # Note on
            track.append(mido.Message(
                'note_on',
                note=pitch,
                velocity=min(100, max(40, 80)),  # Fixed velocity
                time=delta_tick
            ))

            # Note off
            dur_tick = int(duration * ticks_per_second)
            track.append(mido.Message(
                'note_off',
                note=pitch,
                velocity=0,
                time=dur_tick
            ))

            last_time = onset + duration

        mid.save(output_path)
