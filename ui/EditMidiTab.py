"""
Edit MIDI tab: a small piano-roll editor for creating and editing MIDI
directly inside Teto Midi.

Features:
  - Draw / Select / Erase tools, grid snapping, adjustable note length & zoom
  - Drag to move notes, drag the right edge to resize, Delete to remove
  - Undo / Redo
  - Import an existing .mid to keep editing it, or start from a blank roll
  - Export a real, playable .mid file
  - Export a quick .wav "test file" rendered by the built-in preview synth
  - "Preview Audio" to listen to the current notes directly in the app
  - "Test in Playback" to send the notes straight into Teto Midi's normal
    playback/keystroke pipeline (same engine used by the Playback tab)
"""
from typing import Dict, List

from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal as Signal
from PyQt6.QtGui import QBrush, QColor, QKeySequence, QPainter, QPen, QShortcut
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QFileDialog, QGraphicsItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSizePolicy, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from core.audio_player import AudioPreviewPlayer
from core.core import KeyMapper
from core.models import Note

HANDLE_PX = 6
BLACK_KEY_PITCH_CLASSES = {1, 3, 6, 8, 10}

_TOOL_BTN_STYLE = (
    "QPushButton { padding: 5px 12px; }"
    "QPushButton:checked { border: 2px solid #4FA8E0; font-weight: 600; }"
)


# ── Note item ────────────────────────────────────────────────────────────

class NoteItem(QGraphicsRectItem):
    def __init__(self, note_id: int, pitch: int, width: float, row_height: int,
                 velocity: int = 100, color: QColor = None):
        super().__init__(0, 0, max(4.0, width), row_height - 1)
        self.note_id = note_id
        self.pitch = pitch
        self.velocity = max(1, min(127, velocity))
        self.row_height = row_height
        self._base_color = color or QColor("#4FA8E0")
        self._resizing = False
        self._resize_start_width = width
        self._resize_start_mouse_x = 0.0
        # True while we're setting position programmatically (import, zoom
        # rescale, undo/redo) so itemChange() doesn't re-snap or clamp
        # values the user never touched with the mouse.
        self.suppress_snap = True

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor("#14151a"), 1))
        self._apply_velocity_color()

    def _apply_velocity_color(self):
        alpha = 110 + int(self.velocity / 127 * 145)
        c = QColor(self._base_color)
        c.setAlpha(alpha)
        self.setBrush(QBrush(c))

    def set_velocity(self, v: int):
        self.velocity = max(1, min(127, v))
        self._apply_velocity_color()

    # ── interaction ──────────────────────────────────────────────────

    def hoverMoveEvent(self, event):
        if event.pos().x() >= self.rect().width() - HANDLE_PX:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        scene = self.scene()
        if event.button() == Qt.MouseButton.LeftButton and event.pos().x() >= self.rect().width() - HANDLE_PX:
            if scene:
                scene.notify_before_change()
            self._resizing = True
            self._resize_start_width = self.rect().width()
            self._resize_start_mouse_x = event.scenePos().x()
            self.setSelected(True)
            event.accept()
            return

        if scene:
            scene.notify_before_change()
        self.suppress_snap = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            scene = self.scene()
            snap_px = scene.snap_px() if scene else 0.0
            delta = event.scenePos().x() - self._resize_start_mouse_x
            new_width = self._resize_start_width + delta
            if snap_px > 0:
                new_width = round(new_width / snap_px) * snap_px
            new_width = max(snap_px if snap_px > 0 else 4.0, new_width)
            r = self.rect()
            r.setWidth(new_width)
            self.setRect(r)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        scene = self.scene()
        if self._resizing:
            self._resizing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
        self.suppress_snap = True
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        if scene:
            scene.note_edited.emit()

    def itemChange(self, change, value):
        scene = self.scene()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and scene is not None and not self._resizing:
            x = value.x()
            if not self.suppress_snap:
                snap_px = scene.snap_px()
                if snap_px > 0:
                    x = round(x / snap_px) * snap_px
                x = max(0.0, x)
                row = round(value.y() / self.row_height)
                row = max(0, min(scene.total_rows - 1, row))
                self.pitch = scene.row_to_pitch(row)
                y = row * self.row_height
                return QPointF(x, y)
            return QPointF(max(0.0, x), value.y())
        return super().itemChange(change, value)


# ── Scene ────────────────────────────────────────────────────────────────

class PianoRollScene(QGraphicsScene):
    note_edited = Signal()      # a move/resize/velocity edit finished
    notes_changed = Signal()    # structural change: add / delete / load / clear

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 14
        self.pitch_min = 0
        self.pitch_max = 127
        self.total_rows = self.pitch_max - self.pitch_min + 1
        self.px_per_beat = 80.0
        self.bpm = 120.0
        self.snap_division = 4  # subdivisions per beat (4 == 1/16 note)
        self.tool = "draw"      # 'draw' | 'select' | 'erase'
        self.default_length_beats = 0.5
        self.default_velocity = 100
        self.on_before_change = None  # callback set by EditMidiTab for undo

        self._next_id = 0
        self._items: Dict[int, NoteItem] = {}
        self.setSceneRect(0, 0, 4000, self.total_rows * self.row_height)

    def notify_before_change(self):
        if self.on_before_change:
            self.on_before_change()

    def snap_px(self) -> float:
        if self.snap_division <= 0:
            return 0.0
        return self.px_per_beat / self.snap_division

    def set_bpm(self, bpm: float):
        self.bpm = max(1.0, bpm)

    def seconds_to_x(self, seconds: float) -> float:
        beats = seconds * (self.bpm / 60.0)
        return beats * self.px_per_beat

    def x_to_seconds(self, x: float) -> float:
        beats = x / self.px_per_beat if self.px_per_beat > 0 else 0.0
        return beats * (60.0 / self.bpm)

    def pitch_to_row(self, pitch: int) -> int:
        return self.pitch_max - max(self.pitch_min, min(self.pitch_max, pitch))

    def row_to_pitch(self, row: int) -> int:
        return self.pitch_max - row

    def iter_items(self):
        return list(self._items.values())

    def clear_all(self):
        self.clear()
        self._items.clear()
        self._next_id = 0
        self.notes_changed.emit()

    def add_note(self, pitch: int, start_sec: float, duration_sec: float,
                 velocity: int = 100, note_id: int = None) -> NoteItem:
        if note_id is None:
            note_id = self._next_id
        self._next_id = max(self._next_id, note_id + 1)

        x = self.seconds_to_x(start_sec)
        width = max(4.0, self.seconds_to_x(start_sec + duration_sec) - x)
        row = self.pitch_to_row(pitch)

        item = NoteItem(note_id, pitch, width, self.row_height, velocity)
        self.addItem(item)
        item.suppress_snap = True
        item.setPos(x, row * self.row_height)
        self._items[note_id] = item
        return item

    def remove_item(self, item: NoteItem):
        self._items.pop(item.note_id, None)
        self.removeItem(item)
        self.notes_changed.emit()

    def get_notes(self) -> List[Note]:
        result = []
        for item in self._items.values():
            start_sec = self.x_to_seconds(item.pos().x())
            end_sec = self.x_to_seconds(item.pos().x() + item.rect().width())
            duration = max(0.02, end_sec - start_sec)
            result.append(Note(item.note_id, item.pitch, item.velocity,
                                round(start_sec, 5), round(duration, 5)))
        result.sort(key=lambda n: n.start_time)
        return result

    def load_notes(self, notes: List[Note]):
        self.clear()
        self._items.clear()
        self._next_id = 0
        for n in notes:
            self.add_note(n.pitch, n.start_time, max(n.duration, 0.03), n.velocity, note_id=n.id)
        self.notes_changed.emit()

    # ── painting ─────────────────────────────────────────────────────

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor("#1b1d23"))

        top_row = max(0, int(rect.top() // self.row_height))
        bottom_row = min(self.total_rows - 1, int(rect.bottom() // self.row_height) + 1)
        for row in range(top_row, bottom_row + 1):
            pitch = self.row_to_pitch(row)
            y = row * self.row_height
            is_black = (pitch % 12) in BLACK_KEY_PITCH_CLASSES
            painter.fillRect(QRectF(rect.left(), y, rect.width(), self.row_height),
                              QColor("#20222b") if is_black else QColor("#262933"))
            if pitch % 12 == 0:
                painter.setPen(QPen(QColor("#3a3d4a"), 1))
                painter.drawLine(QPointF(rect.left(), y + self.row_height),
                                  QPointF(rect.right(), y + self.row_height))

        beat_px = self.px_per_beat
        sub_px = self.snap_px() or beat_px
        if sub_px <= 0:
            return
        x = (int(rect.left() // sub_px)) * sub_px
        while x < rect.right():
            beat_number = x / beat_px
            is_bar = abs(beat_number - round(beat_number)) < 1e-6 and int(round(beat_number)) % 4 == 0
            is_beat = abs(beat_number - round(beat_number)) < 1e-6
            if is_bar:
                painter.setPen(QPen(QColor("#5b5f70"), 1.6))
            elif is_beat:
                painter.setPen(QPen(QColor("#40434f"), 1.1))
            else:
                painter.setPen(QPen(QColor("#2e303a"), 0.8))
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += sub_px

    # ── mouse: create / erase ────────────────────────────────────────

    def mousePressEvent(self, event):
        pos = event.scenePos()
        views = self.views()
        item = self.itemAt(pos, views[0].transform()) if views else None

        if isinstance(item, NoteItem):
            if self.tool == "erase" and event.button() == Qt.MouseButton.LeftButton:
                self.notify_before_change()
                self.remove_item(item)
                event.accept()
                return
            super().mousePressEvent(event)
            return

        if self.tool == "draw" and event.button() == Qt.MouseButton.LeftButton:
            if pos.x() < 0 or pos.y() < 0 or pos.y() > self.total_rows * self.row_height:
                super().mousePressEvent(event)
                return
            row = max(0, min(self.total_rows - 1, int(pos.y() // self.row_height)))
            pitch = self.row_to_pitch(row)
            snap = self.snap_px()
            x = pos.x()
            if snap > 0:
                x = round(x / snap) * snap
            x = max(0.0, x)
            start_sec = self.x_to_seconds(x)
            dur_sec = self.default_length_beats * (60.0 / self.bpm)

            self.notify_before_change()
            item = self.add_note(pitch, start_sec, dur_sec, self.default_velocity)
            self.clearSelection()
            item.setSelected(True)
            self.notes_changed.emit()
            event.accept()
            return

        super().mousePressEvent(event)


# ── Piano keys reference column ─────────────────────────────────────────

class PianoKeysWidget(QWidget):
    def __init__(self, scene: PianoRollScene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._scroll_offset = 0
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def set_scroll_offset(self, value: int):
        self._scroll_offset = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#20222b"))
        row_h = self.scene.row_height
        top_row = max(0, self._scroll_offset // row_h)
        visible_rows = self.height() // row_h + 2
        for i in range(visible_rows):
            row = top_row + i
            if row >= self.scene.total_rows:
                break
            pitch = self.scene.row_to_pitch(row)
            y = row * row_h - self._scroll_offset
            is_black = (pitch % 12) in BLACK_KEY_PITCH_CLASSES
            painter.fillRect(0, y, self.width(), row_h - 1,
                              QColor("#2b2e38") if is_black else QColor("#e8e8ec"))
            if pitch % 12 == 0:
                painter.setPen(QColor("#101216"))
                painter.drawText(3, y + row_h - 3, f"C{(pitch // 12) - 1}")
        painter.end()


# ── Main tab ──────────────────────────────────────────────────────────────

class EditMidiTab(QWidget):
    # (notes, bpm) — send the current piano roll into the normal playback
    # / keystroke-simulation pipeline for a real in-game test.
    test_requested = Signal(list, float)

    _SNAP_MAP = {"1/4": 1, "1/8": 2, "1/16": 4, "1/32": 8, "1/8 (triplet)": 3, "Off": 0}
    _LENGTH_MAP = {"1/32": 0.125, "1/16": 0.25, "1/8": 0.5, "1/4": 1.0, "1/2": 2.0, "1/1": 4.0}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._undo_stack: List[List[Note]] = []
        self._redo_stack: List[List[Note]] = []
        self._audio_player = AudioPreviewPlayer(self)
        self._audio_player.playback_finished.connect(self._on_preview_finished)
        self._audio_player.error.connect(self._on_preview_error)
        self._setup_ui()

    # ── UI construction ──────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addLayout(self._build_tools_row())
        layout.addLayout(self._build_ops_row())

        roll_row = QHBoxLayout()
        roll_row.setSpacing(0)

        self.scene = PianoRollScene()
        self.scene.on_before_change = self._snapshot_undo
        self.scene.notes_changed.connect(self._update_status)
        self.scene.note_edited.connect(self._update_status)
        self.scene.selectionChanged.connect(self._on_selection_changed)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.keys_widget = PianoKeysWidget(self.scene)
        self.keys_widget.setFixedWidth(46)
        self.view.verticalScrollBar().valueChanged.connect(self.keys_widget.set_scroll_offset)

        roll_row.addWidget(self.keys_widget)
        roll_row.addWidget(self.view, 1)
        layout.addLayout(roll_row, 1)

        layout.addLayout(self._build_status_row())

        QShortcut(QKeySequence.StandardKey.Undo, self).activated.connect(self._undo)
        QShortcut(QKeySequence.StandardKey.Redo, self).activated.connect(self._redo)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.view).activated.connect(self._delete_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self.view).activated.connect(self._delete_selected)

        QTimer.singleShot(0, self._scroll_to_default)

        if not self._audio_player._effect:
            self.preview_btn.setEnabled(False)
            self.preview_btn.setToolTip(
                "QtMultimedia isn't available in this environment — in-app audio "
                "preview is disabled, but MIDI/WAV export and Playback testing still work."
            )

    def _build_tools_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.tool_group = QButtonGroup(self)
        self.draw_btn = QPushButton("✏  Draw")
        self.select_btn = QPushButton("⬚  Select")
        self.erase_btn = QPushButton("🧽  Erase")
        for b in (self.draw_btn, self.select_btn, self.erase_btn):
            b.setCheckable(True)
            b.setStyleSheet(_TOOL_BTN_STYLE)
            self.tool_group.addButton(b)
            row.addWidget(b)
        self.draw_btn.setChecked(True)
        self.tool_group.buttonClicked.connect(self._on_tool_changed)

        row.addSpacing(16)
        row.addWidget(QLabel("BPM"))
        self.bpm_spin = QSpinBox()
        self.bpm_spin.setRange(20, 400)
        self.bpm_spin.setValue(120)
        self.bpm_spin.valueChanged.connect(self._on_bpm_changed)
        row.addWidget(self.bpm_spin)

        row.addSpacing(16)
        row.addWidget(QLabel("Snap"))
        self.snap_combo = QComboBox()
        self.snap_combo.addItems(list(self._SNAP_MAP.keys()))
        self.snap_combo.setCurrentText("1/16")
        self.snap_combo.currentTextChanged.connect(self._on_snap_changed)
        row.addWidget(self.snap_combo)

        row.addSpacing(16)
        row.addWidget(QLabel("Note Length"))
        self.length_combo = QComboBox()
        self.length_combo.addItems(list(self._LENGTH_MAP.keys()))
        self.length_combo.setCurrentText("1/8")
        self.length_combo.currentTextChanged.connect(self._on_length_changed)
        row.addWidget(self.length_combo)

        row.addSpacing(16)
        row.addWidget(QLabel("Zoom"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(30, 240)
        self.zoom_slider.setValue(80)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        row.addWidget(self.zoom_slider)

        row.addStretch()
        return row

    def _build_ops_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.new_btn = QPushButton("New")
        self.import_btn = QPushButton("Import MIDI…")
        self.export_btn = QPushButton("Export MIDI…")
        self.export_wav_btn = QPushButton("Export Test Audio (.wav)")
        self.preview_btn = QPushButton("▶  Preview Audio")
        self.stop_preview_btn = QPushButton("■  Stop")
        self.test_btn = QPushButton("🎮  Test in Playback")
        self.undo_btn = QPushButton("↶ Undo")
        self.redo_btn = QPushButton("↷ Redo")
        self.stop_preview_btn.setEnabled(False)

        for b in (self.new_btn, self.import_btn, self.export_btn, self.export_wav_btn):
            row.addWidget(b)
        row.addSpacing(12)
        row.addWidget(self.preview_btn)
        row.addWidget(self.stop_preview_btn)
        row.addSpacing(12)
        row.addWidget(self.test_btn)
        row.addStretch()
        row.addWidget(self.undo_btn)
        row.addWidget(self.redo_btn)

        self.new_btn.clicked.connect(self._on_new)
        self.import_btn.clicked.connect(self._on_import)
        self.export_btn.clicked.connect(self._on_export_midi)
        self.export_wav_btn.clicked.connect(self._on_export_wav)
        self.preview_btn.clicked.connect(self._on_preview)
        self.stop_preview_btn.clicked.connect(self._on_stop_preview)
        self.test_btn.clicked.connect(self._on_test_in_playback)
        self.undo_btn.clicked.connect(self._undo)
        self.redo_btn.clicked.connect(self._redo)
        return row

    def _build_status_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel("Velocity"))
        self.velocity_slider = QSlider(Qt.Orientation.Horizontal)
        self.velocity_slider.setRange(1, 127)
        self.velocity_slider.setValue(100)
        self.velocity_slider.setFixedWidth(150)
        self.velocity_slider.setEnabled(False)
        self.velocity_slider.valueChanged.connect(self._on_velocity_slider_changed)
        row.addWidget(self.velocity_slider)
        self.velocity_value_label = QLabel("100")
        self.velocity_value_label.setFixedWidth(28)
        row.addWidget(self.velocity_value_label)

        row.addSpacing(20)
        self.status_label = QLabel("0 notes")
        self.status_label.setProperty("role", "muted")
        row.addWidget(self.status_label, 1)
        return row

    def _scroll_to_default(self):
        row = self.scene.pitch_to_row(60)
        self.view.centerOn(200, row * self.scene.row_height)

    # ── tool / snap / length / zoom / bpm ────────────────────────────

    def _on_tool_changed(self, btn):
        if btn is self.draw_btn:
            self.scene.tool = "draw"
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        elif btn is self.select_btn:
            self.scene.tool = "select"
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.scene.tool = "erase"
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def _on_snap_changed(self, text: str):
        self.scene.snap_division = self._SNAP_MAP.get(text, 4)
        self.scene.update()

    def _on_length_changed(self, text: str):
        self.scene.default_length_beats = self._LENGTH_MAP.get(text, 0.5)

    def _on_zoom_changed(self, value: int):
        old_ppb = self.scene.px_per_beat or float(value)
        new_ppb = float(value)
        ratio = new_ppb / old_ppb
        self.scene.px_per_beat = new_ppb
        for item in self.scene.iter_items():
            item.suppress_snap = True
            pos = item.pos()
            r = item.rect()
            item.setPos(pos.x() * ratio, pos.y())
            r.setWidth(max(4.0, r.width() * ratio))
            item.setRect(r)
            item.suppress_snap = True
        rect = self.scene.sceneRect()
        self.scene.setSceneRect(0, 0, max(4000.0, rect.width() * ratio), rect.height())
        self.scene.update()

    def _on_bpm_changed(self, value: int):
        # Notes are stored by beat position (pixels), so changing BPM only
        # changes how many real seconds those beats take — it doesn't move
        # anything in the roll, same as changing tempo in a normal DAW.
        self.scene.set_bpm(float(value))
        self._update_status()

    # ── selection / velocity ─────────────────────────────────────────

    def _selected_note_items(self) -> List[NoteItem]:
        return [it for it in self.scene.selectedItems() if isinstance(it, NoteItem)]

    def _on_selection_changed(self):
        sel = self._selected_note_items()
        self.velocity_slider.blockSignals(True)
        if sel:
            self.velocity_slider.setEnabled(True)
            self.velocity_slider.setValue(sel[0].velocity)
            self.velocity_value_label.setText(str(sel[0].velocity))
        else:
            self.velocity_slider.setEnabled(False)
        self.velocity_slider.blockSignals(False)
        self._update_status()

    def _on_velocity_slider_changed(self, value: int):
        sel = self._selected_note_items()
        if not sel:
            return
        self._snapshot_undo()
        for it in sel:
            it.set_velocity(value)
        self.velocity_value_label.setText(str(value))
        self._update_status()

    def _delete_selected(self):
        sel = self._selected_note_items()
        if not sel:
            return
        self._snapshot_undo()
        for it in sel:
            self.scene.remove_item(it)
        self._update_status()

    # ── status ────────────────────────────────────────────────────────

    def _update_status(self):
        notes = self.scene.get_notes()
        if not notes:
            self.status_label.setText("0 notes")
            return
        total = max(n.end_time for n in notes)
        m, s = divmod(int(total), 60)
        sel = self._selected_note_items()
        extra = ""
        if len(sel) == 1:
            extra = f"   |   Selected: {KeyMapper.pitch_to_name(sel[0].pitch)}, vel {sel[0].velocity}"
        elif len(sel) > 1:
            extra = f"   |   {len(sel)} notes selected"
        self.status_label.setText(f"{len(notes)} note(s)   |   Length {m:02d}:{s:02d}{extra}")

    # ── undo / redo ───────────────────────────────────────────────────

    def _snapshot_undo(self):
        self._undo_stack.append(self.scene.get_notes())
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _undo(self):
        if not self._undo_stack:
            return
        current = self.scene.get_notes()
        prev = self._undo_stack.pop()
        self._redo_stack.append(current)
        self.scene.load_notes(prev)
        self._update_status()

    def _redo(self):
        if not self._redo_stack:
            return
        current = self.scene.get_notes()
        nxt = self._redo_stack.pop()
        self._undo_stack.append(current)
        self.scene.load_notes(nxt)
        self._update_status()

    # ── file operations ───────────────────────────────────────────────

    def _on_new(self):
        if self.scene.iter_items():
            reply = QMessageBox.question(
                self, "New", "Clear the current piano roll? Unsaved edits will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._snapshot_undo()
        self.scene.clear_all()
        self._update_status()

    def _on_import(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Import MIDI", "", "MIDI Files (*.mid *.midi)")
        if not filepath:
            return
        try:
            from core.midi_io import import_midi_for_edit
            notes, bpm = import_midi_for_edit(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not read MIDI file:\n{e}")
            return
        if not notes:
            QMessageBox.warning(self, "Import", "No notes were found in that MIDI file.")
            return

        self._snapshot_undo()
        self.bpm_spin.blockSignals(True)
        self.bpm_spin.setValue(int(round(bpm)))
        self.bpm_spin.blockSignals(False)
        self.scene.set_bpm(bpm)
        self.scene.load_notes(notes)
        self._update_status()

    def _on_export_midi(self):
        notes = self.scene.get_notes()
        if not notes:
            QMessageBox.warning(self, "Export MIDI", "There are no notes to export.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Export MIDI", "edited.mid", "MIDI Files (*.mid)")
        if not filepath:
            return
        try:
            from core.midi_io import export_notes_to_midi
            export_notes_to_midi(notes, filepath, self.bpm_spin.value())
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not write MIDI file:\n{e}")
            return
        QMessageBox.information(self, "Export MIDI", f"Saved to:\n{filepath}")

    def _on_export_wav(self):
        notes = self.scene.get_notes()
        if not notes:
            QMessageBox.warning(self, "Export Test Audio", "There are no notes to export.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Test Audio", "preview.wav", "WAV Audio (*.wav)")
        if not filepath:
            return
        try:
            from core.synth import SimpleSynth
            SimpleSynth().render_to_wav(filepath, notes)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not render audio:\n{e}")
            return
        QMessageBox.information(self, "Export Test Audio", f"Saved to:\n{filepath}")

    # ── audio preview ─────────────────────────────────────────────────

    def _on_preview(self):
        notes = self.scene.get_notes()
        if not notes:
            return
        self.preview_btn.setEnabled(False)
        self.stop_preview_btn.setEnabled(True)
        ok = self._audio_player.play_notes(notes, self.bpm_spin.value())
        if not ok:
            self._on_preview_finished()

    def _on_stop_preview(self):
        self._audio_player.stop()
        self._on_preview_finished()

    def _on_preview_finished(self):
        self.preview_btn.setEnabled(True)
        self.stop_preview_btn.setEnabled(False)

    def _on_preview_error(self, msg: str):
        QMessageBox.warning(self, "Audio Preview", msg)
        self._on_preview_finished()

    # ── test in playback ──────────────────────────────────────────────

    def _on_test_in_playback(self):
        notes = self.scene.get_notes()
        if not notes:
            QMessageBox.warning(self, "Test in Playback", "There are no notes to test.")
            return
        self.test_requested.emit(notes, float(self.bpm_spin.value()))

    # ── lifecycle ─────────────────────────────────────────────────────

    def shutdown(self):
        self._audio_player.shutdown()
