import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QCheckBox, QSlider, QLabel, QStackedWidget, QFrame,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QObject, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QGuiApplication, QCursor

from ui.widgets import NavButton
from ui.PlaybackTab import PlaybackTab
from ui.GuitarTab import GuitarTab
from ui.SettingsTab import SettingsTab
from ui.TranslatorTab import TranslatorTab
from ui.VisualizerTab import VisualizerTab
from ui.DebugTab import DebugTab
from ui.EditMidiTab import EditMidiTab
from ui.TranscriberTab import TranscriberTab
from ui.theme import ThemeManager, generate_stylesheet
from ui.animated_button import AnimatedButton
from managers.i18n import I18nManager


def _resource_path(*relative_parts: str) -> str:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, *relative_parts)


def _make_mdl2_icon(glyph: str, color: QColor, pixel_size: int = 14) -> QIcon:
    pix = QPixmap(pixel_size, pixel_size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    f = QFont("Segoe MDL2 Assets")
    f.setPixelSize(pixel_size)
    p.setFont(f)
    p.setPen(color)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
    p.end()
    return QIcon(pix)


class ElidingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        if text:
            self._update_elided()

    def setText(self, text):
        self._full_text = text
        self._update_elided()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        width = self.contentsRect().width()
        if width <= 0:
            return
        elided = self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, width
        )
        super().setText(elided)


class MainWindowUI(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("main_widget")
        self.main_window.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._is_collapsed = False

        # ── Collapsed mini strip ───────────────────────────────────────
        self._collapsed_strip = QFrame()
        self._collapsed_strip.setObjectName("collapsed_strip")
        self._collapsed_strip.setVisible(False)
        cs_layout = QVBoxLayout(self._collapsed_strip)
        cs_layout.setContentsMargins(12, 6, 12, 6)
        cs_layout.setSpacing(4)

        self._collapsed_file_label = ElidingLabel(I18nManager.t("no_file_selected"))
        self._collapsed_file_label.setObjectName("file_path_label")
        cs_layout.addWidget(self._collapsed_file_label)

        self._collapsed_humanize_check = QCheckBox(I18nManager.t("humanization"))
        self._collapsed_humanize_check.setToolTip(I18nManager.t("tt_humanize_all"))
        cs_layout.addWidget(self._collapsed_humanize_check)

        self._collapsed_load_btn = AnimatedButton("")
        self._collapsed_load_btn.setObjectName("cs_load_btn")
        self._collapsed_load_btn.setIconSize(QSize(16, 16))
        self._collapsed_load_btn.setToolTip(I18nManager.t("tt_browse"))

        self._collapsed_load_saved_btn = AnimatedButton("")
        self._collapsed_load_saved_btn.setObjectName("cs_load_saved_btn")
        self._collapsed_load_saved_btn.setIconSize(QSize(16, 16))
        self._collapsed_load_saved_btn.setToolTip(I18nManager.t("tt_load_save"))

        self._collapsed_save_btn = AnimatedButton("\uE74E")
        self._collapsed_save_btn.setObjectName("cs_save_btn")
        self._collapsed_save_btn.setToolTip(I18nManager.t("tt_save_transport"))
        self._collapsed_save_btn.setEnabled(False)

        cs_row3 = QHBoxLayout()
        cs_row3.setSpacing(5)
        cs_row3.addWidget(self._collapsed_load_btn, 1)
        cs_row3.addWidget(self._collapsed_load_saved_btn, 1)
        cs_layout.addLayout(cs_row3)

        self._cs_scrubber_row = QWidget()
        self._cs_scrubber_layout = QVBoxLayout(self._cs_scrubber_row)
        self._cs_scrubber_layout.setContentsMargins(0, 0, 0, 0)
        self._cs_scrubber_layout.setSpacing(2)
        cs_layout.addWidget(self._cs_scrubber_row)

        self._cs_playback_row = QWidget()
        self._cs_playback_layout = QHBoxLayout(self._cs_playback_row)
        self._cs_playback_layout.setContentsMargins(0, 0, 0, 0)
        self._cs_playback_layout.setSpacing(5)
        cs_layout.addWidget(self._cs_playback_row)

        self._cs_expand_row = QWidget()
        self._cs_expand_layout = QHBoxLayout(self._cs_expand_row)
        self._cs_expand_layout.setContentsMargins(0, 0, 0, 0)
        self._cs_expand_layout.setSpacing(0)
        cs_layout.addWidget(self._cs_expand_row)

        self._cs_layout = cs_layout
        main_layout.addWidget(self._collapsed_strip)

        # ── Body: sidebar + page stack ─────────────────────────────────
        self._body = QWidget()
        body_layout = QHBoxLayout(self._body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(120)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sidebar_vbox = QVBoxLayout(sidebar)
        sidebar_vbox.setContentsMargins(0, 0, 0, 0)
        sidebar_vbox.setSpacing(0)

        self.tabs = QStackedWidget()
        self.tabs.currentChanged.connect(self._on_page_changed)

        _NAV_ITEMS = [
            ("\uE768", I18nManager.t("nav_playback")),
            ("\uE8D6", I18nManager.t("nav_visualizer")),
            ("\uE8B1", I18nManager.t("nav_translator")),
            ("\uE83E", I18nManager.t("nav_guitar")),
            ("\uE95F", "Transcriber"),
            ("\uE713", I18nManager.t("nav_settings")),
            ("\uEBE8", I18nManager.t("nav_debug")),
            ("\uE70F", I18nManager.t("nav_edit_midi")),
        ]
        self._nav_btns: list[NavButton] = []
        for i, (icon, label) in enumerate(_NAV_ITEMS):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda idx=i: self._switch_page(idx))
            sidebar_vbox.addWidget(btn)
            self._nav_btns.append(btn)

        sidebar_vbox.addStretch()

        # ── Discord contact footer ─────────────────────────────────────
        self.discord_btn = AnimatedButton("  @xiunolove")
        self.discord_btn.setObjectName("discord_footer_btn")
        self.discord_btn.setFlat(True)
        self.discord_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.discord_btn.setToolTip(I18nManager.t("discord_tooltip"))
        avatar_path = _resource_path("discord_avatar.png")
        if os.path.exists(avatar_path):
            self.discord_btn.setIcon(QIcon(avatar_path))
        else:
            self.discord_btn.setIcon(_make_mdl2_icon("\uE8F2", QColor("#5865F2"), 16))
        self.discord_btn.setIconSize(QSize(20, 20))
        self.discord_btn.setStyleSheet(
            "QPushButton#discord_footer_btn {"
            "  text-align: left; padding: 8px 12px; border: none;"
            "  color: #5865F2; font-size: 11px; font-weight: 600;"
            "}"
            "QPushButton#discord_footer_btn:hover { color: #7289FF; }"
        )
        self.discord_btn.clicked.connect(self._copy_discord_tag)
        sidebar_vbox.addWidget(self.discord_btn)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.tabs, 1)
        main_layout.addWidget(self._body, 1)

        # ── Pages ──────────────────────────────────────────────────────
        self.playback_tab    = PlaybackTab()
        self.visualizer_tab  = VisualizerTab()
        self.translator_tab  = TranslatorTab()
        self.guitar_tab      = GuitarTab()
        self.transcriber_tab = TranscriberTab()
        self.settings_tab    = SettingsTab()
        self.debug_tab       = DebugTab()
        self.edit_midi_tab   = EditMidiTab()

        self.tabs.addWidget(self.playback_tab)     # 0
        self.tabs.addWidget(self.visualizer_tab)   # 1
        self.tabs.addWidget(self.translator_tab)   # 2
        self.tabs.addWidget(self.guitar_tab)       # 3
        self.tabs.addWidget(self.transcriber_tab)  # 4  NEW
        self.tabs.addWidget(self.settings_tab)     # 5
        self.tabs.addWidget(self.debug_tab)        # 6
        self.tabs.addWidget(self.edit_midi_tab)    # 7

        # ── Convenience aliases ────────────────────────────────────────
        self.log_output      = self.debug_tab.log_output
        self.timeline_widget = self.visualizer_tab.timeline_widget
        self.piano_widget    = self.visualizer_tab.piano_widget
        self.scroll_area     = self.visualizer_tab.scroll_area

        # ── Transport bar ─────────────────────────────────────────────
        transport_bar = QFrame()
        transport_bar.setObjectName("transport_bar")
        transport_layout = QVBoxLayout(transport_bar)
        transport_layout.setContentsMargins(16, 10, 16, 10)
        transport_layout.setSpacing(6)

        self.scrubber_slider = QSlider(Qt.Orientation.Horizontal)
        self.scrubber_slider.setObjectName("scrubber_slider")
        self.scrubber_slider.setRange(0, 10000)
        self.scrubber_slider.sliderPressed.connect(self._on_scrubber_pressed)
        self.scrubber_slider.sliderMoved.connect(self._on_scrubber_moved)
        self.scrubber_slider.sliderReleased.connect(self._on_scrubber_released)
        self._scrubber_dragging = False
        transport_layout.addWidget(self.scrubber_slider)

        self._btn_row_widget = QWidget()
        btn_row = QHBoxLayout(self._btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(5)

        self.play_button = AnimatedButton("▶  " + I18nManager.t("play"))
        self.play_button.setObjectName("play_button")
        self.play_button.setToolTip(I18nManager.t("tt_play"))

        self.stop_button = AnimatedButton("■  " + I18nManager.t("stop"))
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setToolTip(I18nManager.t("tt_stop"))

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("time_label")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.save_button = AnimatedButton(I18nManager.t("save"))
        self.save_button.setObjectName("save_button")
        self.save_button.setToolTip(I18nManager.t("tt_save_transport"))

        self.reset_button = AnimatedButton(I18nManager.t("reset"))
        self.reset_button.setObjectName("reset_button")
        self.reset_button.setToolTip(I18nManager.t("tt_reset"))

        btn_row.addWidget(self.play_button)
        btn_row.addWidget(self.stop_button)
        btn_row.addStretch()
        btn_row.addWidget(self.time_label)
        btn_row.addStretch()
        btn_row.addWidget(self.save_button)
        btn_row.addWidget(self.reset_button)

        self.collapse_btn = AnimatedButton("▲  " + I18nManager.t("collapse"))
        self.collapse_btn.setObjectName("collapse_btn")
        self.collapse_btn.setToolTip(I18nManager.t("tt_collapse"))
        self.collapse_btn.clicked.connect(self._toggle_collapsed)
        btn_row.addWidget(self.collapse_btn)

        transport_layout.addWidget(self._btn_row_widget)
        main_layout.addWidget(transport_bar)
        self._transport_bar = transport_bar
        self._transport_layout = transport_layout

        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.scrubber_slider.setEnabled(False)

        # ── Cross-cutting connections ──────────────────────────────────
        self.settings_tab.timeline_vis_check.toggled.connect(self._on_timeline_toggle)
        self.settings_tab.piano_vis_check.toggled.connect(self._on_piano_toggle)
        self.settings_tab.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.settings_tab.theme_customize_btn.clicked.connect(self._open_theme_dialog)

        self._collapsed_humanize_check.toggled.connect(self._on_collapsed_humanize_toggled)
        self.playback_tab.select_all_humanization_check.toggled.connect(
            self._sync_collapsed_humanize
        )

        self._switch_page(0)
        self.apply_theme(ThemeManager.get_active_name())

    # ── Navigation ─────────────────────────────────────────────────────

    def _switch_page(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)

    def _on_page_changed(self, index: int) -> None:
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == index)

    # ── Discord footer ────────────────────────────────────────────────

    def _copy_discord_tag(self) -> None:
        QGuiApplication.clipboard().setText("@xiunolove")
        original_text = "  @xiunolove"
        self.discord_btn.setText("  " + I18nManager.t("msg_copied"))
        QTimer.singleShot(1500, lambda: self.discord_btn.setText(original_text))

    # ── Theme ──────────────────────────────────────────────────────────

    def apply_theme(self, name: str) -> None:
        themes = ThemeManager.all_themes()
        theme = themes.get(name)
        if theme is None:
            return
        ThemeManager.set_active_name(name)
        self.main_window.setStyleSheet(generate_stylesheet(theme))
        _c = QColor(theme.text_primary)
        _px = self._collapsed_load_btn.fontMetrics().height()
        self._collapsed_load_btn.setIconSize(QSize(_px, _px))
        self._collapsed_load_btn.setIcon(_make_mdl2_icon("\uE8D6", _c, _px))
        self._collapsed_load_saved_btn.setIconSize(QSize(_px, _px))
        self._collapsed_load_saved_btn.setIcon(_make_mdl2_icon("\uEC50", _c, _px))
        self.timeline_widget.left_hand_color.setNamedColor(theme.accent)
        self.timeline_widget.left_hand_color.setAlpha(210)
        self.timeline_widget.right_hand_color.setNamedColor(theme.accent_play)
        self.timeline_widget.right_hand_color.setAlpha(210)
        self.timeline_widget.bg_color.setNamedColor(theme.bg_primary)
        pedal_q = QColor(theme.pedal_color)
        pedal_q.setAlpha(180)
        self.timeline_widget.pedal_color = pedal_q
        self.timeline_widget.cached_background = None
        self.timeline_widget.update()
        piano_pedal_q = QColor(theme.pedal_color)
        self.piano_widget.pedal_color = piano_pedal_q
        self.piano_widget.update()
        self.guitar_tab.fretboard.bg_color.setNamedColor(theme.bg_primary)
        self.guitar_tab.fretboard.fret_color.setNamedColor(theme.border)
        self.guitar_tab.fretboard.string_color.setNamedColor(theme.text_secondary)
        self.guitar_tab.fretboard.note_color.setNamedColor(theme.accent)
        self.guitar_tab.fretboard.note_glow.setNamedColor(theme.accent_play)
        self.guitar_tab.fretboard.nut_color.setNamedColor(theme.text_primary)
        self.guitar_tab.fretboard.update()

    def _open_theme_dialog(self) -> None:
        from ui.ThemeDialog import ThemeDialog
        dlg = ThemeDialog(self.main_window, self.main_window)
        dlg.theme_applied.connect(self._on_theme_dialog_accepted)
        dlg.exec()

    def _on_theme_dialog_accepted(self, name: str) -> None:
        self.settings_tab.refresh_theme_combo()
        self.apply_theme(name)

    # ── Visualizer helpers ─────────────────────────────────────────────

    def _on_timeline_toggle(self, checked: bool) -> None:
        self.scroll_area.setVisible(checked)
        self._update_visualizer_availability()

    def _on_piano_toggle(self, checked: bool) -> None:
        self.piano_widget.setVisible(checked)
        self.timeline_widget.set_show_pedal(checked)
        self._update_visualizer_availability()

    def _update_visualizer_availability(self) -> None:
        both_off = (not self.settings_tab.timeline_vis_check.isChecked() and
                    not self.settings_tab.piano_vis_check.isChecked())
        self._nav_btns[1].setEnabled(not both_off)
        if both_off and self.tabs.currentIndex() == 1:
            self._switch_page(0)

    def update_progress(self, current_time, total_duration):
        if self.scroll_area.isVisible() and not self.timeline_widget.is_dragging:
            self.timeline_widget.set_position(current_time)
            if total_duration > 0:
                ratio = current_time / total_duration
                cursor_x = ratio * self.timeline_widget.width()
                target_scroll = cursor_x - (self.scroll_area.width() / 2)
                self.scroll_area.horizontalScrollBar().setValue(int(target_scroll))

        if not self._scrubber_dragging and not self.timeline_widget.is_dragging:
            self.scrubber_slider.blockSignals(True)
            if total_duration > 0:
                self.scrubber_slider.setValue(int(current_time / total_duration * 10000))
            self.scrubber_slider.blockSignals(False)

        self.update_time_label(current_time, total_duration)

    def reset_timeline_position(self) -> None:
        self.timeline_widget.current_time = 0.0
        self.scrubber_slider.blockSignals(True)
        self.scrubber_slider.setValue(0)
        self.scrubber_slider.blockSignals(False)

    def update_time_label(self, current, total) -> None:
        def fmt(s):
            m, sec = int(s // 60), int(s % 60)
            return f"{m:02d}:{sec:02d}"
        self.time_label.setText(f"{fmt(current)} / {fmt(total)}")

    # ── Scrubber ───────────────────────────────────────────────────────

    def _on_scrubber_pressed(self):
        self._scrubber_dragging = True

    def _on_scrubber_moved(self, value):
        if self.timeline_widget.total_duration > 0:
            t = (value / 10000.0) * self.timeline_widget.total_duration
            self.timeline_widget.current_time = t
            self.timeline_widget.scrub_position_changed.emit(t)
            self.update_time_label(t, self.timeline_widget.total_duration)

    def _on_scrubber_released(self):
        self._scrubber_dragging = False
        self.timeline_widget.seek_requested.emit(self.timeline_widget.current_time)

    # ── Collapse ───────────────────────────────────────────────────────

    def _toggle_collapsed(self) -> None:
        self._is_collapsed = not self._is_collapsed
        if self._is_collapsed:
            self._expanded_size = self.main_window.size()
            self._body.setVisible(False)
            self._collapsed_strip.setVisible(True)
            self.collapse_btn.setText("▼  " + I18nManager.t("expand"))
            self.collapse_btn.setToolTip(I18nManager.t("tt_expand"))
            self.collapse_btn.setMinimumWidth(0)
            self.collapse_btn.setMaximumWidth(16777215)
            self.collapse_btn.setProperty("strip_mode", True)
            self.collapse_btn.style().unpolish(self.collapse_btn)
            self.collapse_btn.style().polish(self.collapse_btn)
            self._cs_scrubber_layout.addWidget(self.scrubber_slider)
            self._cs_scrubber_layout.addWidget(self.time_label)
            self._cs_playback_layout.addWidget(self.play_button, 1)
            self._cs_playback_layout.addWidget(self.stop_button, 1)
            self._cs_expand_layout.addWidget(self.collapse_btn)
            for btn, glyph in [
                (self.play_button, "\uE768"),
                (self.stop_button, "\uE71A"),
            ]:
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)
                btn.setText(glyph)
                btn.setProperty("icon_mode", True)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            self.save_button.setVisible(False)
            self.reset_button.setVisible(False)
            self._transport_bar.setVisible(False)
            self.main_window.setMinimumWidth(0)
            self.main_window.setMinimumHeight(0)
            self.main_window.adjustSize()
            self.main_window.resize(250, 250)
        else:
            self._body.setVisible(True)
            self._collapsed_strip.setVisible(False)
            self.collapse_btn.setText("▲  " + I18nManager.t("collapse"))
            self.collapse_btn.setToolTip(I18nManager.t("tt_collapse"))
            self.collapse_btn.setProperty("strip_mode", False)
            self.collapse_btn.style().unpolish(self.collapse_btn)
            self.collapse_btn.style().polish(self.collapse_btn)
            self._transport_layout.insertWidget(0, self.scrubber_slider)
            btn_row_layout = self._btn_row_widget.layout()
            btn_row_layout.insertWidget(0, self.play_button)
            btn_row_layout.insertWidget(1, self.stop_button)
            btn_row_layout.insertWidget(3, self.time_label)
            btn_row_layout.addWidget(self.collapse_btn)
            for btn in (self.play_button, self.stop_button):
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)
                btn.setProperty("icon_mode", False)
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            self.stop_button.setText("■  " + I18nManager.t("stop"))
            self.save_button.setVisible(True)
            self.save_button.setText(I18nManager.t("save"))
            self.reset_button.setVisible(True)
            self.reset_button.setText(I18nManager.t("reset"))
            self._transport_bar.setVisible(True)
            self.main_window.setMinimumWidth(820)
            self.main_window.setMinimumHeight(485)
            self.main_window.resize(self._expanded_size)

    # ── Collapsed-strip humanize sync ──────────────────────────────────

    def _on_collapsed_humanize_toggled(self, checked: bool) -> None:
        sel = self.playback_tab.select_all_humanization_check
        sel.blockSignals(True)
        sel.setChecked(checked)
        sel.blockSignals(False)
        self.playback_tab._toggle_all(checked)

    def _sync_collapsed_humanize(self, checked: bool) -> None:
        self._collapsed_humanize_check.blockSignals(True)
        self._collapsed_humanize_check.setChecked(checked)
        self._collapsed_humanize_check.blockSignals(False)

    # ── Public API ─────────────────────────────────────────────────────

    def update_file_label(self, text: str, tooltip: str = "") -> None:
        self.playback_tab.update_file_label(text, tooltip)
        self.guitar_tab.update_file_label(text, tooltip)
        self._collapsed_file_label.setText(text)

    def set_controls_enabled(self, enabled: bool, ignore_if_loaded: bool = False) -> None:
        self.playback_tab.set_groups_enabled(
            enabled,
            skip_playback_humanization=(ignore_if_loaded and enabled)
        )

    def _set_save_enabled(self, val: bool) -> None:
        self.save_button.setEnabled(val)
        self._collapsed_save_btn.setEnabled(val)

    def reset_controls_to_default(self) -> None:
        self.playback_tab.reset_to_default()
        self.guitar_tab.reset_to_default()

    def load_config_to_ui(self, config: dict, save_dir: str) -> None:
        self.playback_tab.load_config(config)
        self.guitar_tab.load_config(config)
        self.settings_tab.load_config(config, save_dir)

    def gather_playback_config(self) -> dict:
        cfg = self.playback_tab.gather_playback_config()
        cfg['use_ai_pedal'] = False
        return cfg

    def gather_app_config(self) -> dict:
        return {
            **self.playback_tab.gather_app_config(),
            **self.guitar_tab.gather_app_config(),
            **self.settings_tab.gather_config()
        }

    def update_enabled_states(self) -> None:
        self.playback_tab.update_enabled_states()
