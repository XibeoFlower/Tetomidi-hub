"""
Internationalization (i18n) module for Teto Midi.
Supports English (default) and Vietnamese (Tiếng Việt) with full diacritics.
"""

from dataclasses import dataclass, field
from typing import Dict
import json
from pathlib import Path


@dataclass
class TranslationStrings:
    """All UI strings that need translation."""
    # Navigation
    nav_playback: str = "Playback"
    nav_visualizer: str = "Visualizer"
    nav_translator: str = "Translator"
    nav_settings: str = "Settings"
    nav_debug: str = "Debug"
    nav_guitar: str = "Guitar"

    # Playback Tab
    midi_file: str = "MIDI File"
    no_file_selected: str = "No file selected."
    browse: str = "Browse…"
    load_save: str = "Load Save"
    playback: str = "Playback"
    tempo: str = "Tempo"
    pedal: str = "Pedal"
    instrument: str = "Instrument"
    piano: str = "Piano"
    guitar: str = "Guitar"
    transpose: str = "Transpose"
    key_layout_88: str = "88-Key Layout"
    countdown: str = "Countdown"
    debug_output: str = "Debug Output"

    # Humanization
    humanization: str = "Humanization"
    all_humanize: str = "All"
    simulate_hands: str = "Simulate Hands"
    chord_roll: str = "Chord Roll"
    vary_timing: str = "Vary Timing"
    vary_articulation: str = "Vary Articulation"
    hand_drift: str = "Hand Drift"
    mistakes: str = "Mistakes"
    tempo_sway: str = "Tempo Sway"
    invert_sway: str = "Invert Sway"

    # Settings Tab
    save_path: str = "Save Path"
    hotkey: str = "Hotkey"
    change: str = "Change"
    overlay: str = "Overlay"
    always_on_top: str = "Always on Top"
    opacity: str = "Opacity"
    check_updates: str = "Check for updates"
    visualizer: str = "Visualizer"
    timeline: str = "Timeline"
    piano_keys: str = "Piano Keys"
    theme: str = "Theme"
    customize: str = "Customize…"
    language: str = "Language"

    # Transport
    play: str = "Play"
    resume: str = "Resume"
    pause: str = "Pause"
    stop: str = "Stop"
    save: str = "Save"
    reset: str = "Reset"
    collapse: str = "Collapse"
    expand: str = "Expand"

    # Tooltips
    tt_browse: str = "Open a MIDI file to play"
    tt_load_save: str = "Load a previously saved humanized performance"
    tt_tempo: str = "Playback speed as a percentage of the original tempo"
    tt_countdown: str = "Show a 3-second countdown before playback begins"
    tt_debug: str = "Print verbose event logs to the Debug tab during playback"
    tt_humanize_all: str = "Enable or disable all humanization options at once"
    tt_simulate_hands: str = "Assign notes to left/right hand and limit simultaneous finger usage"
    tt_chord_roll: str = "Slightly stagger the notes within each chord"
    tt_vary_timing: str = "Add random timing offsets to note events (in seconds)"
    tt_vary_articulation: str = "Randomize note hold duration"
    tt_hand_drift: str = "Simulate gradual timing drift between hands"
    tt_mistakes: str = "Randomly skip notes to simulate human errors"
    tt_tempo_sway: str = "Apply a sinusoidal tempo variation across the song"
    tt_invert_sway: str = "Invert the phase of the tempo sway curve"
    tt_always_top: str = "Keep this window above all other windows"
    tt_opacity: str = "Adjust window transparency (20–100%)"
    tt_timeline: str = "Show the piano-roll timeline in the Visualizer tab"
    tt_piano_vis: str = "Show the piano key visualizer in the Visualizer tab"
    tt_theme: str = "Switch the application colour theme"
    tt_customize: str = "Open the theme editor"
    tt_language: str = "Switch application language (requires restart)"
    tt_save_path: str = "Directory where humanized performance saves are stored"
    tt_browse_save: str = "Choose where to save humanized performance files"
    tt_hotkey: str = "Click to bind a new hotkey for toggling playback"
    tt_check_update: str = "Check GitHub for a newer version"
    tt_play: str = "Start, pause, or resume playback"
    tt_stop: str = "Stop playback and reset to the beginning"
    tt_save_transport: str = "Save the current humanized performance"
    tt_reset: str = "Reset all settings to their default values"
    tt_collapse: str = "Collapse to mini mode"
    tt_expand: str = "Restore full window"

    # Pedal options
    pedal_auto: str = "Auto (Default)"
    pedal_ai: str = "PedalAI"
    pedal_harmonic: str = "Harmonic"
    pedal_rhythmic: str = "Rhythmic"
    pedal_none: str = "None"

    # Messages
    msg_bind_key: str = "Press the key you want to bind now."
    msg_listening: str = "Listening…"
    msg_copied: str = "Copied!"
    msg_no_tracks: str = "Please select a MIDI file and choose tracks first."
    msg_save_success: str = "Save Successful"
    msg_save_error: str = "Save Error"
    msg_up_to_date: str = "Up to Date"
    msg_update_failed: str = "Update Check Failed"
    msg_parse_error: str = "Failed to parse MIDI"
    msg_no_notes: str = "No playable notes were found"
    msg_unknown_format: str = "No handler found for format"
    msg_export_error: str = "Failed to generate sheet"
    msg_no_midi: str = "Load and prepare a MIDI file first."
    msg_hardware_error: str = "Hardware/Execution Failure"
    msg_error_playback: str = "Playback thread terminated unexpectedly"

    # Status
    status_parsing: str = "Parsing MIDI structure…"
    status_selected_tracks: str = "Tracks selected:"
    status_cancelled: str = "Track selection cancelled."
    status_playback_finished: str = "Playback process finished."
    status_seeking: str = "Seeking to"
    status_importing: str = "Importing sheet"
    status_exported: str = "Sheet exported"
    status_selected_file: str = "Selected file"
    status_loaded_save: str = "Loaded save file"

    # Translator
    translator_import: str = "Import"
    translator_export: str = "Export"
    translator_format: str = "Format"
    translator_paste_sheet: str = "Paste sheet text"
    translator_bpm: str = "BPM"
    translator_humanize: str = "Humanize"
    translator_play_sheet: str = "Play Sheet"

    # Discord
    discord_tooltip: str = "Discord: @xiunolove — click to copy"


# ── Vietnamese Translation (Tiếng Việt đầy đủ dấu) ─────────────────────────

VIETNAMESE = TranslationStrings(
    nav_playback="Phát Nhạc",
    nav_visualizer="Trực Quan",
    nav_translator="Dịch Bản Nhạc",
    nav_settings="Cài Đặt",
    nav_debug="Gỡ Lỗi",
    nav_guitar="Guitar",

    midi_file="Tập Tin MIDI",
    no_file_selected="Chưa chọn tập tin.",
    browse="Duyệt…",
    load_save="Tải Bản Lưu",
    playback="Phát Lại",
    tempo="Tốc Độ",
    pedal="Bàn Đạp",
    instrument="Nhạc Cụ",
    piano="Piano",
    guitar="Guitar",
    transpose="Chuyển Giọng",
    key_layout_88="Bố Trí 88 Phím",
    countdown="Đếm Ngược",
    debug_output="Ghi Log Gỡ Lỗi",

    humanization="Nhân Bản Hóa",
    all_humanize="Tất Cả",
    simulate_hands="Mô Phỏng Bàn Tay",
    chord_roll="Lăn Hợp Âm",
    vary_timing="Thay Đổi Thời Gian",
    vary_articulation="Thay Đổi Cách Diễn",
    hand_drift="Trôi Bàn Tay",
    mistakes="Sai Lầm",
    tempo_sway="Lắc Nhịp Điệu",
    invert_sway="Đảo Ngược Lắc",

    save_path="Đường Dẫn Lưu",
    hotkey="Phím Tắt",
    change="Thay Đổi",
    overlay="Lớp Phủ",
    always_on_top="Luôn Ở Trên Cùng",
    opacity="Độ Trong Suốt",
    check_updates="Kiểm Tra Cập Nhật",
    visualizer="Trực Quan",
    timeline="Dòng Thời Gian",
    piano_keys="Phím Piano",
    theme="Giao Diện",
    customize="Tùy Chỉnh…",
    language="Ngôn Ngữ",

    play="Phát",
    resume="Tiếp Tục",
    pause="Tạm Dừng",
    stop="Dừng",
    save="Lưu",
    reset="Đặt Lại",
    collapse="Thu Nhỏ",
    expand="Mở Rộng",

    tt_browse="Mở tập tin MIDI để phát",
    tt_load_save="Tải bản lưu hiệu suất đã nhân bản hóa trước đó",
    tt_tempo="Tốc độ phát lại theo phần trăm của tempo gốc",
    tt_countdown="Hiển thị đếm ngược 3 giây trước khi phát",
    tt_debug="In log chi tiết vào tab Gỡ Lỗi trong khi phát",
    tt_humanize_all="Bật hoặc tắt tất cả tùy chọn nhân bản hóa cùng lúc",
    tt_simulate_hands="Phân bổ nốt cho tay trái/phải và giới hạn ngón tay đồng thời",
    tt_chord_roll="Làm trễ nhẹ các nốt trong hợp âm để mô phỏng lăn ngón",
    tt_vary_timing="Thêm độ lệch thời gian ngẫu nhiên cho sự kiện nốt (tính bằng giây)",
    tt_vary_articulation="Ngẫu nhiên hóa thời lượng giữ nốt",
    tt_hand_drift="Mô phỏng độ trôi thời gian dần dần giữa hai bàn tay",
    tt_mistakes="Bỏ qua nốt ngẫu nhiên để mô phỏng lỗi của con người",
    tt_tempo_sway="Áp dụng biến thiên tempo hình sin xuyên suốt bài hát",
    tt_invert_sway="Đảo ngược pha của đường cong lắc tempo",
    tt_always_top="Giữ cửa sổ này luôn ở trên các cửa sổ khác",
    tt_opacity="Điều chỉnh độ trong suốt cửa sổ (20–100%)",
    tt_timeline="Hiển thị dòng thời gian piano-roll trong tab Trực Quan",
    tt_piano_vis="Hiển thị trực quan phím piano trong tab Trực Quan",
    tt_theme="Chuyển đổi giao diện màu của ứng dụng",
    tt_customize="Mở trình chỉnh sửa giao diện",
    tt_language="Chuyển đổi ngôn ngữ ứng dụng (cần khởi động lại)",
    tt_save_path="Thư mục lưu trữ các bản lưu hiệu suất đã nhân bản hóa",
    tt_browse_save="Chọn nơi lưu tập tin hiệu suất",
    tt_hotkey="Nhấn để gán phím tắt mới cho phát/dừng",
    tt_check_update="Kiểm tra phiên bản mới trên GitHub",
    tt_play="Bắt đầu, tạm dừng hoặc tiếp tục phát lại",
    tt_stop="Dừng phát và quay về đầu",
    tt_save_transport="Lưu hiệu suất nhân bản hóa hiện tại",
    tt_reset="Đặt lại tất cả cài đặt về mặc định",
    tt_collapse="Thu nhỏ về chế độ mini",
    tt_expand="Khôi phục cửa sổ đầy đủ",

    pedal_auto="Tự Động (Mặc Định)",
    pedal_ai="Trí Tuệ Nhân Tạo",
    pedal_harmonic="Hài Hòa",
    pedal_rhythmic="Nhịp Điệu",
    pedal_none="Không",

    msg_bind_key="Nhấn phím bạn muốn gán ngay bây giờ.",
    msg_listening="Đang Lắng Nghe…",
    msg_copied="Đã Sao Chép!",
    msg_no_tracks="Vui lòng chọn tập tin MIDI và chọn track trước.",
    msg_save_success="Lưu Thành Công",
    msg_save_error="Lỗi Lưu",
    msg_up_to_date="Đã Cập Nhật",
    msg_update_failed="Kiểm Tra Cập Nhật Thất Bại",
    msg_parse_error="Không thể phân tích MIDI",
    msg_no_notes="Không tìm thấy nốt nào có thể phát",
    msg_unknown_format="Không tìm thấy trình xử lý cho định dạng",
    msg_export_error="Không thể tạo bản nhạc",
    msg_no_midi="Hãy tải và chuẩn bị tập tin MIDI trên tab Phát Nhạc trước.",
    msg_hardware_error="Lỗi Phần Cứng/Thực Thi",
    msg_error_playback="Luồng phát lại bị dừng đột ngột do lỗi.",

    status_parsing="Đang phân tích cấu trúc MIDI…",
    status_selected_tracks="Đã chọn track:",
    status_cancelled="Đã hủy chọn track.",
    status_playback_finished="Quá trình phát lại đã kết thúc.",
    status_seeking="Đang tua đến",
    status_importing="Đang nhập bản nhạc",
    status_exported="Đã xuất bản nhạc",
    status_selected_file="Đã chọn tập tin",
    status_loaded_save="Đã tải bản lưu",

    translator_import="Nhập",
    translator_export="Xuất",
    translator_format="Định Dạng",
    translator_paste_sheet="Dán bản nhạc vào đây",
    translator_bpm="Nhịp/phút",
    translator_humanize="Nhân Bản Hóa",
    translator_play_sheet="Phát Bản Nhạc",

    discord_tooltip="Discord: @xiunolove — nhấn để sao chép",
)


# ── Manager ───────────────────────────────────────────────────────────────

class I18nManager:
    """Manages application language and provides translated strings."""

    _current_lang: str = "en"
    _strings: TranslationStrings = TranslationStrings()

    LANG_NAMES = {
        "en": "English",
        "vi": "Tiếng Việt",
    }

    @classmethod
    def set_language(cls, lang_code: str) -> None:
        """Set active language. 'en' or 'vi'."""
        cls._current_lang = lang_code.lower()
        if cls._current_lang == "vi":
            cls._strings = VIETNAMESE
        else:
            cls._strings = TranslationStrings()

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def get_strings(cls) -> TranslationStrings:
        return cls._strings

    @classmethod
    def t(cls, key: str, *args) -> str:
        """Get translated string by attribute name."""
        val = getattr(cls._strings, key, key)
        if args:
            return val.format(*args)
        return val

    @classmethod
    def all_languages(cls) -> Dict[str, str]:
        return cls.LANG_NAMES.copy()
