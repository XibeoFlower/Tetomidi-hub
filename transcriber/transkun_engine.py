"""
TransKun v2 Neural Acoustic Model wrapper.
Có thể gọi qua CLI (subprocess) hoặc Python API trực tiếp.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

class TransKunEngine:
    """
    Wrapper cho TransKun v2 — SOTA piano transcription (F1 ~0.953 trên MAESTRO V3)
    """

    def __init__(self, device: str = "auto"):
        self.device = self._resolve_device(device)
        self._has_cli = shutil.which("transkun") is not None
        self._has_module = self._check_module_import()

    def _resolve_device(self, device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _check_module_import(self) -> bool:
        """Kiểm tra có thể import transkun.trascribe không."""
        try:
            import transkun.transcribe  # noqa: F401
            return True
        except ImportError:
            return False

    def transcribe(self, audio_path: str, output_mid: str,
                   segment_size: float = 20.0,
                   segment_hop: float = 10.0,
                   velocity_threshold: int = 25,
                   min_duration_ms: int = 50) -> dict:
        """
        Chuyển audio -> MIDI dùng TransKun v2.

        Args:
            audio_path: Đường dẫn file audio đầu vào
            output_mid: Đường dẫn file .mid đầu ra
            segment_size: Kích thước segment (giây), mặc định 20s
            segment_hop: Bước nhảy segment (giây), mặc định 10s
            velocity_threshold: Lọc note có velocity dưới ngưỡng này (mặc định 25)
                              Giúp loại bỏ nhiễu từ vocal/background
            min_duration_ms: Note ngắn hơn ngưỡng này sẽ bị xóa (mặc định 50ms)

        Returns:
            dict: {"engine": "TransKun v2", "device": ..., "output": ..., "notes_estimated": int}
        """
        # Ưu tiên CLI vì ổn định hơn
        if self._has_cli:
            result = self._transcribe_cli(audio_path, output_mid, segment_size, segment_hop)
        elif self._has_module:
            result = self._transcribe_api(audio_path, output_mid, segment_size, segment_hop)
        else:
            raise RuntimeError(
                "TransKun chưa được cài đúng cách. "
                "Chạy: pip install transkun"
            )

        # === FIX: Post-process để lọc nhiễu vocal và note sai ===
        self._post_process_midi(
            output_mid,
            velocity_threshold=velocity_threshold,
            min_duration_ms=min_duration_ms
        )

        # Cập nhật số note sau khi lọc
        result["notes_estimated"] = self._count_midi_notes(output_mid)
        return result

    def _transcribe_cli(self, audio_path: str, output_mid: str,
                        segment_size: float, segment_hop: float) -> dict:
        cmd = [
            "transkun",
            audio_path,
            output_mid,
            "--device", self.device,
            "--segmentSize", str(segment_size),
            "--segmentHopSize", str(segment_hop),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        note_count = self._count_midi_notes(output_mid)
        return {
            "engine": "TransKun v2 (CLI)",
            "device": self.device,
            "output": output_mid,
            "notes_estimated": note_count,
            "stdout": result.stdout,
        }

    def _transcribe_api(self, audio_path: str, output_mid: str,
                        segment_size: float, segment_hop: float) -> dict:
        from transkun.transcribe import transcribe as tk_transcribe

        tk_transcribe(
            audioPath=audio_path,
            outPath=output_mid,
            device=self.device,
            segmentSize=segment_size,
            segmentHopSize=segment_hop,
        )
        note_count = self._count_midi_notes(output_mid)
        return {
            "engine": "TransKun v2 (API)",
            "device": self.device,
            "output": output_mid,
            "notes_estimated": note_count,
        }

    @staticmethod
    def _count_midi_notes(mid_path: str) -> int:
        """Đếm số note_on trong file MIDI output."""
        try:
            import mido
            mid = mido.MidiFile(mid_path)
            count = 0
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        count += 1
            return count
        except Exception:
            return -1

    @staticmethod
    def _post_process_midi(mid_path: str, velocity_threshold: int = 25, min_duration_ms: int = 50):
        """
        FIX #1: Lọc nhiễu vocal và note sai sau khi TransKun transcribe.

        - Xóa note có velocity thấp (thường là nhiễu từ vocal/background)
        - Xóa note quá ngắn (transient noise)
        - Gộp note cùng pitch chồng lấp (vocal run tạo ra nhiều note liền kề)
        """
        try:
            import mido
            from collections import defaultdict

            mid = mido.MidiFile(mid_path)
            ticks_per_beat = mid.ticks_per_beat
            # Giả định tempo mặc định 500000 microseconds/beat (120 BPM)
            tempo = 500000
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'set_tempo':
                        tempo = msg.tempo
                        break

            # Chuyển ms -> ticks
            def ms_to_ticks(ms):
                return int((ms * 1e-3) * ticks_per_beat * 1e6 / tempo)

            min_ticks = ms_to_ticks(min_duration_ms)

            new_tracks = []
            for track in mid.tracks:
                new_track = mido.MidiTrack()
                new_track.append(mido.MetaMessage('track_name', name='TransKun Fixed', time=0))

                # Tách note_on/note_off và lọc
                events = []
                abs_time = 0
                for msg in track:
                    abs_time += msg.time
                    if msg.type == 'note_on' and msg.velocity > 0:
                        if msg.velocity >= velocity_threshold:
                            events.append({
                                'type': 'on',
                                'note': msg.note,
                                'velocity': msg.velocity,
                                'time': abs_time
                            })
                        else:
                            # Bỏ qua note yếu
                            pass
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        events.append({
                            'type': 'off',
                            'note': msg.note,
                            'velocity': 0,
                            'time': abs_time
                        })

                # Ghép cặp note_on/note_off
                active = {}
                notes = []
                for ev in events:
                    if ev['type'] == 'on':
                        if ev['note'] in active:
                            # Note cùng pitch mở lại khi chưa tắt -> tắt note cũ trước
                            old_start = active.pop(ev['note'])
                            notes.append({
                                'note': ev['note'],
                                'velocity': old_start['velocity'],
                                'start': old_start['time'],
                                'end': ev['time']
                            })
                        active[ev['note']] = {
                            'time': ev['time'],
                            'velocity': ev['velocity']
                        }
                    else:
                        if ev['note'] in active:
                            start = active.pop(ev['note'])
                            notes.append({
                                'note': ev['note'],
                                'velocity': start['velocity'],
                                'start': start['time'],
                                'end': ev['time']
                            })

                # Lọc note quá ngắn
                notes = [n for n in notes if (n['end'] - n['start']) >= min_ticks]

                # Sắp xếp theo thứ tự thờigian
                note_events = []
                for n in notes:
                    note_events.append(('on', n['start'], n['note'], n['velocity']))
                    note_events.append(('off', n['end'], n['note'], 0))
                note_events.sort(key=lambda x: (x[1], 0 if x[0] == 'off' else 1))

                # Build lại track với delta time
                last_time = 0
                for ev_type, t, note, vel in note_events:
                    delta = t - last_time
                    last_time = t
                    if ev_type == 'on':
                        new_track.append(mido.Message('note_on', note=note, velocity=vel, time=delta))
                    else:
                        new_track.append(mido.Message('note_off', note=note, velocity=0, time=delta))

                # Thêm end_of_track
                new_track.append(mido.MetaMessage('end_of_track', time=1))
                new_tracks.append(new_track)

            mid.tracks = new_tracks
            mid.save(mid_path)
        except Exception as e:
            print(f"[TransKunEngine] Post-process warning: {e}")

    @property
    def available(self) -> bool:
        return self._has_cli or self._has_module
