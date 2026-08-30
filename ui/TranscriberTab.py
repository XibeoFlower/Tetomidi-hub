"""
TranscriberTab — MP3/Audio → MIDI transcription.
"""
import os
import time
import shutil
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QComboBox, QSpinBox, QDoubleSpinBox,
    QProgressBar, QMessageBox, QGroupBox, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.core import MidiParser
from ui.TrackSelectionDialog import TrackSelectionDialog


class TranscriberWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)
    log = pyqtSignal(str)

    def __init__(self, engine_name: str, audio_path: str, output_mid: str,
                 segment_size: float, segment_hop: float, parent=None):
        super().__init__(parent)
        self.engine_name = engine_name
        self.audio_path = audio_path
        self.output_mid = output_mid
        self.segment_size = segment_size
        self.segment_hop = segment_hop
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.log.emit("Initializing transcription engine...")
            self.progress.emit(10)

            if self.engine_name == "TransKun v2":
                from transcriber.transkun_engine import TransKunEngine
                engine = TransKunEngine()
                if not engine.available:
                    raise RuntimeError("TransKun v2 is not installed.")
                self.log.emit("TransKun v2 loaded. Transcribing...")
                self.progress.emit(30)
                result = engine.transcribe(
                    self.audio_path, self.output_mid,
                    segment_size=self.segment_size,
                    segment_hop=self.segment_hop,
                    velocity_threshold=25,   # FIX: Lọc nhiễu vocal
                    min_duration_ms=50       # FIX: Xóa note quá ngắn
                )
                self.log.emit(f"Transcription complete: {result.get('notes_estimated', 0)} notes")
                self.progress.emit(100)
                self.finished.emit(True, self.output_mid)

            elif self.engine_name == "Spectral Onset":
                # FIX #1: class thật sự tên là SpectralOnsetEngine, không phải
                # SpectralEngine -> import sai tên gây ImportError ngay lập tức.
                from transcriber.spectral_engine import SpectralOnsetEngine
                # FIX #2: SpectralOnsetEngine.transcribe() cần numpy array audio
                # đã load sẵn (44100Hz mono), KHÔNG nhận đường dẫn file string.
                # audio_loader.load_audio() có sẵn nhưng chưa từng được gọi.
                from transcriber.audio_loader import load_audio

                self.log.emit("Loading audio file...")
                self.progress.emit(15)
                audio_array, _sr = load_audio(self.audio_path)

                engine = SpectralOnsetEngine()
                self.log.emit("Spectral Onset engine loaded. Transcribing...")
                self.progress.emit(30)
                engine.transcribe(audio_array, self.output_mid)
                self.log.emit("Spectral transcription complete.")
                self.progress.emit(100)
                self.finished.emit(True, self.output_mid)

            else:
                raise RuntimeError(f"Unknown engine: {self.engine_name}")

        except Exception as e:
            self.log.emit(f"Error: {str(e)}")
            self.finished.emit(False, str(e))


class TranscriberTab(QWidget):
    """Tab điều khiển transcription audio → MIDI."""

    load_into_playback = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: TranscriberWorker | None = None
        self._last_mid_path: str | None = None   # FIX: Lưu đường dẫn output
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Engine selection ---
        engine_group = QGroupBox("⚙️ Transcription Engine")
        engine_layout = QHBoxLayout()
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["TransKun v2", "Spectral Onset"])
        self.engine_combo.setToolTip(
            "TransKun v2: Best for piano solo (default).\n"
            "Spectral Onset: Zero-dependency fallback."
        )
        engine_layout.addWidget(QLabel("Engine:"))
        engine_layout.addWidget(self.engine_combo, 1)
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)

        # --- Audio file input ---
        file_group = QGroupBox("🎵 Input Audio File")
        file_layout = QHBoxLayout()
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("Select an audio file (MP3, WAV, FLAC, OGG)...")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_audio)
        file_layout.addWidget(self.audio_path_edit, 1)
        file_layout.addWidget(self.browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # --- Segment settings ---
        seg_group = QGroupBox("📐 Segment Settings")
        seg_grid = QGridLayout()

        seg_grid.addWidget(QLabel("Segment Size (s):"), 0, 0)
        self.seg_size_spin = QDoubleSpinBox()
        self.seg_size_spin.setRange(5.0, 60.0)
        self.seg_size_spin.setValue(30.0)   # FIX: Tăng từ 20 lên 30 để ít lỗi hơn
        self.seg_size_spin.setDecimals(1)
        seg_grid.addWidget(self.seg_size_spin, 0, 1)

        seg_grid.addWidget(QLabel("Hop Size (s):"), 0, 2)
        self.seg_hop_spin = QDoubleSpinBox()
        self.seg_hop_spin.setRange(2.5, 30.0)
        self.seg_hop_spin.setValue(15.0)    # FIX: Tăng từ 10 lên 15
        self.seg_hop_spin.setDecimals(1)
        seg_grid.addWidget(self.seg_hop_spin, 0, 3)

        seg_group.setLayout(seg_grid)
        layout.addWidget(seg_group)

        # --- Output settings ---
        out_group = QGroupBox("💾 Output MIDI")
        out_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Output MIDI path (auto-generated if empty)...")
        self.out_browse_btn = QPushButton("Browse...")
        self.out_browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(self.output_path_edit, 1)
        out_layout.addWidget(self.out_browse_btn)
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

        # --- Controls ---
        ctrl_layout = QHBoxLayout()
        self.transcribe_btn = QPushButton("▶️ Start Transcription")
        self.transcribe_btn.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.transcribe_btn.clicked.connect(self._start_transcription)

        self.cancel_btn = QPushButton("⏹ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_transcription)

        ctrl_layout.addWidget(self.transcribe_btn)
        ctrl_layout.addWidget(self.cancel_btn)
        layout.addLayout(ctrl_layout)

        # --- Progress ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # --- Post-transcription actions (FIX: Thêm nút Select Tracks và Discard) ---
        action_group = QGroupBox("✅ Post-Transcription Actions")
        action_layout = QHBoxLayout()

        self.select_tracks_btn = QPushButton("☑️ Select Tracks to Keep")
        self.select_tracks_btn.setToolTip("Chọn/bỏ chọn track trước khi load vào Playback")
        self.select_tracks_btn.setVisible(False)
        self.select_tracks_btn.clicked.connect(self._on_select_tracks_clicked)

        self.load_playback_btn = QPushButton("🎹 Load into Playback Tab")
        self.load_playback_btn.setVisible(False)
        self.load_playback_btn.clicked.connect(self._on_load_playback)

        self.discard_btn = QPushButton("🗑️ Discard Output")
        self.discard_btn.setToolTip("Xóa file MIDI vừa tạo và hủy output")
        self.discard_btn.setVisible(False)
        self.discard_btn.setStyleSheet("color: #c0392b;")
        self.discard_btn.clicked.connect(self._on_discard_clicked)

        action_layout.addWidget(self.select_tracks_btn)
        action_layout.addWidget(self.load_playback_btn)
        action_layout.addWidget(self.discard_btn)
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        layout.addStretch()

    def _browse_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a);;All Files (*)"
        )
        if path:
            self.audio_path_edit.setText(path)
            # Auto-generate output path
            base = Path(path).stem
            out = Path(tempfile.gettempdir()) / f"{base}_transcribed.mid"
            self.output_path_edit.setText(str(out))

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save MIDI As", "", "MIDI Files (*.mid)"
        )
        if path:
            if not path.endswith(".mid"):
                path += ".mid"
            self.output_path_edit.setText(path)

    def _start_transcription(self):
        audio_path = self.audio_path_edit.text().strip()
        if not audio_path or not os.path.isfile(audio_path):
            QMessageBox.warning(self, "No Audio File", "Please select a valid audio file.")
            return

        output_path = self.output_path_edit.text().strip()
        if not output_path:
            base = Path(audio_path).stem
            output_path = str(Path(tempfile.gettempdir()) / f"{base}_transcribed.mid")
            self.output_path_edit.setText(output_path)

        engine = self.engine_combo.currentText()
        seg_size = self.seg_size_spin.value()
        seg_hop = self.seg_hop_spin.value()

        self.transcribe_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Transcribing... please wait.")

        # Ẩn các nút post-transcription
        self.select_tracks_btn.setVisible(False)
        self.load_playback_btn.setVisible(False)
        self.discard_btn.setVisible(False)

        self.worker = TranscriberWorker(
            engine, audio_path, output_path, seg_size, seg_hop, parent=self
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self._on_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _cancel_transcription(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_label.setText("Cancelling...")
            self.worker.wait(3000)
        self._reset_ui()

    def _on_log(self, msg: str):
        self.status_label.setText(msg)

    def _on_finished(self, success: bool, result: str):
        self.transcribe_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if success:
            self._last_mid_path = result   # FIX: Lưu lại đường dẫn
            self.status_label.setText(f"✅ Transcription saved to: {result}")
            self.progress_bar.setValue(100)

            # FIX: Hiển thị các nút post-transcription
            self.select_tracks_btn.setVisible(True)
            self.load_playback_btn.setVisible(True)
            self.discard_btn.setVisible(True)

            QMessageBox.information(
                self, "Transcription Complete",
                f"MIDI file saved to:\n{result}\n\n"
                f"You can now:\n"
                f"• 'Select Tracks to Keep' — bỏ tick track không cần\n"
                f"• 'Load into Playback Tab' — đưa vào tab chơi\n"
                f"• 'Discard Output' — xóa file nếu không vừa ý"
            )
        else:
            self.status_label.setText(f"❌ Error: {result}")
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Transcription Failed", result)

    def _on_select_tracks_clicked(self):
        """FIX #2: Mở TrackSelectionDialog để chọn/bỏ chọn track trước khi load."""
        if not self._last_mid_path or not os.path.isfile(self._last_mid_path):
            QMessageBox.warning(self, "No Output", "No transcription output available.")
            return

        try:
            tracks, _ = MidiParser.parse_structure(self._last_mid_path, 1.0, None)
            if not tracks:
                QMessageBox.information(self, "No Tracks", "No playable tracks found in output.")
                return

            dialog = TrackSelectionDialog(tracks, self)
            if dialog.exec() == TrackSelectionDialog.DialogCode.Accepted:
                selection = dialog.get_selection()
                # Lưu lại selection để dùng khi load playback
                self._track_selection = selection
                selected_count = sum(1 for s in selection if s["play"])
                self.status_label.setText(
                    f"Track selection updated: {selected_count}/{len(selection)} tracks enabled"
                )
            else:
                # User bấm Cancel trong dialog → không làm gì
                self.status_label.setText("Track selection cancelled.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open track selection:\n{str(e)}")

    def _on_load_playback(self):
        if self._last_mid_path and os.path.isfile(self._last_mid_path):
            self.load_into_playback.emit(self._last_mid_path)
            self.status_label.setText("Loaded into Playback tab.")
        else:
            QMessageBox.warning(self, "No Output", "No transcription output to load.")

    def _on_discard_clicked(self):
        """FIX #2: Xóa file output MIDI và reset trạng thái."""
        if not self._last_mid_path:
            return

        reply = QMessageBox.question(
            self, "Discard Output",
            f"Bạn có chắc muốn xóa file output?\n\n{self._last_mid_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(self._last_mid_path):
                    os.remove(self._last_mid_path)
                self.status_label.setText("🗑️ Output discarded. Ready for new transcription.")
                self._last_mid_path = None
                self.progress_bar.setValue(0)
                self.select_tracks_btn.setVisible(False)
                self.load_playback_btn.setVisible(False)
                self.discard_btn.setVisible(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file:\n{str(e)}")

    def _reset_ui(self):
        self.transcribe_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.select_tracks_btn.setVisible(False)
        self.load_playback_btn.setVisible(False)
        self.discard_btn.setVisible(False)
