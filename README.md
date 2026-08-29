# Teto Midi hub

**Teto Midi** is a MIDI playback and auto-play tool with a Kasane Teto–themed interface. It loads MIDI files (or pasted sheet-music text), can play them back with a live piano-roll visualizer, and can **auto-play the track through simulated key presses** into virtual piano games — such as the piano games found on Roblox — with optional humanization so the input feels less robotic.

This README covers every tab and setting in the app, plus full install/build instructions for Windows and Linux.

---

## Table of Contents

1. [Overview](#overview)
2. [Interface Layout](#interface-layout)
3. [Playback Tab](#playback-tab)
4. [Visualizer Tab](#visualizer-tab)
5. [Translator Tab](#translator-tab)
6. [Humanization Options (Detailed)](#humanization-options-detailed)
7. [Settings & Debug Tabs](#settings--debug-tabs)
8. [Themes](#themes)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Auto-Playing Piano on Roblox — Full Walkthrough](#auto-playing-piano-on-roblox--full-walkthrough)
11. [Installation](#installation)
    - [Windows](#windows)
    - [Linux (terminal)](#linux-terminal)
    - [Build from Source](#build-from-source)
12. [Requirements](#requirements)
13. [Project Structure](#project-structure)
14. [Troubleshooting](#troubleshooting)
15. [FAQ](#faq)
16. [License / Credits](#license--credits)

---

## Overview

Teto Midi has five main sections, accessible from the left-hand sidebar:

| Icon | Tab | Purpose |
|---|---|---|
| ▶ | **Playback** | Load a MIDI file, control tempo/pedal/transpose, start/stop playback |
| ♬ | **Visualizer** | Watch notes fall on a piano roll in real time as the track plays |
| ⇄ | **Translator** | Convert between sheet-music text formats (e.g. Virtual Piano notation) and play them directly |
| ⚙ | **Settings** | App-wide configuration and theme selection |
| ⚒ | **Debug** | Diagnostic console/output for troubleshooting |

At the bottom of the window, a **transport bar** is always visible no matter which tab you're on:

- **▶ Play (F6)** — start playback (button turns green when a file/sheet is ready)
- **■ Stop** — stop playback immediately
- A **progress bar** with elapsed / total time (`00:15 / 01:57`)
- **Save** — save the current session/settings
- **Reset** — reset playback position and cleared loaded state
- **▲ Collapse** — switch to a compact/mini view of the app

---

## Interface Layout

The app window is split into:

- **Left sidebar** — tab navigation (Playback / Visualizer / Translator / Settings / Debug)
- **Main panel** — content specific to the selected tab
- **Bottom transport bar** — always-visible playback controls (see above)

The default color theme is **Teto Red**, a dark crimson palette inspired by Kasane Teto's hair color. This can be changed at any time from the Settings tab (see [Themes](#themes)).

---

## Playback Tab

This is the main tab for loading and playing a MIDI file.

### MIDI File section
- **Browse…** — opens a file picker to select a `.mid` file from disk.
- **Load Save** — restores a previously saved session (loaded file + playback settings), created via the **Save** button in the transport bar.
- If no file is loaded, this section shows *"No file selected."*

### Playback section
- **Tempo** — slider + numeric field controlling playback speed in BPM. Default: `100.0`. Drag the slider or type an exact value.
- **Pedal** — dropdown for how sustain-pedal (damper) events are handled. Default: `Auto (Default)`, which follows the pedal data embedded in the MIDI file.
- **Transpose** — shifts every note up or down by a number of semitones (`st`). Use this if the target piano's range doesn't match the MIDI file, or to change key.
- **88-Key Layout** — checkbox. Enable if your target keyboard/game supports the full 88-key range; otherwise the app maps notes to a reduced range.
- **Countdown** — checkbox (enabled by default). When turned on, playback waits a few seconds after you press Play before actually starting, giving you time to switch window focus (e.g. into a Roblox game).
- **Debug Output** — checkbox. Enable to print internal playback logs to the Debug tab — useful when notes aren't playing as expected.

### Humanization panel (right side)
See the full breakdown in [Humanization Options (Detailed)](#humanization-options-detailed) below.

---

## Visualizer Tab

Shows a **real-time piano roll**:

- Notes scroll across the view and light up on a **virtual on-screen keyboard** as they're played.
- **Color coding**: notes are colored (e.g. green vs. red) to visually distinguish two independent parts — typically left-hand vs. right-hand, or melody vs. accompaniment.
- A **sustain pedal indicator bar** appears below the note roll, showing exactly when the sustain pedal is held during playback.
- A vertical **playhead line** moves across the roll in sync with the transport progress bar at the bottom of the window.

This tab is read-only (no editing) — it's meant purely to preview/monitor playback, useful for confirming a MIDI file will play correctly before using it for auto-play.

---

## Translator Tab

Converts sheet-music **text** (not a binary `.mid` file) into playable input, or converts a loaded track back into text.

- **Format** dropdown — selects the sheet-music notation to use. Currently includes **Virtual Piano** notation (the format commonly used by online/virtual piano sheet communities).
- **Import** sub-tab:
  - A text box labeled *"Paste sheet text"* — paste your sheet notation here (e.g. copied from a Virtual Piano sheet website).
  - **BPM** field — set the playback speed for the pasted sheet (default `120`).
  - **Humanize** checkbox — applies humanization to the translated sheet the same way it applies to MIDI playback.
  - **▶ Play Sheet** — plays the pasted sheet directly, without needing to save it as a `.mid` file first.
- **Export** sub-tab — converts the currently loaded MIDI/session into text in the selected Format, so you can copy it out and share/reuse it elsewhere.

**Tip:** Use the Translator when you find a piano sheet as plain text online and don't have (or don't want to create) a `.mid` file for it.

---

## Humanization Options (Detailed)

Found in the right-hand panel of the **Playback** tab. Purpose: make automated playback sound and *look* less mechanically perfect — useful both for a more musical performance and for making auto-play input less obviously robotic.

| Option | Type | Default | What it does |
|---|---|---|---|
| **All** | checkbox | off | Master switch. Enables every option below at once. |
| **Simulate Hands** | checkbox | off | Models two virtual "hands" moving across the keyboard, adding small delays consistent with realistic hand movement between distant notes. |
| **Chord Roll** | checkbox | off | Instead of hitting every note in a chord at the exact same instant, notes are slightly staggered (rolled), like a human pressing keys not perfectly simultaneously. |
| **Vary Timing** | checkbox + slider | off, `0.010 s` | Adds small random timing offsets to note-on events, up to the configured number of seconds. |
| **Vary Articulation** | checkbox + slider | off, `95.0%` | Randomizes how long each note is held (and/or its velocity), within the given percentage range, so notes don't all sound identically articulated. |
| **Hand Drift** | checkbox + slider | off, `25.0%` | Simulates gradual positional drift, as if a hand slowly shifts position over a long passage. |
| **Mistakes** | checkbox + slider | off, `0.5%` | Introduces a small, configurable chance of minor human-like errors (e.g. slightly wrong timing/note) — keep this low, since it's cumulative over the whole track. |
| **Tempo Sway** | checkbox + slider | off, `0.015 s` | Makes the overall tempo drift slightly faster/slower in a wave pattern over time, instead of a perfectly locked metronome. |
| **Invert Sway** | checkbox | off (disabled until Tempo Sway is on) | Flips the direction of the tempo sway wave. |

**Recommended starting point:** enable `Simulate Hands`, `Chord Roll`, and `Vary Timing` with their default values for a good balance between natural feel and playback accuracy. Increase `Mistakes` only if you specifically want an imperfect, very human sound — it's off by default for a reason.

---

## Settings & Debug Tabs

- **Settings** — app-wide preferences, including **theme selection** (see below). Exact contents may expand in future versions.
- **Debug** — a console/log view showing internal events (file loading, key-press dispatch, errors). Turn on **Debug Output** in the Playback tab first if you need detailed logs while troubleshooting a specific playback issue.

---

## Themes

Teto Midi ships with 8 built-in color themes, selectable from Settings:

| Theme | Style |
|---|---|
| **Teto Red** *(default)* | Dark crimson red, inspired by Kasane Teto's hair |
| Dark | Neutral dark blue-gray |
| Light | Clean light theme |
| Midnight | Deep blue-black, GitHub-style dark mode |
| Mocha | Warm dark brown |
| Sakura | Soft cherry-blossom pink, light background |
| Emerald | Dark theme with green accents |
| Royal Purple | Dark theme with purple accents |

Switching themes is instant and does not require restarting the app.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `F6` | Play / Pause playback |

*(More shortcuts may exist depending on version — check the Settings tab if one is added for shortcut customization.)*

---

## Auto-Playing Piano on Roblox — Full Walkthrough

Teto Midi can send simulated key presses to auto-play a track inside a virtual piano game window, such as the piano games on Roblox.

**Step-by-step:**

1. **Prepare your track.**
   - Either load a `.mid` file via **Playback → Browse…**, **or**
   - Go to **Translator**, set **Format** to `Virtual Piano`, and paste your sheet text into the **Import** box.

2. **Preview it first (optional but recommended).**
   - Switch to the **Visualizer** tab and hit Play to watch the note roll — confirm the notes, range, and timing look correct before trying to auto-play it into a game.

3. **Tune playback settings.**
   - Set **Tempo** to match what you want in-game.
   - Set **Transpose** if the in-game piano's range differs from the source file (common with games that only support a limited number of octaves).
   - Enable **88-Key Layout** only if the target piano actually supports the full range — otherwise leave it off so notes get mapped down correctly.

4. **Enable Humanization (recommended).**
   - Turn on `Simulate Hands`, `Chord Roll`, and `Vary Timing` at minimum, so the automated input doesn't look perfectly robotic.
   - Adjust sliders to taste — higher `Vary Timing`/`Hand Drift` values make it feel more "loose" and human, at some cost to timing precision.

5. **Enable Countdown.**
   - Keep **Countdown** checked in the Playback tab. This gives you a few seconds after pressing Play to click into the Roblox window before any key presses are sent.

6. **Switch to Roblox.**
   - Get the in-game piano ready and focused (make sure the game window/piano UI is the active, focused window — key presses go to whatever window has focus).

7. **Press ▶ Play (F6).**
   - During the countdown, alt-tab / click into the Roblox window.
   - Once the countdown ends, Teto Midi begins sending key presses matching the loaded track's notes and timing.

8. **Monitor progress.**
   - You can glance at the transport bar's progress (`00:15 / 01:57`) to track how far along the piece is.
   - Press **■ Stop** at any time to immediately halt playback/input.

> ⚠️ **Important:** Automating input into a game may violate that game's or platform's Terms of Service, and some games have anti-macro/anti-automation detection. This tool is provided as-is; use it at your own discretion and risk, and be aware it could result in in-game penalties depending on the platform's rules.

---

## Installation

### Windows

1. Download `TetoMidi.exe` from the project's **Releases** page (or from a CI build artifact if you're building via GitHub Actions).
2. Double-click `TetoMidi.exe` to launch it — no installer, it runs standalone.
3. If **Windows SmartScreen** shows a warning (*"Windows protected your PC"*), this is expected for unsigned builds:
   - Click **More info**
   - Click **Run anyway**
4. The app should open showing the Teto Red themed interface.

**If it doesn't launch at all:**
- Make sure you downloaded the correct 64-bit build for your system.
- Try running it from a terminal (`cmd` or PowerShell) instead of double-clicking, so you can see any error output:
  ```powershell
  .\TetoMidi.exe
  ```

### Linux (terminal)

Download and run the prebuilt Linux binary directly from a terminal:

```bash
# 1. Download the binary
#    (replace the URL below with the actual release asset link from your repo's Releases page)
curl -L -o TetoMidi https://github.com/XibeoFlower/Tetomidi-hub/releases/latest/download/TetoMidi

# 2. Make it executable
chmod +x TetoMidi

# 3. Run it
./TetoMidi
```

**If the app fails to launch with missing library errors**, install the required GUI/Qt dependencies first:

```bash
sudo apt-get update
sudo apt-get install -y \
    libgl1 libegl1 libxkbcommon0 libxkbcommon-x11-0 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 \
    libdbus-1-3 libfontconfig1
```

Then try running `./TetoMidi` again.

*(Package names above are for Debian/Ubuntu-based systems via `apt`. On Fedora/Arch/other distros, install the equivalent packages using `dnf`, `pacman`, etc.)*

### Build from Source

If you'd rather build the app yourself instead of using a prebuilt binary:

```bash
# Clone the repository
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub

# --- Linux ---
chmod +x build_linux.sh
./build_linux.sh
./dist/TetoMidi

# --- Windows (run in cmd, not WSL) ---
build_windows.bat
dist\TetoMidi.exe
```

Both build scripts will:
1. Create a local Python virtual environment (`venv/`)
2. Install dependencies from `requirements.txt` plus `pyinstaller` (and `pillow`, for Windows icon conversion)
3. Clean any previous `build/`/`dist/` output
4. Package the app into a single executable using PyInstaller

You can also trigger an automated build via **GitHub Actions** — see `.github/workflows/build.yml` in the repo. It builds both Windows and Linux versions automatically on every push to `main`, with results downloadable from the **Actions** tab as build artifacts.

---

## Requirements

- **Windows:** Windows 10 or 11, 64-bit
- **Linux:** Any modern 64-bit desktop distro with Qt6-compatible GUI libraries (see the `apt-get install` list above)
- **To build from source:** Python 3.10+ and the packages listed in `requirements.txt`
- A `.mid` file, or sheet-music text in a supported format (e.g. Virtual Piano notation), to play

---

## Project Structure

```
Tetomidi-hub/
├── backup/            # Backup/versioned data
├── controllers/        # App control logic (connects UI actions to core logic)
├── core/                # Core MIDI/playback engine
├── managers/            # State, settings, and session managers
├── ui/                  # Interface code, including theme.py (color themes & stylesheet engine)
├── icon.ico             # Windows app icon
├── icon.icns            # macOS app icon
├── main.py              # App entry point
├── requirements.txt     # Python dependencies
├── ruff.toml            # Linter configuration
├── build_windows.bat    # Local Windows build script (PyInstaller)
├── build_linux.sh       # Local Linux build script (PyInstaller)
└── .github/workflows/build.yml   # CI: automated Windows + Linux builds
```

---

## Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| App won't open on Windows | SmartScreen is blocking it — click **More info → Run anyway**. If it still fails, run from `cmd`/PowerShell to see the error message. |
| App won't open on Linux | Missing Qt/GUI system libraries — install the packages listed under [Linux (terminal)](#linux-terminal). |
| No sound / notes not playing | Check that a `.mid` file is actually loaded (see the MIDI File section — it should not say *"No file selected"*), or that sheet text was pasted correctly in the Translator tab. |
| Keys aren't reaching the game (Roblox) | Make sure the Roblox window is focused before the Countdown ends — key presses go to whichever window currently has focus. |
| Notes are out of range in-game | Adjust **Transpose** and/or toggle **88-Key Layout** to match the target piano's actual range. |
| Build fails with an icon-format error | Make sure `icon.ico` is a real multi-size `.ico` file (not a renamed `.png`/other format), and that `pillow` is installed alongside `pyinstaller` so PyInstaller can auto-convert if needed. |
| Playback sounds too "perfect"/robotic | Enable Humanization options — see the [Humanization Options (Detailed)](#humanization-options-detailed) table above. |

---

## FAQ

**Q: Do I need to install anything else to run the Windows `.exe`?**
No — it's a self-contained onefile build. Just download and run it.

**Q: Can I use my own MIDI files?**
Yes — any standard `.mid` file can be loaded via **Playback → Browse…**.

**Q: What sheet formats does the Translator support?**
Currently **Virtual Piano** notation is supported; more formats may be added later via the **Format** dropdown.

**Q: Will this get me banned on Roblox?**
Automating input can violate a game's Terms of Service and may be detected by anti-cheat/anti-macro systems. Use at your own risk — this tool doesn't guarantee safety from in-game penalties.

**Q: How do I change the app's color theme?**
Go to **Settings** and pick from the 8 built-in themes (see [Themes](#themes)).

---

## License / Credits

Add your license (e.g. MIT, GPL-3.0) and any credits here.
