"""
ByteDance Piano Transcription wrapper (piano_transcription_inference).
Model nhẹ hơn TransKun v2 (CRNN, khoảng ~170MB checkpoint tải 1 lần dùng mãi),
tốc độ transcribe nhanh hơn, phù hợp máy yếu / muốn app "nhẹ" hơn.

Nguồn: https://github.com/qiuqiangkong/piano_transcription_inference
API xác nhận từ README chính thức của package (không đoán, tránh lặp lại
bug 'gọi hàm không tồn tại' như từng gặp với TransKun):

    from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
    audio, _ = load_audio(audio_path, sr=sample_rate, mono=True)
    transcriptor = PianoTranscription(device='cuda'|'cpu', checkpoint_path=None)
    transcribed_dict = transcriptor.transcribe(audio, output_midi_path)
"""
import os


class ByteDanceEngine:
    """
    Wrapper cho ByteDance Piano Transcription (High-resolution Piano
    Transcription with Pedals by Regressing Onsets and Offsets Times).
    Nhẹ hơn TransKun v2, khởi động nhanh hơn, dùng ít RAM/VRAM hơn.
    """

    def __init__(self, device: str = "auto"):
        self.device = self._resolve_device(device)
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
        try:
            import piano_transcription_inference  # noqa: F401
            return True
        except ModuleNotFoundError as e:
            if "pkg_resources" in str(e):
                print(f"[ByteDanceEngine] pkg_resources missing. "
                      f"Run: pip install setuptools>=70.0.0")
            return False
        except ImportError:
            return False

    def transcribe(self, audio_path: str, output_mid: str,
                   velocity_threshold: int = 0,
                   min_duration_ms: int = 30) -> dict:
        """
        Chuyển audio -> MIDI dùng ByteDance Piano Transcription.

        Args:
            audio_path: Đường dẫn file audio đầu vào
            output_mid: Đường dẫn file .mid đầu ra
            velocity_threshold: Lọc note velocity thấp hơn ngưỡng (model này
                                 vốn đã lọc onset/offset tốt nên mặc định 0)
            min_duration_ms: Note ngắn hơn ngưỡng này sẽ bị xóa (mặc định 30ms)

        Returns:
            dict: {"engine": "ByteDance Piano Transcription", "device": ...,
                   "output": ..., "notes_estimated": int}
        """
        if not self._has_module:
            raise RuntimeError(
                "ByteDance Piano Transcription chưa được cài. "
                "Chạy: pip install piano_transcription_inference"
            )

        try:
            from piano_transcription_inference import (
                PianoTranscription, sample_rate, load_audio,
            )
        except ModuleNotFoundError as e:
            raise RuntimeError(
                f"Cannot import piano_transcription_inference ({e}). "
                f"If the error mentions 'pkg_resources', run: "
                f"pip install setuptools>=70.0.0"
            ) from e

        os.makedirs(os.path.dirname(os.path.abspath(output_mid)) or ".", exist_ok=True)

        # Lần chạy đầu tiên sẽ tự tải checkpoint (~170MB) về
        # ~/piano_transcription_inference_data/ rồi dùng lại cho các lần sau.
        audio, _ = load_audio(audio_path, sr=sample_rate, mono=True)
        transcriptor = PianoTranscription(device=self.device, checkpoint_path=None)
        transcriptor.transcribe(audio, output_mid)

        if not os.path.isfile(output_mid):
            raise RuntimeError(
                "ByteDance Piano Transcription finished but no output MIDI "
                "file was produced."
            )

        self._post_process_midi(
            output_mid,
            velocity_threshold=velocity_threshold,
            min_duration_ms=min_duration_ms,
        )

        return {
            "engine": "ByteDance Piano Transcription",
            "device": self.device,
            "output": output_mid,
            "notes_estimated": self._count_midi_notes(output_mid),
        }

    @staticmethod
    def _count_midi_notes(mid_path: str) -> int:
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
    def _post_process_midi(mid_path: str, velocity_threshold: int = 0, min_duration_ms: int = 30):
        """Lọc note quá ngắn / quá nhẹ, cùng logic với TransKunEngine để đồng nhất kết quả."""
        try:
            import mido

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
            if min_ticks <= 0 and velocity_threshold <= 0:
                return  # không cần lọc gì cả

            new_tracks = []
            for track in mid.tracks:
                new_track = mido.MidiTrack()
                new_track.append(mido.MetaMessage('track_name', name='ByteDance Piano', time=0))

                events = []
                abs_time = 0
                for msg in track:
                    abs_time += msg.time
                    if msg.type == 'note_on' and msg.velocity > 0:
                        if msg.velocity >= velocity_threshold:
                            events.append({'type': 'on', 'note': msg.note,
                                           'velocity': msg.velocity, 'time': abs_time})
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        events.append({'type': 'off', 'note': msg.note,
                                       'velocity': 0, 'time': abs_time})

                active = {}
                notes = []
                for ev in events:
                    if ev['type'] == 'on':
                        if ev['note'] in active:
                            old_start = active.pop(ev['note'])
                            notes.append({'note': ev['note'], 'velocity': old_start['velocity'],
                                          'start': old_start['time'], 'end': ev['time']})
                        active[ev['note']] = {'time': ev['time'], 'velocity': ev['velocity']}
                    else:
                        if ev['note'] in active:
                            start = active.pop(ev['note'])
                            notes.append({'note': ev['note'], 'velocity': start['velocity'],
                                          'start': start['time'], 'end': ev['time']})

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
            print(f"[ByteDanceEngine] Post-process warning: {e}")

    @property
    def available(self) -> bool:
        return self._has_module
