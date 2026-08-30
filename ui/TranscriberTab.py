"""
TranscriberTab — AI Audio-to-MIDI Transcription
Tích hợp TransKun v2 + Spectral Onset fallback
"""
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QTextEdit, QComboBox, QGroupBox,
    QCheckBox, QMessageBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from managers.i18n import I18nManager


class TranscriptionWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, dict)

    def __init__(self, audio_path: str, output_path: str,
                 engine: str, use_gpu: bool,
                 segment_size: float = 20.0, segment_hop: float = 10.0):
        super().__init__()
        self.audio_path = audio_path
        self.output_path = output_path
        self.engine = engine
        self.use_gpu = use_gpu
        self.segment_size = segment_size
        self.segment_hop = segment_hop

    def run(self):
        try:
            self.log.emit(f"🎵 Loading audio: {Path(self.audio_path).name}")
            self.progress.emit(5)

            from transcriber.audio_loader import load_audio
            audio, sr = load_audio(self.audio_path)
            self.progress.emit(15)

            if self.engine == "TransKun v2 (Neural)":
                self.log.emit("🧠 Initializing TransKun v2...")
                from transcriber.transkun_engine import TransKunEngine

                device = "cuda" if self.use_gpu else "cpu"
                engine = TransKunEngine(device=device)

                if not engine.available:
                    raise RuntimeError("TransKun not installed. Run: pip install transkun")

                self.progress.emit(30)
                self.log.emit(f"⚙️ Device: {engine.device}")
                self.log.emit("⏳ Transcribing... (may take a few minutes for long files)")

                result = engine.transcribe(
                    self.audio_path,
                    self.output_path,
                    segment_size=self.segment_size,
                    segment_hop=self.segment_hop
                )
                self.progress.emit(100)
                self.log.emit(f"✅ Done! ~{result.get('notes_estimated', '?')} notes detected")

            else:
                self.log.emit("📊 Running Spectral Onset Parser...")
                from transcriber.spectral_engine import SpectralOnsetEngine

                engine = SpectralOnsetEngine(sr=sr)
                result = engine.transcribe(audio, self.output_path)
                self.progress.emit(100)
                self.log.emit(f"✅ Done! {result.get('notes_detected', 0)} notes detected")

            self.finished.emit(True, result)

        except Exception as e:
            self.log.emit(f"❌ Error: {str(e)}")
            self.finished.emit(False, {"error": str(e)})


class TranscriberTab(QWidget):
    load_midi_requested = pyqtSignal(str)  # Signal để load MIDI vào Playback

    def __init__(self):
        super().__init__()
        self.audio_path = None
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("🧠 AI Audio-to-MIDI Transcriber")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #00ff88;")
        layout.addWidget(title)

        subtitle = QLabel("Convert MP3 / WAV / FLAC into note-accurate MIDI files")
        subtitle.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(subtitle)

        # Input
        input_group = QGroupBox("📁 Audio Input")
        input_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #666;")
        self.file_label.setWordWrap(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setToolTip("Select MP3, WAV, FLAC, M4A, OGG")
        browse_btn.clicked.connect(self._browse_audio)
        input_layout.addWidget(self.file_label, 1)
        input_layout.addWidget(browse_btn)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Engine
        engine_group = QGroupBox("⚙️ Transcription Engine")
        engine_layout = QVBoxLayout()
        self.engine_combo = QComboBox()
        self.engine_combo.addItems([
            "TransKun v2 (Neural — Best for Piano)",
            "Spectral Onset (Zero-Dependency — Universal)"
        ])
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)

        gpu_layout = QHBoxLayout()
        self.gpu_check = QCheckBox("Use GPU (CUDA)")
        self.gpu_check.setToolTip("Significant speedup if you have NVIDIA GPU")
        try:
            import torch
            self.gpu_check.setEnabled(torch.cuda.is_available())
            if not torch.cuda.is_available():
                self.gpu_check.setToolTip("No CUDA GPU detected")
        except ImportError:
            self.gpu_check.setEnabled(False)
            self.gpu_check.setToolTip("torch not installed")

        self.segment_size_spin = QDoubleSpinBox()
        self.segment_size_spin.setRange(5.0, 60.0)
        self.segment_size_spin.setValue(20.0)
        self.segment_size_spin.setSuffix(" s")

        self.segment_hop_spin = QDoubleSpinBox()
        self.segment_hop_spin.setRange(2.0, 30.0)
        self.segment_hop_spin.setValue(10.0)
        self.segment_hop_spin.setSuffix(" s")

        seg_layout = QHBoxLayout()
        seg_layout.addWidget(QLabel("Segment:"))
        seg_layout.addWidget(self.segment_size_spin)
        seg_layout.addWidget(QLabel("Hop:"))
        seg_layout.addWidget(self.segment_hop_spin)
        seg_layout.addStretch()

        gpu_layout.addWidget(self.gpu_check)
        gpu_layout.addStretch()

        engine_layout.addWidget(self.engine_combo)
        engine_layout.addLayout(gpu_layout)
        engine_layout.addLayout(seg_layout)
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)

        # Output
        out_group = QGroupBox("💾 Output MIDI")
        out_layout = QHBoxLayout()
        self.output_label = QLabel("transcription_output.mid")
        self.output_label.setStyleSheet("color: #666;")
        out_btn = QPushButton("Choose...")
        out_btn.clicked.connect(self._choose_output)
        out_layout.addWidget(self.output_label, 1)
        out_layout.addWidget(out_btn)
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

        # Progress & Log
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(140)
        self.log_box.setPlaceholderText("Transcription log will appear here...")
        self.log_box.setStyleSheet(
            "QTextEdit { background: #1a1a2e; color: #00ff88; "
            "border: 1px solid #333; border-radius: 4px; font-family: monospace; }"
        )
        layout.addWidget(self.log_box)

        # Transcribe
        self.transcribe_btn = QPushButton("▶️ Start Transcription")
        self.transcribe_btn.setStyleSheet(
            "QPushButton { background: #00ff88; color: #000; font-weight: bold; "
            "padding: 10px; border-radius: 6px; font-size: 13px; }"
            "QPushButton:hover { background: #00cc66; }"
            "QPushButton:disabled { background: #444; color: #888; }"
        )
        self.transcribe_btn.clicked.connect(self._start_transcription)
        layout.addWidget(self.transcribe_btn)

        # Load to Playback button (hidden until done)
        self.load_playback_btn = QPushButton("🎹 Load into Playback Tab")
        self.load_playback_btn.setStyleSheet(
            "QPushButton { background: #2d2d3a; color: #00ff88; border: 1px solid #00ff88; "
            "padding: 8px; border-radius: 6px; font-size: 12px; }"
            "QPushButton:hover { background: #00ff88; color: #000; }"
        )
        self.load_playback_btn.setVisible(False)
        self.load_playback_btn.clicked.connect(self._load_to_playback)
        layout.addWidget(self.load_playback_btn)

        info = QLabel(
            "💡 <b>TransKun v2</b>: High accuracy for piano solo (F1 ~95%). Requires installation.<br>"
            "💡 <b>Spectral Onset</b>: No AI needed, works with any music, but lower accuracy."
        )
        info.setStyleSheet("color: #777; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()

    def _on_engine_changed(self, index: int):
        is_transkun = (index == 0)
        self.gpu_check.setVisible(is_transkun)
        self.segment_size_spin.setVisible(is_transkun)
        self.segment_hop_spin.setVisible(is_transkun)

    def _browse_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg);;All Files (*)"
        )
        if path:
            self.audio_path = path
            self.file_label.setText(Path(path).name)
            self.file_label.setStyleSheet("color: #00ff88; font-weight: bold;")
            out = str(Path(path).with_suffix('.mid'))
            self.output_label.setText(out)
            self.load_playback_btn.setVisible(False)

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save MIDI File", self.output_label.text(),
            "MIDI Files (*.mid *.midi);;All Files (*)"
        )
        if path:
            if not path.lower().endswith(('.mid', '.midi')):
                path += '.mid'
            self.output_label.setText(path)

    def _start_transcription(self):
        if not self.audio_path:
            QMessageBox.warning(self, "No File", "Please select an audio file first!")
            return

        output = self.output_label.text()
        engine = self.engine_combo.currentText()
        use_gpu = self.gpu_check.isChecked() and self.gpu_check.isEnabled()

        self.transcribe_btn.setEnabled(False)
        self.load_playback_btn.setVisible(False)
        self.progress_bar.setValue(0)
        self.log_box.clear()

        seg_size = self.segment_size_spin.value()
        seg_hop = self.segment_hop_spin.value()

        self.worker = TranscriptionWorker(
            self.audio_path, output, engine, use_gpu, seg_size, seg_hop
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self._append_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _append_log(self, msg: str):
        self.log_box.append(msg)

    def _on_finished(self, success: bool, result: dict):
        self.transcribe_btn.setEnabled(True)
        if success:
            out_path = result.get('output', 'unknown')
            notes = result.get('notes_estimated', result.get('notes_detected', 0))
            self._append_log(f"💾 Saved: {out_path}")
            self.load_playback_btn.setVisible(True)
            self._last_mid_path = out_path
            QMessageBox.information(
                self, "Transcription Complete",
                f"Successfully transcribed to:\n{out_path}\n\nNotes detected: ~{notes}"
            )
        else:
            err = result.get('error', 'Unknown error')
            QMessageBox.critical(self, "Transcription Failed", str(err))

    def _load_to_playback(self):
        if hasattr(self, '_last_mid_path') and os.path.exists(self._last_mid_path):
            self.load_midi_requested.emit(self._last_mid_path)
