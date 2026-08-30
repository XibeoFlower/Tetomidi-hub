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
    cite🛠web_search:4#0:~:text=Transkun V2...Maestro V3
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
                   segment_hop: float = 10.0) -> dict:
        """
        Chuyển audio -> MIDI dùng TransKun v2.

        Args:
            audio_path: Đường dẫn file audio đầu vào
            output_mid: Đường dẫn file .mid đầu ra
            segment_size: Kích thước segment (giây), mặc định 20s
            segment_hop: Bước nhảy segment (giây), mặc định 10s

        Returns:
            dict: {"engine": "TransKun v2", "device": ..., "output": ..., "notes_estimated": int}
        """
        # Ưu tiên CLI vì ổn định hơn
        if self._has_cli:
            return self._transcribe_cli(audio_path, output_mid, segment_size, segment_hop)

        if self._has_module:
            return self._transcribe_api(audio_path, output_mid, segment_size, segment_hop)

        raise RuntimeError(
            "TransKun chưa được cài đúng cách. "
            "Chạy: pip install transkun"
        )

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
        # Đếm số note trong output MIDI
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

    @property
    def available(self) -> bool:
        return self._has_cli or self._has_module
