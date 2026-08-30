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
        """
        Kiểm tra có thể import transkun.transcribe và có hàm main() không.
        FIX: Bắt lỗi pkg_resources (và các lỗi import liên quan) để không crash app.
        """
        try:
            import transkun.transcribe as tk_module
            return hasattr(tk_module, "main")
        except ModuleNotFoundError as e:
            if "pkg_resources" in str(e):
                print(f"[TransKunEngine] pkg_resources missing — transkun will use CLI mode only. "
                      f"Run: pip install setuptools>=70.0.0")
            return False
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
        if self._has_cli:
            result = self._transcribe_cli(audio_path, output_mid, segment_size, segment_hop)
        elif self._has_module:
            result = self._transcribe_api(audio_path, output_mid, segment_size, segment_hop)
        else:
            raise RuntimeError(
                "TransKun chưa được cài đúng cách. "
                "Chạy: pip install transkun"
            )

        self._post_process_midi(
            output_mid,
            velocity_threshold=velocity_threshold,
            min_duration_ms=min_duration_ms
        )

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
            cmd, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"TransKun CLI failed (exit code {result.returncode}): "
                f"{detail[-1500:] if detail else 'no output captured'}"
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
        """
        FIX: package `transkun` KHÔNG export hàm `transcribe(audioPath=..., outPath=...)`
        — chỉ export `main()` làm entrypoint CLI. Gọi thẳng main() bằng cách giả lập sys.argv.
        """
        import sys
        try:
            from transkun.transcribe import main as tk_main
        except ModuleNotFoundError as e:
            raise RuntimeError(
                f"Cannot import transkun API ({e}). "
                f"If the error mentions 'pkg_resources', run: pip install setuptools>=70.0.0"
            ) from e

        argv_backup = sys.argv
        try:
            sys.argv = [
                "transkun",
                audio_path,
                output_mid,
                "--device", self.device,
                "--segmentSize", str(segment_size),
                "--segmentHopSize", str(segment_hop),
            ]
            tk_main()
        except SystemExit as e:
            if e.code not in (0, None):
                raise RuntimeError(f"TransKun (API) exited with code {e.code}")
        finally:
            sys.argv = argv_backup

        if not os.path.isfile(output_mid):
            raise RuntimeError(
                "TransKun (API) finished but no output MIDI file was produced."
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
        Lọc nhiễu vocal và note sai sau khi TransKun transcribe.
        """
        try:
            import mido
            from collections import defaultdict

            mid = mido.MidiFile(mid_path)
            ticks_per_beat = mid.ticks_per_beat
            tempo = 500000
            tempo_found = False
            for track in mid.tracks:
                if tempo_found:
                    break
                for msg in track:
                    if msg.type == 'set_tempo':
                        tempo = msg.tempo
                        tempo_found = True
                        break

            def ms_to_ticks(ms):
                return int((ms * 1e-3) * ticks_per_beat * 1e6 / tempo)

            min_ticks = ms_to_ticks(min_duration_ms)

            new_tracks = []
            for track in mid.tracks:
                new_track = mido.MidiTrack()
                new_track.append(mido.MetaMessage('track_name', name='TransKun Fixed', time=0))

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
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        events.append({
                            'type': 'off',
                            'note': msg.note,
                            'velocity': 0,
                            'time': abs_time
                        })

                active = {}
                notes = []
                for ev in events:
                    if ev['type'] == 'on':
                        if ev['note'] in active:
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

                notes = [n for n in notes if (n['end'] - n['start']) >= min_ticks]

                note_events = []
                for n in notes:
                    note_events.append(('on', n['start'], n['note'], n['velocity']))
                    note_events.append(('off', n['end'], n['note'], 0))
                note_events.sort(key=lambda x: (x[1], 0 if x[0] == 'off' else 1))

                last_time = 0
                for ev_type, t, note, vel in note_events:
                    delta = t - last_time
                    last_time = t
                    if ev_type == 'on':
                        new_track.append(mido.Message('note_on', note=note, velocity=vel, time=delta))
                    else:
                        new_track.append(mido.Message('note_off', note=note, velocity=0, time=delta))

                new_track.append(mido.MetaMessage('end_of_track', time=1))
                new_tracks.append(new_track)

            mid.tracks = new_tracks
            mid.save(mid_path)
        except Exception as e:
            print(f"[TransKunEngine] Post-process warning: {e}")

    @property
    def available(self) -> bool:
        return self._has_cli or self._has_module
