"""
Audio loader cho TranscriberTab.
Hỗ trợ: MP3, WAV, FLAC, M4A, OGG
Output: numpy array mono 44100Hz (TransKun yêu cầu)
"""
import numpy as np
from pathlib import Path

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

SAMPLE_RATE = 44100  # TransKun hard-require 44100Hz


def load_audio(path: str, target_sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """
    Load audio file và resample về target_sr (mặc định 44100Hz), mono.
    Trả về: (audio_array: np.ndarray, sample_rate: int)
    """
    ext = Path(path).suffix.lower()
    supported = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma'}
    if ext not in supported:
        raise ValueError(f"Định dạng không hỗ trợ: {ext}. Hỗ trợ: {supported}")

    if not HAS_LIBROSA:
        raise ImportError("librosa chưa được cài. Chạy: pip install librosa soundfile")

    # librosa.load tự động resample về target_sr và convert sang mono
    audio, sr = librosa.load(path, sr=target_sr, mono=True)
    return audio, sr
