"""
Read/write helpers used by the Edit MIDI tab.

Unlike core.translator (which converts to/from Roblox keystroke "sheet"
text), this module works with *real* .mid files: exporting a list of
in-app Note objects to a standard, playable Format-1 MIDI file, and
flattening an existing MIDI file's tracks into one editable note list.
"""
from typing import List, Tuple

import mido

from core.core import MidiParser
from core.models import Note


def export_notes_to_midi(notes: List[Note], filepath: str, bpm: float = 120.0,
                          ticks_per_beat: int = 480) -> None:
    """Write a flat list of Note objects out as a standard, playable
    Format-1 .mid file (a real MIDI file any DAW/player/game can read —
    not a Roblox keystroke sheet)."""
    bpm = max(1.0, float(bpm))
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)

    tempo_track = mido.MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(mido.MetaMessage("track_name", name="Tempo", time=0))
    tempo_track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    tempo_track.append(mido.MetaMessage("end_of_track", time=0))

    note_track = mido.MidiTrack()
    mid.tracks.append(note_track)
    note_track.append(mido.MetaMessage("track_name", name="Edited", time=0))

    sec_per_tick = 60.0 / (bpm * ticks_per_beat)

    events = []
    for note in notes:
        if note.duration <= 0:
            continue
        start_tick = max(0, round(note.start_time / sec_per_tick))
        end_tick = max(start_tick + 1, round((note.start_time + note.duration) / sec_per_tick))
        channel = note.channel if 0 <= note.channel <= 15 else 0
        pitch = max(0, min(127, int(round(note.pitch))))
        velocity = max(1, min(127, int(round(note.velocity))))
        # priority 0 = note_on before note_off when ticks tie, so a note
        # that ends exactly when another starts doesn't get truncated wrong
        events.append((start_tick, 0, mido.Message("note_on", note=pitch, velocity=velocity, channel=channel)))
        events.append((end_tick, 1, mido.Message("note_off", note=pitch, velocity=0, channel=channel)))

    events.sort(key=lambda e: (e[0], e[1]))
    last_tick = 0
    for abs_tick, _priority, msg in events:
        delta = max(0, abs_tick - last_tick)
        note_track.append(msg.copy(time=delta))
        last_tick = abs_tick

    note_track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(filepath)


def import_midi_for_edit(filepath: str) -> Tuple[List[Note], float]:
    """Flatten every track of a MIDI file into one editable note list plus
    an estimated BPM, ready to load into the Edit MIDI tab's piano roll."""
    tracks, tempo_map = MidiParser.parse_structure(filepath)

    flat: List[Note] = []
    note_id = 0
    for track in tracks:
        for n in track.notes:
            flat.append(Note(note_id, n.pitch, n.velocity, n.start_time, n.duration,
                              "unknown", n.original_track_index, n.channel))
            note_id += 1
    flat.sort(key=lambda n: n.start_time)

    tempo_us = tempo_map.get_tempo_at(0.0) or 500000
    bpm = mido.tempo2bpm(tempo_us)
    return flat, round(bpm, 2)
