#!/usr/bin/env python3
import sys
import os
import bisect
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from core.core import MidiParser, KeyMapper, TempoMap
from core.translator import FormatRegistry
from managers.HotkeyManager import HotkeyManager
import webbrowser
from managers.UpdateManager import UpdateChecker
from controllers.PlaybackController import PlaybackController
from managers.ConfigManager import ConfigManager
from managers.i18n import I18nManager
from ui.MainWindowUI import MainWindowUI
from ui.TrackSelectionDialog import TrackSelectionDialog
from ui.LoadSaveDialog import LoadSaveDialog

APP_VERSION = "3.3"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Teto Midi v{APP_VERSION}")
        self.setMinimumWidth(820)
        self.setMinimumHeight(485)
        self.resize(self.minimumWidth(), self.minimumHeight())

        # Set specific Icon base execution path
        base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Instantiate Domains
        self.config_manager = ConfigManager()

        # Load config early to set language before UI builds
        loaded_cfg = self.config_manager.load()
        lang = loaded_cfg.get('language', 'en') if loaded_cfg else 'en'
        I18nManager.set_language(lang)

        self.ui = MainWindowUI(self)
        self.playback_controller = PlaybackController()
        self.hotkey_manager = HotkeyManager()

        # Global Application States
        self.loaded_save_data = None
        self.loaded_save_filename = None
        self.selected_tracks_info = None
        self.current_notes = []
        self._note_start_times = []
        self.total_song_duration_sec = 1.0
        self._max_note_duration = 0.0
        self.current_pedal_intervals = []

        # Guitar mode state
        self._guitar_file_loaded = False
        self._guitar_selected_tracks = None

        self._bind_signals()

        # Load initialization data
        if loaded_cfg:
            self.ui.load_config_to_ui(loaded_cfg, self.config_manager.save_dir)
            self.ui.settings_tab.hk_label.setText(
                f"{I18nManager.t('hotkey')}: {self.hotkey_manager._format_key_string(self.hotkey_manager.current_key)}"
            )
        else:
            self.ui.reset_controls_to_default()

        self._update_checker = UpdateChecker(APP_VERSION)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()

    def _bind_signals(self):
        # UI controls bound strictly to Execution/Router logic
        self.ui.play_button.clicked.connect(self.handle_play)
        self.ui.stop_button.clicked.connect(self.handle_stop)
        self.ui.save_button.clicked.connect(self.handle_save)
        self.ui.reset_button.clicked.connect(self.ui.reset_controls_to_default)

        # Playback tab
        self.ui.playback_tab.browse_button.clicked.connect(self.select_file)
        self.ui.playback_tab.load_saved_btn.clicked.connect(self.open_load_dialog)

        # Guitar tab (NEW)
        self.ui.guitar_tab.browse_button.clicked.connect(self.select_file_guitar)
        self.ui.guitar_tab.load_saved_btn.clicked.connect(self.open_load_dialog)
        self.ui.guitar_tab.play_button.clicked.connect(self.handle_guitar_play)
        self.ui.guitar_tab.stop_button.clicked.connect(self.handle_stop)

        # Settings
        self.ui.settings_tab.save_browse_btn.clicked.connect(self._browse_save_dir)
        self.ui._collapsed_load_btn.clicked.connect(self.select_file)
        self.ui._collapsed_load_saved_btn.clicked.connect(self.open_load_dialog)
        self.ui._collapsed_save_btn.clicked.connect(self.handle_save)
        self.ui.settings_tab.hk_btn.clicked.connect(self._change_hotkey)
        self.ui.settings_tab.check_update_btn.clicked.connect(self._manual_check_update)

        # Language change
        self.ui.settings_tab.lang_combo.currentIndexChanged.connect(self._on_language_changed)

        # View manipulations bound to Window behavior
        self.ui.collapse_btn.clicked.connect(self._sync_play_button)
        self.ui.settings_tab.always_top_check.toggled.connect(self._toggle_always_on_top)
        self.ui.settings_tab.opacity_slider.valueChanged.connect(self._change_opacity)

        # Settings-tab persistence
        self.ui.settings_tab.always_top_check.toggled.connect(self._save_config)
        self.ui.settings_tab.opacity_slider.valueChanged.connect(self._save_config)
        self.ui.settings_tab.timeline_vis_check.toggled.connect(self._save_config)
        self.ui.settings_tab.piano_vis_check.toggled.connect(self._save_config)
        self.ui.settings_tab.lang_combo.currentIndexChanged.connect(self._save_config)

        # Translator tab
        self.ui.translator_tab.play_sheet_requested.connect(self._on_play_sheet)
        self.ui.translator_tab.export_requested.connect(self._on_export_sheet)

        # Edit MIDI tab (NEW)
        self.ui.edit_midi_tab.test_requested.connect(self._on_edit_midi_test)

        # Timeline logic bridging
        self.ui.timeline_widget.seek_requested.connect(self._on_timeline_seek)
        self.ui.timeline_widget.scrub_position_changed.connect(self._on_visual_scrub)

        # External IO bridging
        self.hotkey_manager.toggle_requested.connect(self.toggle_playback_state)
        self.hotkey_manager.bound_updated.connect(self._on_hotkey_bound)
        self.hotkey_manager.listener_unavailable.connect(self._on_hotkey_unavailable)
        if not self.hotkey_manager.available:
            # The listener may have already failed during HotkeyManager.__init__(),
            # before this connection existed — surface it now instead of losing it.
            self._on_hotkey_unavailable(
                "Global hotkey listener unavailable at startup. "
                "The F6-style hotkey won't work, but the on-screen Play/Stop "
                "buttons still function normally."
            )

        # System Logic bridging to the View representations
        self.playback_controller.status_updated.connect(self.ui.log_output.append)
        self.playback_controller.progress_updated.connect(self.update_progress)
        self.playback_controller.playback_finished.connect(self.on_playback_finished)
        self.playback_controller.visualizer_updated.connect(lambda p: self.ui.piano_widget.set_active_pitches(p))
        self.playback_controller.pedal_updated.connect(self.ui.piano_widget.set_pedal_active)
        self.playback_controller.auto_paused.connect(self._on_auto_paused)
        self.playback_controller.error_occurred.connect(self.show_error_dialog)
        self.playback_controller.timeline_data_ready.connect(self._on_timeline_data_ready)
        self.playback_controller.pedal_data_ready.connect(self._on_pedal_data_ready)
        self.playback_controller.save_successful.connect(self._on_save_successful)
        self.playback_controller.save_failed.connect(self._on_save_failed)

        # Guitar visualizer bridge (NEW)
        self.playback_controller.visualizer_updated.connect(self._on_guitar_notes_update)

    # --- Guitar Mode (NEW) ---
    def _on_guitar_notes_update(self, pitches: list):
        """Forward active pitches to guitar fretboard visualizer."""
        notes = [(p, 100) for p in pitches]
        self.ui.guitar_tab.fretboard.set_active_notes(notes)
        # Update chord label with pitch count
        if pitches:
            self.ui.guitar_tab.note_info_label.setText(
                f"{len(pitches)} note(s) active"
            )
        else:
            self.ui.guitar_tab.note_info_label.setText("—")

    def select_file_guitar(self):
        """File selection specifically for Guitar mode."""
        if self.playback_controller.is_playing() or self.playback_controller.is_paused():
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, I18nManager.t("browse"), "", "MIDI Files (*.mid *.midi)"
        )
        if filepath:
            self.loaded_save_data = None
            self.loaded_save_filename = None
            self.ui.guitar_tab.update_file_label(os.path.basename(filepath), filepath)
            self.ui.log_output.append(f"{I18nManager.t('status_selected_file')}: {filepath}")
            self._parse_and_select_tracks_guitar(filepath)

    def _parse_and_select_tracks_guitar(self, filepath):
        self.ui.log_output.append(I18nManager.t("status_parsing"))
        try:
            tracks, tempo_map = MidiParser.parse_structure(filepath, 1.0, None)
        except Exception as e:
            QMessageBox.critical(
                self, I18nManager.t("msg_save_error"),
                f"{I18nManager.t('msg_parse_error')}:\n{e}"
            )
            return

        dialog = TrackSelectionDialog(tracks, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._guitar_selected_tracks = dialog.get_selection()
            self.parsed_tempo_map = tempo_map
            self.ui.log_output.append(
                f"{I18nManager.t('status_selected_tracks')} {len(self._guitar_selected_tracks)}"
            )
            self.ui.guitar_tab.play_button.setEnabled(True)
            self._guitar_file_loaded = True
        else:
            self.ui.log_output.append(I18nManager.t("status_cancelled"))
            self._guitar_selected_tracks = None
            self.ui.guitar_tab.play_button.setEnabled(False)
            self._guitar_file_loaded = False

    def handle_guitar_play(self):
        """Start playback in Guitar mode."""
        if self.playback_controller.is_playing() or self.playback_controller.is_paused():
            self.toggle_playback_state()
            return

        if not self._guitar_file_loaded or not self._guitar_selected_tracks:
            QMessageBox.warning(
                self, I18nManager.t("msg_no_notes"),
                I18nManager.t("msg_no_tracks")
            )
            return

        # Build guitar config
        guitar_cfg = self.ui.guitar_tab.gather_guitar_config()

        # Merge with playback config but force guitar instrument
        config = self.ui.gather_playback_config()
        config.update(guitar_cfg)
        config['instrument'] = 'guitar'
        config['use_88_key_layout'] = False

        self.playback_controller.play(config, self._guitar_selected_tracks)

        self.ui.guitar_tab.set_controls_enabled(False)
        self.ui.guitar_tab.play_button.setEnabled(True)
        self.ui.guitar_tab.stop_button.setEnabled(True)
        self._sync_play_button()

    # --- Language ---
    def _on_language_changed(self):
        lang = self.ui.settings_tab.lang_combo.currentData()
        if lang != I18nManager.get_language():
            I18nManager.set_language(lang)
            QMessageBox.information(
                self, I18nManager.t("language"),
                "Language changed. Please restart the app to apply fully.\n"
                "Ngôn ngữ đã thay đổi. Vui lòng khởi động lại ứng dụng để áp dụng đầy đủ."
            )

    # --- Windows Specific GUI Modifications ---
    def _toggle_always_on_top(self, checked):
        flags = self.windowFlags()
        if checked: self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else: self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _change_opacity(self, value):
        self.setWindowOpacity(value / 100.0)

    # --- Standard Execution Behaviors ---
    def _save_config(self):
        config_data = self.ui.gather_app_config()
        self.config_manager.save(config_data)

    def _browse_save_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, I18nManager.t("browse"), self.config_manager.save_dir
        )
        if path:
            self.config_manager.set_save_dir(path)
            self.ui.settings_tab.save_path_input.setText(path)
            self._save_config()

    def _change_hotkey(self):
        QMessageBox.information(
            self, I18nManager.t("hotkey"), I18nManager.t("msg_bind_key")
        )
        self.ui.settings_tab.hk_btn.setText(I18nManager.t("msg_listening"))
        self.ui.settings_tab.hk_btn.setEnabled(False)
        self.hotkey_manager.start_binding()

    def _on_hotkey_bound(self, key_str):
        self.ui.settings_tab.hk_label.setText(
            f"{I18nManager.t('hotkey')}: {key_str}"
        )
        self.ui.settings_tab.hk_btn.setText(I18nManager.t("change"))
        self.ui.settings_tab.hk_btn.setEnabled(True)
        self._sync_play_button()

    def _on_hotkey_unavailable(self, message: str):
        # Don't block app startup with a modal — just log it and let the
        # user notice via the status/debug output. The rest of the app
        # (Play/Stop buttons, file loading, etc.) still works fine even
        # without a global hotkey listener.
        try:
            self.ui.log_output.append(f"[Hotkey] {message}")
        except Exception:
            pass
        # If the user had just clicked "Change" and the button is stuck
        # showing "Listening...", restore it instead of leaving it disabled.
        if not self.ui.settings_tab.hk_btn.isEnabled():
            self.ui.settings_tab.hk_btn.setText(I18nManager.t("change"))
            self.ui.settings_tab.hk_btn.setEnabled(True)

    def _sync_play_button(self):
        """Single authoritative update for the play button."""
        key_str = self.hotkey_manager._format_key_string(self.hotkey_manager.current_key)
        t = I18nManager.t
        if self.ui._is_collapsed:
            if self.playback_controller.is_paused():
                self.ui.play_button.setText("\uE768")
                self.ui.play_button.setToolTip(f"{t('resume')} ({key_str})")
            elif self.playback_controller.is_playing():
                self.ui.play_button.setText("\uE769")
                self.ui.play_button.setToolTip(f"{t('pause')} ({key_str})")
            else:
                self.ui.play_button.setText("\uE768")
                self.ui.play_button.setToolTip(f"{t('play')} ({key_str})")
        else:
            if self.playback_controller.is_paused():
                self.ui.play_button.setText(f"{t('resume')} ({key_str})")
            elif self.playback_controller.is_playing():
                self.ui.play_button.setText(f"{t('pause')} ({key_str})")
            else:
                self.ui.play_button.setText(f"{t('play')} ({key_str})")
            self.ui.play_button.setToolTip(t("tt_play"))

    def toggle_playback_state(self):
        if not self.playback_controller.is_paused():
            self.ui.piano_widget.clear()
            self.ui.guitar_tab.fretboard.clear()

        if self.playback_controller.is_playing() or self.playback_controller.is_paused():
            self.playback_controller.toggle_pause()
            self._sync_play_button()
            if not self.playback_controller.is_paused():
                current_t = self.ui.timeline_widget.current_time
                self._on_visual_scrub(current_t)
        elif self.ui.play_button.isEnabled():
            self.handle_play()

    def _on_auto_paused(self):
        self._sync_play_button()
        self.ui.piano_widget.clear()
        self.ui.guitar_tab.fretboard.clear()
        self.ui.stop_button.setEnabled(True)

    def _on_timeline_seek(self, time):
        self.ui.log_output.append(f"{I18nManager.t('status_seeking')} {time:.2f}s...")
        self.playback_controller.seek(time)

    def _on_visual_scrub(self, time):
        active_pitches = set()
        lo = bisect.bisect_left(self._note_start_times, time - self._max_note_duration)
        hi = bisect.bisect_right(self._note_start_times, time)
        for note in self.current_notes[lo:hi]:
            if note.end_time > time:
                active_pitches.add(note.pitch)
        self.ui.piano_widget.set_active_pitches(list(active_pitches))
        self.ui.guitar_tab.fretboard.set_active_notes([(p, 100) for p in active_pitches])
        pedal_down = any(s <= time < e for s, e in self.current_pedal_intervals)
        self.ui.piano_widget.set_pedal_active(pedal_down)
        self.ui.update_time_label(time, self.total_song_duration_sec)

    def _on_timeline_data_ready(self, notes, total_dur, tempo_map):
        self.current_notes = notes
        self._note_start_times = [n.start_time for n in notes]
        self._max_note_duration = max((n.duration for n in notes), default=0.0)
        self.total_song_duration_sec = total_dur
        self.ui.timeline_widget.set_data(notes, total_dur, tempo_map)
        self.ui.reset_timeline_position()

    def _on_pedal_data_ready(self, intervals: list):
        self.current_pedal_intervals = intervals
        self.ui.timeline_widget.set_pedal_intervals(intervals)

    def update_progress(self, current_time):
        self.ui.update_progress(current_time, self.total_song_duration_sec)

    # --- Loading & File State Dialogs ---
    def select_file(self):
        if self.playback_controller.is_playing() or self.playback_controller.is_paused():
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, I18nManager.t("browse"), "", "MIDI Files (*.mid *.midi)"
        )
        if filepath:
            self.loaded_save_data = None
            self.loaded_save_filename = None
            self.ui.playback_tab.playback_group.setEnabled(True)
            self.ui.playback_tab.humanization_group.setEnabled(True)
            self.ui.update_file_label(os.path.basename(filepath), filepath)
            self.ui.log_output.append(f"{I18nManager.t('status_selected_file')}: {filepath}")
            self._parse_and_select_tracks(filepath)

    def open_load_dialog(self):
        dialog = LoadSaveDialog(self.config_manager.save_dir, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_file, data = dialog.get_selected_data()
            if selected_file and data:
                self.loaded_save_data = data
                self.loaded_save_filename = os.path.basename(selected_file)

                self.ui.update_file_label(self.loaded_save_filename, selected_file)
                self.ui.playback_tab.playback_group.setEnabled(False)
                self.ui.playback_tab.humanization_group.setEnabled(False)
                self.ui._set_save_enabled(False)
                self.ui.play_button.setEnabled(True)
                self.ui.scrubber_slider.setEnabled(True)
                self.ui.log_output.append(
                    f"{I18nManager.t('status_loaded_save')}: {self.loaded_save_filename}"
                )

    def _parse_and_select_tracks(self, filepath):
        self.ui.log_output.append(I18nManager.t("status_parsing"))
        try:
            tracks, tempo_map = MidiParser.parse_structure(filepath, 1.0, None)
        except Exception as e:
            QMessageBox.critical(
                self, I18nManager.t("msg_save_error"),
                f"{I18nManager.t('msg_parse_error')}:\n{e}"
            )
            return

        dialog = TrackSelectionDialog(tracks, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_tracks_info = dialog.get_selection()
            self.parsed_tempo_map = tempo_map 
            self.ui.log_output.append(
                f"{I18nManager.t('status_selected_tracks')} {len(self.selected_tracks_info)}"
            )
            self.ui.play_button.setEnabled(True)
            self.ui.scrubber_slider.setEnabled(True)
            self.ui._set_save_enabled(True)
        else:
            self.ui.log_output.append(I18nManager.t("status_cancelled"))
            self.selected_tracks_info = None
            self.ui.play_button.setEnabled(False)
            self.ui.scrubber_slider.setEnabled(False)
            self.ui._set_save_enabled(False)

    # --- Translator ---
    def _on_play_sheet(self, text: str, format_name: str, bpm: int, humanize: bool):
        if self.playback_controller.is_playing() or self.playback_controller.is_paused():
            return

        fmt = FormatRegistry.get(format_name)
        if not fmt:
            QMessageBox.critical(
                self, I18nManager.t("msg_unknown_format"),
                f"{I18nManager.t('msg_unknown_format')}: {format_name}"
            )
            return

        use_88 = self.ui.playback_tab.use_88_key_check.isChecked()
        instrument = self.ui.playback_tab.instrument_combo.currentText().lower()
        key_mapper = KeyMapper(use_88_key_layout=use_88, instrument=instrument)

        try:
            notes = fmt.parse(text, float(bpm), key_mapper)
        except Exception as e:
            QMessageBox.critical(
                self, I18nManager.t("msg_parse_error"),
                f"{I18nManager.t('msg_parse_error')}:\n{e}"
            )
            return

        if not notes:
            QMessageBox.warning(self, I18nManager.t("msg_no_notes"), I18nManager.t("msg_no_notes"))
            return

        tempo_us = int(60_000_000 / bpm)
        tempo_map = TempoMap([(0, tempo_us)], [])

        if humanize:
            config = self.ui.gather_playback_config()
        else:
            config = {
                'use_88_key_layout': use_88, 'instrument': instrument, 'debug_mode': False,
                'countdown': False, 'pedal_style': 'none', 'simulate_hands': False,
                'vary_velocity': False, 'enable_chord_roll': False, 'vary_timing': False,
                'timing_variance': 0.01, 'vary_articulation': False, 'articulation': 0.95,
                'enable_drift_correction': False, 'drift_decay_factor': 0.25,
                'enable_mistakes': False, 'mistake_chance': 0.0,
                'enable_tempo_sway': False, 'tempo_sway_intensity': 0.0,
                'invert_tempo_sway': False, 'use_ai_pedal': False,
            }

        self.ui.log_output.append(
            f"{I18nManager.t('status_importing')}: {len(notes)} notes at {bpm} BPM ({format_name})"
        )
        self.playback_controller.play_from_notes(config, notes, tempo_map)
        self.ui.set_controls_enabled(False)
        self.ui.play_button.setEnabled(True)
        self.ui.stop_button.setEnabled(True)
        self.ui.scrubber_slider.setEnabled(True)
        self._sync_play_button()
        if self.ui._nav_btns[1].isEnabled():
            self.ui.tabs.setCurrentIndex(1)

    def _on_export_sheet(self, format_name: str):
        if not self.current_notes:
            QMessageBox.warning(self, I18nManager.t("msg_no_notes"), I18nManager.t("msg_no_midi"))
            return

        fmt = FormatRegistry.get(format_name)
        if not fmt:
            QMessageBox.critical(
                self, I18nManager.t("msg_unknown_format"),
                f"{I18nManager.t('msg_unknown_format')}: {format_name}"
            )
            return

        use_88 = self.ui.playback_tab.use_88_key_check.isChecked()
        instrument = self.ui.playback_tab.instrument_combo.currentText().lower()
        key_mapper = KeyMapper(use_88_key_layout=use_88, instrument=instrument)

        try:
            text = fmt.serialize(self.current_notes, key_mapper, self.parsed_tempo_map)
        except Exception as e:
            QMessageBox.critical(
                self, I18nManager.t("msg_export_error"),
                f"{I18nManager.t('msg_export_error')}:\n{e}"
            )
            return

        self.ui.translator_tab.set_export_text(text)
        self.ui.log_output.append(
            f"{I18nManager.t('status_exported')}: {format_name} ({len(text.splitlines())} lines)"
        )

    # --- Edit MIDI tab (NEW) ---
    def _on_edit_midi_test(self, notes: list, bpm: float):
        """Send the piano-roll's current notes straight into the normal
        playback/keystroke pipeline, so the user can test what they just
        drew/edited without exporting a file first."""
        if self.playback_controller.is_playing() or self.playback_controller.is_paused():
            QMessageBox.warning(
                self, I18nManager.t("msg_no_tracks"),
                "Please stop the current playback before testing the edited MIDI."
            )
            return
        if not notes:
            QMessageBox.warning(self, I18nManager.t("msg_no_notes"), I18nManager.t("msg_no_notes"))
            return

        tempo_us = int(60_000_000 / max(1.0, bpm))
        tempo_map = TempoMap([(0, tempo_us)], [])
        config = self.ui.gather_playback_config()

        self.loaded_save_data = None
        self.ui.log_output.append(
            f"Testing edited MIDI: {len(notes)} note(s) at {bpm} BPM"
        )
        self.playback_controller.play_from_notes(config, notes, tempo_map)
        self.ui.set_controls_enabled(False)
        self.ui.play_button.setEnabled(True)
        self.ui.stop_button.setEnabled(True)
        self.ui.scrubber_slider.setEnabled(True)
        self._sync_play_button()
        self.ui.tabs.setCurrentIndex(0)

    def show_error_dialog(self, error_message: str):
        self.ui.log_output.append(I18nManager.t("msg_error_playback"))
        QMessageBox.critical(self, I18nManager.t("msg_hardware_error"), error_message)

    # --- Core Executions ---
    def handle_save(self):
        config = self.ui.gather_playback_config()
        if not self.selected_tracks_info:
            QMessageBox.warning(
                self, I18nManager.t("msg_no_notes"), I18nManager.t("msg_no_tracks")
            )
            return

        self._save_config()
        original_filename = os.path.basename(self.ui.playback_tab.file_path_label.toolTip())
        self.playback_controller.save(
            config, self.selected_tracks_info, self.config_manager.save_dir, original_filename
        )

    def _on_save_successful(self, filepath: str, message: str):
        QMessageBox.information(
            self, I18nManager.t("msg_save_success"), f"{message}\n{filepath}"
        )

    def _on_save_failed(self, error_message: str):
        QMessageBox.critical(self, I18nManager.t("msg_save_error"), error_message)

    def handle_play(self):
        if self.playback_controller.is_playing() or self.playback_controller.is_paused(): 
            self.toggle_playback_state()
            return

        if self.loaded_save_data:
            self.playback_controller.play_from_save(self.loaded_save_data)
        else:
            config = self.ui.gather_playback_config()
            if not self.selected_tracks_info:
                QMessageBox.warning(
                    self, I18nManager.t("msg_no_notes"), I18nManager.t("msg_no_tracks")
                )
                return
            self.playback_controller.play(config, self.selected_tracks_info)

        self.ui.set_controls_enabled(False, bool(self.loaded_save_data))
        self.ui.play_button.setEnabled(True)
        self.ui.stop_button.setEnabled(True)
        self._sync_play_button()
        if self.ui._nav_btns[1].isEnabled():
            self.ui.tabs.setCurrentIndex(1)

    def handle_stop(self):
        self.playback_controller.stop()

    def on_playback_finished(self):
        self.ui.log_output.append(
            I18nManager.t("status_playback_finished") + "\n" + "="*50 + "\n"
        )
        self.ui.set_controls_enabled(True, bool(self.loaded_save_data))
        self.ui.stop_button.setEnabled(False)
        self.ui.guitar_tab.stop_button.setEnabled(False)
        self.ui.guitar_tab.set_controls_enabled(True)
        self._sync_play_button()
        self.ui.piano_widget.set_pedal_active(False)
        self.ui.guitar_tab.fretboard.clear()

    # --- Update ---
    def _manual_check_update(self):
        btn = self.ui.settings_tab.check_update_btn
        btn.setEnabled(False)
        btn.setText(I18nManager.t("msg_listening"))
        self._manual_checker = UpdateChecker(APP_VERSION, force=True)
        self._manual_checker.update_available.connect(self._on_update_available)
        self._manual_checker.update_available.connect(lambda *_: self._reset_update_btn())
        self._manual_checker.no_update.connect(self._on_no_update)
        self._manual_checker.check_failed.connect(self._on_check_failed)
        self._manual_checker.start()

    def _reset_update_btn(self):
        btn = self.ui.settings_tab.check_update_btn
        btn.setEnabled(True)
        btn.setText(I18nManager.t("check_updates"))

    def _on_no_update(self):
        self._reset_update_btn()
        QMessageBox.information(
            self, I18nManager.t("msg_up_to_date"),
            f"Teto Midi v{APP_VERSION} is the latest version."
        )

    def _on_check_failed(self):
        self._reset_update_btn()
        QMessageBox.warning(
            self, I18nManager.t("msg_update_failed"),
            "Could not reach GitHub.\nPlease check your internet connection."
        )

    def _on_update_available(self, latest_tag: str, releases_url: str):
        reply = QMessageBox.question(
            self, "Update Available",
            f"Update available to {latest_tag}. Would you like to open the download page?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(releases_url)

    def closeEvent(self, event):
        self._update_checker.quit()
        self._save_config()
        self.playback_controller.shutdown()
        self.ui.edit_midi_tab.shutdown()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
