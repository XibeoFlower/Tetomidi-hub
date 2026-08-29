from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QSlider,
    QLabel, QComboBox, QSpinBox, QGridLayout, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QFont, QPen, QBrush

from ui.widgets import make_card
from ui.animated_button import AnimatedButton
from managers.i18n import I18nManager


class FretboardWidget(QWidget):
    """Guitar fretboard visualizer showing 6 strings and frets with active notes."""

    STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # E2, A2, D3, G3, B3, E4
    STRING_NAMES = ["E", "A", "D", "G", "B", "e"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.setMaximumHeight(280)
        self.active_notes = set()  # set of (string_idx, fret)
        self._flash_notes = {}     # (string_idx, fret) -> flash intensity (0-1)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._decay_flash)
        self._timer.start(50)

        self.bg_color = QColor("#1c1c2e")
        self.fret_color = QColor("#32324a")
        self.string_color = QColor("#7878a0")
        self.note_color = QColor("#e0263f")
        self.note_glow = QColor("#ff4d6d")
        self.nut_color = QColor("#dcdcf0")

    def set_active_notes(self, notes: list):
        """notes: list of (midi_pitch, velocity)"""
        self.active_notes.clear()
        for pitch, vel in notes:
            for s_idx, open_pitch in enumerate(self.STANDARD_TUNING):
                fret = pitch - open_pitch
                if 0 <= fret <= 24:
                    self.active_notes.add((s_idx, fret))
                    self._flash_notes[(s_idx, fret)] = 1.0
        self.update()

    def clear(self):
        self.active_notes.clear()
        self._flash_notes.clear()
        self.update()

    def _decay_flash(self):
        to_remove = []
        for key, intensity in self._flash_notes.items():
            self._flash_notes[key] = max(0, intensity - 0.08)
            if self._flash_notes[key] <= 0:
                to_remove.append(key)
        for key in to_remove:
            del self._flash_notes[key]
        if to_remove or self._flash_notes:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 20
        fretboard_w = w - margin * 2
        fretboard_h = h - margin * 2

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw frets
        num_frets = 18
        fret_spacing = fretboard_w / num_frets

        for i in range(num_frets + 1):
            x = margin + i * fret_spacing
            pen = QPen(self.nut_color if i == 0 else self.fret_color)
            pen.setWidth(3 if i == 0 else 1)
            painter.setPen(pen)
            painter.drawLine(int(x), margin, int(x), h - margin)

            # Fret markers (dots)
            if i > 0 and i in [3, 5, 7, 9, 12, 15, 17]:
                dot_x = int(x - fret_spacing / 2)
                dot_y = margin + fretboard_h // 2
                painter.setBrush(QBrush(QColor("#7878a0")))
                painter.setPen(Qt.PenStyle.NoPen)
                radius = 4 if i != 12 else 3
                painter.drawEllipse(dot_x - radius, dot_y - radius, radius * 2, radius * 2)
                if i == 12:
                    painter.drawEllipse(dot_x - radius, dot_y - 30 - radius, radius * 2, radius * 2)

        # Draw strings
        string_spacing = fretboard_h / 5
        for s in range(6):
            y = int(margin + s * string_spacing)
            pen = QPen(self.string_color)
            pen.setWidth(max(1, 3 - s // 2))
            painter.setPen(pen)
            painter.drawLine(margin, y, w - margin, y)

        # Draw active notes
        for (s_idx, fret), flash in self._flash_notes.items():
            y = int(margin + s_idx * string_spacing)
            x = int(margin + fret * fret_spacing - fret_spacing / 2)

            # Glow effect based on flash intensity
            glow_alpha = int(255 * flash)
            glow_color = QColor(self.note_glow)
            glow_color.setAlpha(glow_alpha)

            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x - 8, y - 8, 16, 16)

            # Inner solid
            solid_color = QColor(self.note_color)
            solid_color.setAlpha(int(200 + 55 * flash))
            painter.setBrush(QBrush(solid_color))
            painter.drawEllipse(x - 5, y - 5, 10, 10)

            # Fret number
            painter.setPen(QPen(QColor("#ffffff")))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(x - 10, y - 12, 20, 10, Qt.AlignmentFlag.AlignCenter, str(fret))

        # String labels
        painter.setPen(QPen(self.string_color))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        for s, name in enumerate(self.STRING_NAMES):
            y = int(margin + s * string_spacing)
            painter.drawText(2, y - 8, margin - 4, 16, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, name)

        painter.end()


class GuitarTab(QWidget):
    """Dedicated Guitar Auto-Play tab with fretboard visualizer and guitar-specific settings."""

    TUNINGS = {
        "Standard (EADGBE)": [40, 45, 50, 55, 59, 64],
        "Drop D (DADGBE)": [38, 45, 50, 55, 59, 64],
        "D Standard (DGCFAD)": [38, 43, 48, 53, 57, 62],
        "Half Step Down": [39, 44, 49, 54, 58, 63],
        "Open G (DGDGBD)": [38, 43, 47, 55, 59, 62],
    }

    STRUM_PATTERNS = {
        "Down Only": [1, 0, 0, 0],
        "Down-Up": [1, 0, 1, 0],
        "Down-Down-Up": [1, 1, 0, 1, 0, 1, 0, 1],
        "Folk": [1, 0, 1, 0, 1, 1, 0, 1],
        "Fingerpicking": [1, 0, 0, 1, 0, 0, 1, 0],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        # Left column: controls
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        # File card
        file_card, file_layout = make_card(I18nManager.t("midi_file"))
        self.file_path_label = QLabel(I18nManager.t("no_file_selected"))
        self.file_path_label.setObjectName("file_path_label")
        self.file_path_label.setWordWrap(True)

        file_btn_row = QHBoxLayout()
        file_btn_row.setSpacing(6)
        self.browse_button = AnimatedButton(I18nManager.t("browse"))
        self.browse_button.setToolTip(I18nManager.t("tt_browse"))
        self.load_saved_btn = AnimatedButton(I18nManager.t("load_save"))
        self.load_saved_btn.setToolTip(I18nManager.t("tt_load_save"))
        file_btn_row.addWidget(self.browse_button)
        file_btn_row.addWidget(self.load_saved_btn)

        file_layout.addWidget(self.file_path_label)
        file_layout.addLayout(file_btn_row)
        left_col.addWidget(file_card)

        # Guitar Settings card
        settings_card, settings_layout = make_card("Guitar Settings")
        grid = QGridLayout()
        grid.setSpacing(8)

        # Tuning
        tuning_label = QLabel("Tuning")
        self.tuning_combo = QComboBox()
        self.tuning_combo.addItems(list(self.TUNINGS.keys()))
        self.tuning_combo.setToolTip("Select guitar tuning")
        grid.addWidget(tuning_label, 0, 0)
        grid.addWidget(self.tuning_combo, 0, 1, 1, 2)

        # Capo
        capo_label = QLabel("Capo")
        self.capo_spinbox = QSpinBox()
        self.capo_spinbox.setRange(0, 12)
        self.capo_spinbox.setValue(0)
        self.capo_spinbox.setSuffix(" fret")
        self.capo_spinbox.setToolTip("Place capo on fret (shifts all notes up)")
        grid.addWidget(capo_label, 1, 0)
        grid.addWidget(self.capo_spinbox, 1, 1)

        # Strum Pattern
        pattern_label = QLabel("Strum Pattern")
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(list(self.STRUM_PATTERNS.keys()))
        self.pattern_combo.setToolTip("Choose strumming pattern for auto-play")
        grid.addWidget(pattern_label, 2, 0)
        grid.addWidget(self.pattern_combo, 2, 1, 1, 2)

        # Strum Speed
        speed_label = QLabel("Strum Speed")
        self.strum_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.strum_speed_slider.setRange(50, 200)
        self.strum_speed_slider.setValue(100)
        self.strum_speed_slider.setToolTip("Strumming speed percentage")
        grid.addWidget(speed_label, 3, 0)
        grid.addWidget(self.strum_speed_slider, 3, 1, 1, 2)

        # Options
        self.palm_mute_check = QCheckBox("Palm Mute")
        self.palm_mute_check.setToolTip("Simulate palm muting on staccato notes")
        self.slide_check = QCheckBox("Enable Slides")
        self.slide_check.setToolTip("Simulate sliding between adjacent frets")
        self.hammer_on_check = QCheckBox("Hammer-On / Pull-Off")
        self.hammer_on_check.setToolTip("Simulate hammer-ons and pull-offs for fast passages")

        settings_layout.addLayout(grid)
        settings_layout.addWidget(self.palm_mute_check)
        settings_layout.addWidget(self.slide_check)
        settings_layout.addWidget(self.hammer_on_check)
        settings_layout.addStretch()
        left_col.addWidget(settings_card)

        # Playback controls
        ctrl_card, ctrl_layout = make_card(I18nManager.t("playback"))
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self.play_button = AnimatedButton("▶  " + I18nManager.t("play"))
        self.play_button.setObjectName("play_button")
        self.play_button.setToolTip(I18nManager.t("tt_play"))
        self.play_button.setEnabled(False)

        self.stop_button = AnimatedButton("■  " + I18nManager.t("stop"))
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setToolTip(I18nManager.t("tt_stop"))
        self.stop_button.setEnabled(False)

        self.countdown_check = QCheckBox(I18nManager.t("countdown"))
        self.countdown_check.setChecked(True)
        self.countdown_check.setToolTip(I18nManager.t("tt_countdown"))

        ctrl_row.addWidget(self.play_button)
        ctrl_row.addWidget(self.stop_button)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.countdown_check)
        ctrl_layout.addLayout(ctrl_row)
        left_col.addWidget(ctrl_card)
        left_col.addStretch()

        # Right column: fretboard + info
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        # Fretboard visualizer
        fb_card, fb_layout = make_card("Fretboard")
        self.fretboard = FretboardWidget()
        fb_layout.addWidget(self.fretboard)
        right_col.addWidget(fb_card)

        # Info / Chord display
        info_card, info_layout = make_card("Now Playing")
        self.chord_label = QLabel("—")
        self.chord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chord_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #e0263f;")
        info_layout.addWidget(self.chord_label)

        self.note_info_label = QLabel("Load a MIDI file to start")
        self.note_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.note_info_label.setProperty("role", "muted")
        info_layout.addWidget(self.note_info_label)
        right_col.addWidget(info_card)
        right_col.addStretch()

        outer.addLayout(left_col, 1)
        outer.addLayout(right_col, 1)

    def update_file_label(self, text: str, tooltip: str = "") -> None:
        self.file_path_label.setText(text)
        self.file_path_label.setToolTip(tooltip)

    def set_controls_enabled(self, enabled: bool) -> None:
        self.browse_button.setEnabled(enabled)
        self.load_saved_btn.setEnabled(enabled)
        self.tuning_combo.setEnabled(enabled)
        self.capo_spinbox.setEnabled(enabled)
        self.pattern_combo.setEnabled(enabled)
        self.strum_speed_slider.setEnabled(enabled)
        self.palm_mute_check.setEnabled(enabled)
        self.slide_check.setEnabled(enabled)
        self.hammer_on_check.setEnabled(enabled)
        self.countdown_check.setEnabled(enabled)

    def gather_guitar_config(self) -> dict:
        return {
            'mode': 'guitar',
            'tuning': self.tuning_combo.currentText(),
            'tuning_pitches': self.TUNINGS[self.tuning_combo.currentText()],
            'capo': self.capo_spinbox.value(),
            'strum_pattern': self.pattern_combo.currentText(),
            'strum_pattern_data': self.STRUM_PATTERNS[self.pattern_combo.currentText()],
            'strum_speed': self.strum_speed_slider.value(),
            'palm_mute': self.palm_mute_check.isChecked(),
            'slide': self.slide_check.isChecked(),
            'hammer_on': self.hammer_on_check.isChecked(),
            'countdown': self.countdown_check.isChecked(),
            'instrument': 'guitar',
        }

    def reset_to_default(self) -> None:
        self.tuning_combo.setCurrentIndex(0)
        self.capo_spinbox.setValue(0)
        self.pattern_combo.setCurrentIndex(0)
        self.strum_speed_slider.setValue(100)
        self.palm_mute_check.setChecked(False)
        self.slide_check.setChecked(False)
        self.hammer_on_check.setChecked(False)
        self.countdown_check.setChecked(True)

    def load_config(self, config: dict) -> None:
        tuning = config.get('guitar_tuning', 'Standard (EADGBE)')
        idx = self.tuning_combo.findText(tuning)
        if idx >= 0:
            self.tuning_combo.setCurrentIndex(idx)
        self.capo_spinbox.setValue(config.get('guitar_capo', 0))
        pattern = config.get('guitar_strum_pattern', 'Down Only')
        idx = self.pattern_combo.findText(pattern)
        if idx >= 0:
            self.pattern_combo.setCurrentIndex(idx)
        self.strum_speed_slider.setValue(config.get('guitar_strum_speed', 100))
        self.palm_mute_check.setChecked(config.get('guitar_palm_mute', False))
        self.slide_check.setChecked(config.get('guitar_slide', False))
        self.hammer_on_check.setChecked(config.get('guitar_hammer_on', False))
        self.countdown_check.setChecked(config.get('countdown', True))

    def gather_app_config(self) -> dict:
        return {
            'guitar_tuning': self.tuning_combo.currentText(),
            'guitar_capo': self.capo_spinbox.value(),
            'guitar_strum_pattern': self.pattern_combo.currentText(),
            'guitar_strum_speed': self.strum_speed_slider.value(),
            'guitar_palm_mute': self.palm_mute_check.isChecked(),
            'guitar_slide': self.slide_check.isChecked(),
            'guitar_hammer_on': self.hammer_on_check.isChecked(),
        }
