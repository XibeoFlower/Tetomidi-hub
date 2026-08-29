from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QSlider,
    QLabel, QComboBox, QLineEdit, QGridLayout)
from PyQt6.QtCore import Qt

from ui.widgets import make_card
from ui.theme import ThemeManager
from managers.i18n import I18nManager


class SettingsTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        # ── Save Path card (full width) ────────────────────────────────
        save_card, save_content = make_card(I18nManager.t("save_path"))
        save_row = QHBoxLayout()
        save_row.setSpacing(8)
        self.save_path_input = QLineEdit()
        self.save_path_input.setReadOnly(True)
        self.save_path_input.setToolTip(I18nManager.t("tt_save_path"))
        self.save_browse_btn = QPushButton(I18nManager.t("browse"))
        self.save_browse_btn.setToolTip(I18nManager.t("tt_browse_save"))
        save_row.addWidget(self.save_path_input)
        save_row.addWidget(self.save_browse_btn)
        save_content.addLayout(save_row)
        outer.addWidget(save_card)

        # ── Two-column body ────────────────────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        # Hotkey card
        hk_card, hk_content = make_card(I18nManager.t("hotkey"))
        hk_row = QHBoxLayout()
        hk_row.setSpacing(8)
        self.hk_label = QLabel(I18nManager.t("hotkey") + ": ")
        self.hk_btn = QPushButton(I18nManager.t("change"))
        self.hk_btn.setToolTip(I18nManager.t("tt_hotkey"))
        hk_row.addWidget(self.hk_label, 1)
        hk_row.addWidget(self.hk_btn)
        hk_content.addLayout(hk_row)
        left_col.addWidget(hk_card)

        # Overlay card
        ov_card, ov_content = make_card(I18nManager.t("overlay"))
        ov_grid = QGridLayout()
        ov_grid.setSpacing(8)
        self.always_top_check = QCheckBox(I18nManager.t("always_on_top"))
        self.always_top_check.setToolTip(I18nManager.t("tt_always_top"))
        opacity_label = QLabel(I18nManager.t("opacity"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setToolTip(I18nManager.t("tt_opacity"))
        ov_grid.addWidget(self.always_top_check, 0, 0, 1, 2)
        ov_grid.addWidget(opacity_label,         1, 0)
        ov_grid.addWidget(self.opacity_slider,   1, 1)
        ov_content.addLayout(ov_grid)
        left_col.addWidget(ov_card)

        self.check_update_btn = QPushButton(I18nManager.t("check_updates"))
        self.check_update_btn.setToolTip(I18nManager.t("tt_check_update"))
        left_col.addWidget(self.check_update_btn)
        left_col.addStretch()

        # Visualizer card
        vis_card, vis_content = make_card(I18nManager.t("visualizer"))
        self.timeline_vis_check = QCheckBox(I18nManager.t("timeline"))
        self.timeline_vis_check.setChecked(True)
        self.timeline_vis_check.setToolTip(I18nManager.t("tt_timeline"))
        self.piano_vis_check = QCheckBox(I18nManager.t("piano_keys"))
        self.piano_vis_check.setChecked(True)
        self.piano_vis_check.setToolTip(I18nManager.t("tt_piano_vis"))
        vis_content.addWidget(self.timeline_vis_check)
        vis_content.addWidget(self.piano_vis_check)
        right_col.addWidget(vis_card)

        # Theme card
        theme_card, theme_content = make_card(I18nManager.t("theme"))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        self.theme_combo = QComboBox()
        self.theme_combo.setToolTip(I18nManager.t("tt_theme"))
        self._populate_theme_combo()
        self.theme_customize_btn = QPushButton(I18nManager.t("customize"))
        self.theme_customize_btn.setToolTip(I18nManager.t("tt_customize"))
        theme_row.addWidget(self.theme_combo, 1)
        theme_row.addWidget(self.theme_customize_btn)
        theme_content.addLayout(theme_row)
        right_col.addWidget(theme_card)

        # Language card (NEW)
        lang_card, lang_content = make_card(I18nManager.t("language"))
        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)
        self.lang_combo = QComboBox()
        self.lang_combo.setToolTip(I18nManager.t("tt_language"))
        for code, name in I18nManager.all_languages().items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(0)  # Default English
        lang_row.addWidget(self.lang_combo, 1)
        lang_content.addLayout(lang_row)
        right_col.addWidget(lang_card)
        right_col.addStretch()

        body.addLayout(left_col, 1)
        body.addLayout(right_col, 1)
        outer.addLayout(body, 1)

    def _populate_theme_combo(self) -> None:
        active = ThemeManager.get_active_name()
        for name in ThemeManager.all_themes():
            self.theme_combo.addItem(name)
        idx = self.theme_combo.findText(active)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

    # ── Public API ─────────────────────────────────────────────────────

    def refresh_theme_combo(self) -> None:
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self._populate_theme_combo()
        self.theme_combo.blockSignals(False)

    def load_config(self, config: dict, save_dir: str) -> None:
        self.always_top_check.setChecked(config.get('always_on_top', False))
        self.opacity_slider.setValue(config.get('opacity', 100))
        self.timeline_vis_check.setChecked(config.get('show_timeline_visualizer', True))
        self.piano_vis_check.setChecked(config.get('show_piano_visualizer', True))
        self.save_path_input.setText(save_dir)
        # Load language
        lang = config.get('language', 'en')
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == lang:
                self.lang_combo.setCurrentIndex(i)
                break

    def gather_config(self) -> dict:
        return {
            'always_on_top':             self.always_top_check.isChecked(),
            'opacity':                   self.opacity_slider.value(),
            'show_timeline_visualizer':  self.timeline_vis_check.isChecked(),
            'show_piano_visualizer':     self.piano_vis_check.isChecked(),
            'language':                  self.lang_combo.currentData(),
        }
