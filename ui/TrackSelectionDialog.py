"""
TrackSelectionDialog — Chọn track MIDI để phát.
FIX: Thêm Select All/Deselect All, fix checkbox hiển thị rõ ràng.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QComboBox, QAbstractItemView, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt


class TrackSelectionDialog(QDialog):
    """
    Dialog cho phép chọn track MIDI và gán tay trái/phải.
    """

    def __init__(self, tracks: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎹 Select Tracks to Play")
        self.setMinimumSize(650, 350)
        self.tracks = tracks
        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Hướng dẫn
        hint = QLabel(
            "<b>Hướng dẫn:</b> Tick ☑️ vào cột <b>Play</b> để chọn track muốn phát. "
            "Bỏ tick để 'cancel' track đó. Gán tay Trái/Phải nếu cần."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # --- Nút Select All / Deselect All (FIX) ---
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("☑️ Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn = QPushButton("☐ Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Bảng track ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Play", "Track Name", "Instrument", "Notes", "Hand Assignment"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # --- Nút OK / Cancel ---
        btn_layout2 = QHBoxLayout()
        self.ok_btn = QPushButton("✅ OK — Load Selected")
        self.ok_btn.setStyleSheet("font-weight: bold; background-color: #27ae60; color: white;")
        self.ok_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout2.addStretch()
        btn_layout2.addWidget(self.cancel_btn)
        btn_layout2.addWidget(self.ok_btn)
        layout.addLayout(btn_layout2)

    def _populate_table(self):
        self.table.setRowCount(len(self.tracks))

        for row, track in enumerate(self.tracks):
            # FIX: Cột Play — dùng QCheckBox widget rõ ràng thay vì chỉ dùng Item
            play_checkbox = QCheckBox()
            play_checkbox.setChecked(track.get("play", True))
            play_checkbox.setStyleSheet("QCheckBox { margin-left: 15px; }")
            play_widget = QWidget()
            play_layout = QHBoxLayout(play_widget)
            play_layout.addWidget(play_checkbox)
            play_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            play_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, play_widget)

            # Track Name
            name_item = QTableWidgetItem(track.get("name", f"Track {row}"))
            self.table.setItem(row, 1, name_item)

            # Instrument
            inst_item = QTableWidgetItem(track.get("instrument", "Unknown"))
            self.table.setItem(row, 2, inst_item)

            # Notes
            notes_item = QTableWidgetItem(str(track.get("notes", 0)))
            notes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, notes_item)

            # Hand Assignment
            hand_combo = QComboBox()
            hand_combo.addItems(["Auto-Detect", "Left Hand", "Right Hand", "Both"])
            hand_combo.setCurrentText(track.get("hand", "Auto-Detect"))
            self.table.setCellWidget(row, 4, hand_combo)

    def _select_all(self):
        """FIX: Tick tất cả checkbox Play."""
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)

    def _deselect_all(self):
        """FIX: Bỏ tick tất cả checkbox Play (= cancel all tracks)."""
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)

    def get_selection(self) -> list[dict]:
        """
        Trả về danh sách track với trạng thái play/hand đã chọn.
        """
        selection = []
        for row in range(self.table.rowCount()):
            play_widget = self.table.cellWidget(row, 0)
            play = True
            if play_widget:
                checkbox = play_widget.findChild(QCheckBox)
                if checkbox:
                    play = checkbox.isChecked()

            hand_widget = self.table.cellWidget(row, 4)
            hand = "Auto-Detect"
            if hand_widget and isinstance(hand_widget, QComboBox):
                hand = hand_widget.currentText()

            selection.append({
                "index": row,
                "play": play,
                "hand": hand,
                "name": self.table.item(row, 1).text() if self.table.item(row, 1) else "",
                "instrument": self.table.item(row, 2).text() if self.table.item(row, 2) else "",
                "notes": int(self.table.item(row, 3).text()) if self.table.item(row, 3) else 0,
            })
        return selection
