🎹 Teto Midi
Teto Midi is a desktop MIDI player and audio-to-MIDI transcription tool built with Python and PyQt6.
It is designed for virtual piano and guitar applications, especially games and software that receive keyboard input. Teto Midi can load MIDI files, simulate keyboard presses, visualize notes, translate sheet music, and convert audio recordings such as MP3 files into MIDI.
Current version: 3.4 beta
✨ Features
🎹 MIDI Playback
Load .mid and .midi files
Automatically map MIDI notes to keyboard keys
Support for 61-key and 88-key layouts
Select individual MIDI tracks before playback
Adjustable tempo
Transpose support
Play / Pause / Resume / Stop
Global playback hotkey
🎸 Guitar Mode
Guitar-specific MIDI mapping
Interactive fretboard visualizer
Guitar-oriented playback
Visualize currently active notes
🎵 MP3 → MIDI Transcriber
Convert audio recordings into MIDI files directly inside Teto Midi.
Supported audio formats include:
.mp3
.wav
.flac
.m4a
.ogg
.aac
.wma
The audio loader automatically converts the input to mono 44.1 kHz audio, which is required by the TransKun transcription engine.
👁️ Visualizer
Piano keyboard visualization
Piano-roll style timeline
Real-time note visualization
Playback position tracking
📝 Sheet Music Translator
Import sheet music
Convert supported sheet formats into playable notes
Play translated music
Export translated data to supported formats
🧠 Humanization
Make MIDI playback sound and behave more naturally.
Available features include:
Timing variation
Chord rolling
Velocity variation
Articulation variation
Tempo sway
Mistake simulation
Drift correction
Hand simulation
🦶 Smart Pedal
Multiple pedal modes are available:
Auto
PedalAI
Harmonic
Rhythmic
None
🎨 Customization
English / Vietnamese interface
Custom themes
Always-on-top mode
Window opacity
Mini / collapsed mode
Custom playback hotkey
📋 Requirements
Windows
Recommended:
Windows 10 or newer
Python 3.10+
Git
Internet connection for installing dependencies
Linux
Required:
Python 3.10+
Git
PyQt6 system libraries
pynput
Linux distributions using Wayland may require additional permissions for keyboard input simulation.
📥 Installation
Option 1 — Run from Source
1. Clone the repository
Open Terminal, PowerShell, or Command Prompt:
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub
2. Create a virtual environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python3 -m venv venv
source venv/bin/activate
3. Update pip
python -m pip install --upgrade pip
4. Install dependencies
pip install -r requirements.txt
5. Start Teto Midi
Windows
python main.py
Linux / macOS
python3 main.py
🚀 First Launch
After starting the application, you will see the main Teto Midi interface.
The application contains several main tabs:
Tab	Description
Playback	Load and play MIDI files
Guitar	Guitar mode and fretboard visualization
Transcriber	Convert audio files into MIDI
Visualizer	View notes and playback timeline
Translator	Convert sheet music into playable notes
Settings	Configure language, hotkeys, theme, and other options
🎵 MP3 → MIDI Transcription
The Transcriber allows you to turn an audio recording into a MIDI file.
Step 1 — Open Transcriber
Start Teto Midi and open:
Transcriber
Step 2 — Select an Audio File
Choose your audio file.
For example:
song.mp3
Supported formats:
MP3
WAV
FLAC
M4A
OGG
AAC
WMA
The application automatically loads the audio and prepares it for transcription.
Internally, the audio is converted to:
Mono
44,100 Hz
This format is required by the TransKun transcription engine.
Step 3 — Start Transcription
Start the transcription process from the Transcriber interface.
The application analyzes the audio and attempts to detect musical notes and timing.
Depending on the audio length and your computer, transcription may take some time.
Step 4 — Wait for Completion
Do not close the application while transcription is running.
When the process finishes, Teto Midi generates a MIDI file.
For example:
song.mid
Step 5 — Load the Generated MIDI
The generated MIDI can be sent directly to the Playback tab.
Teto Midi automatically loads the transcribed MIDI into Playback after a successful transcription.
You can then select the tracks and configure playback.
🎧 Tips for Better MP3 → MIDI Results
Audio-to-MIDI transcription is an estimation process. Results depend heavily on the source audio.
For the best results:
Recommended
Use high-quality audio
Use clear instruments
Prefer isolated melodies
Use clean recordings
Avoid excessive background noise
Avoid heavily distorted audio
More difficult
Full songs containing:
Vocals
Drums
Bass
Multiple instruments
Heavy effects
Reverb
Large chords
may produce inaccurate notes.
For complex songs, the generated MIDI may require editing inside a DAW or MIDI editor.
🎹 Playing a MIDI File
Step 1 — Open Playback
Go to:
Playback
Step 2 — Load MIDI
Click:
Browse...
Select:
song.mid
or:
song.midi
Step 3 — Select Tracks
After loading the MIDI, Teto Midi displays the available tracks.
Select the tracks you want to play.
For example:
☑ Piano
☐ Bass
☐ Drums
☑ Melody
Confirm your selection.
Step 4 — Configure Playback
You can adjust:
Tempo
Transpose
Keyboard layout
Instrument
Humanization
Pedal
Other playback options
Step 5 — Start Playback
Click:
Play
Teto Midi will simulate keyboard input based on the MIDI notes.
The target game or application receives those inputs as keyboard events.
⌨️ Playback Hotkey
Teto Midi supports a global playback hotkey.
The hotkey can be used to:
Play
Pause
Resume
To change the hotkey:
Open Settings
Find the Hotkey option
Click the hotkey configuration button
Press the key you want to use
Save the configuration
If the global hotkey is unavailable, the normal on-screen Play / Stop controls can still be used.
🎸 Guitar Mode
Teto Midi includes a dedicated Guitar mode.
Step 1
Open:
Guitar
Step 2
Load a MIDI file.
Step 3
Select the desired MIDI tracks.
Step 4
Use the guitar fretboard visualizer to see the notes being played.
Step 5
Start playback.
Guitar Mode uses guitar-specific note mapping and disables the 88-key piano layout for guitar playback.
👁️ Visualizer
The Visualizer provides a real-time view of MIDI playback.
It includes:
Piano Keyboard
Shows currently active MIDI notes.
Timeline
Displays the position of notes throughout the song.
Playback Position
The timeline follows the current playback position.
You can use the timeline to inspect different parts of a MIDI file.
📝 Translator
The Translator allows you to work with supported sheet-music formats.
Typical workflow:
Sheet Music
     ↓
Translator
     ↓
Parsed Notes
     ↓
MIDI Playback
Basic Usage
Open Translator
Paste or import your sheet music
Select the appropriate format
Set the BPM
Choose whether humanization should be used
Click Play or export the result
The translated notes can use the selected keyboard layout and instrument settings.
🧠 Humanization
Humanization modifies MIDI playback so that every note does not behave in exactly the same way.
Depending on the selected options, Teto Midi can introduce:
Timing variation
Velocity variation
Chord roll
Articulation variation
Tempo sway
Small playing mistakes
Drift correction
Simulated hand behavior
When should I use Humanization?
Use it when you want playback to feel less mechanically perfect.
For highly accurate timing, disable humanization.
For a more natural performance, enable the features you need.
🦶 Smart Pedal
Teto Midi provides several pedal modes.
Mode	Description
Auto	Automatically handles pedal behavior
PedalAI	AI-assisted pedal behavior
Harmonic	Harmonic-based pedal behavior
Rhythmic	Rhythm-oriented pedal behavior
None	Disable pedal simulation
If you are unsure which mode to use, start with:
Auto
⚙️ Settings
The Settings tab contains application-wide configuration.
Available options include:
Language
Supported languages:
English
Vietnamese
After changing the language, restart the application to fully apply the new language.
Always on Top
Keeps Teto Midi above other windows.
Useful when playing a game while monitoring the MIDI visualizer.
Opacity
Change the transparency of the application window.
Theme
Change the application's visual theme.
Save Directory
Choose where Teto Midi stores saved performance data.
Hotkey
Configure the global playback hotkey.
Update
Use:
Check for updates
to manually check for a newer version.
💾 Saving Humanized Performances
Teto Midi can save humanized performance data.
This allows you to reuse a customized performance without rebuilding the same humanization settings every time.
To load a saved performance:
Open Playback
Choose the saved-performance loading option
Select your saved file
Start playback
🔄 Updating Teto Midi
If you installed Teto Midi from source:
cd Tetomidi-hub
git pull
Activate your virtual environment:
Windows
venv\Scripts\activate
Linux / macOS
source venv/bin/activate
Then update dependencies:
pip install -r requirements.txt
You can also use the application's built-in:
Check for updates
option.
🏗️ Building a Standalone Application
Teto Midi includes build scripts for creating standalone builds.
Linux
chmod +x build_linux.sh
./build_linux.sh
The generated application should appear under:
dist/TetoMidi
Run it with:
./dist/TetoMidi
Windows
The repository also contains:
build_windows.bat
Run the batch file from a Windows environment to build the application.
🐧 Linux Troubleshooting
Keyboard input does not work
Teto Midi uses pynput to simulate keyboard input.
Some Linux environments restrict keyboard injection, especially Wayland sessions.
Ubuntu / Debian
Try:
sudo apt install python3-pynput
Fedora / RHEL
Try:
sudo dnf install python3-pynput
If keyboard input still does not work, try using an X11 session instead of Wayland.
❌ MP3 Cannot Be Loaded
Make sure your file uses one of the supported extensions:
.mp3
.wav
.flac
.m4a
.ogg
.aac
.wma
If the file is corrupted or uses an unusual codec, convert it to WAV or MP3 and try again.
❌ Transcription Fails
If audio transcription fails:
Make sure the audio file can be played normally.
Try a shorter audio file.
Try converting the file to WAV.
Make sure all Python dependencies are installed.
Restart Teto Midi.
Check the application's log output for the actual error.
❌ MIDI Sounds Wrong
Audio-to-MIDI conversion cannot perfectly reproduce every recording.
Possible causes include:
Multiple instruments playing simultaneously
Background noise
Reverb
Distortion
Complex chords
Unclear note attacks
Drums or percussion
Poor audio quality
Try using a cleaner or more isolated recording.
📁 Project Structure
Tetomidi-hub/
│
├── .github/
│   └── workflows/
│
├── backup/
│
├── controllers/
│
├── core/
│
├── managers/
│
├── transcriber/
│   ├── audio_loader.py
│   ├── spectral_engine.py
│   └── transkun_engine.py
│
├── ui/
│
├── main.py
├── requirements.txt
├── build_linux.sh
├── build_windows.bat
├── ruff.toml
│
├── icon.ico
├── icon.icns
└── teto-midi-logo.svg
The Transcriber subsystem is separated into audio loading, spectral processing, and TransKun engine components.
📦 Main Dependencies
The project uses several Python libraries, including:
PyQt6
mido
numpy
pynput
The audio transcription subsystem additionally uses audio-processing dependencies such as librosa and soundfile.
🔗 Workflow Overview
A typical MP3-to-MIDI workflow looks like this:
┌──────────────┐
│   Audio File │
│ MP3 / WAV... │
└──────┬───────┘
       │
       ▼
┌────────────────┐
│    Transcriber │
└──────┬─────────┘
       │
       ▼
┌────────────────┐
│ Audio Analysis │
└──────┬─────────┘
       │
       ▼
┌────────────────┐
│ MIDI Generation│
└──────┬─────────┘
       │
       ▼
┌────────────────┐
│    Playback    │
└──────┬─────────┘
       │
       ▼
┌────────────────┐
│ Keyboard Input │
└────────────────┘
The current application also bridges a successfully transcribed MIDI file directly into the Playback interface.
🎯 Recommended Workflow
For a normal song:
1. Start Teto Midi
2. Open Transcriber
3. Select your MP3
4. Run transcription
5. Wait for the MIDI to be generated
6. Open / continue to Playback
7. Select MIDI tracks
8. Adjust tempo
9. Configure humanization if needed
10. Configure pedal
11. Press Play
For a MIDI file you already have:
1. Open Playback
2. Browse for the MIDI file
3. Select tracks
4. Configure playback
5. Press Play
For guitar:
1. Open Guitar
2. Load MIDI
3. Select tracks
4. Check the fretboard
5. Start playback
⚠️ Important Notes
Teto Midi simulates keyboard input. The behavior of simulated keyboard input depends on the operating system and the target application.
Some games and applications may block or restrict synthetic keyboard input.
Use Teto Midi responsibly and follow the rules of the software or game you are using.
Audio-to-MIDI transcription is not guaranteed to be 100% accurate. Always review generated MIDI data when accuracy is important.
🛠️ Development
Clone the repository:
git clone https://github.com/XibeoFlower/Tetomidi-hub.git
cd Tetomidi-hub
Create the environment:
python -m venv venv
Activate it and install dependencies:
pip install -r requirements.txt
Run:
python main.py
🤝 Contributing
Contributions are welcome.
If you find a bug or have an idea:
Open an Issue
Describe the problem clearly
Include your operating system
Include relevant error messages or logs
Explain how to reproduce the issue
Pull requests are also welcome.
🐛 Bug Reports
When reporting a bug, please include:
Operating System:
Python Version:
Teto Midi Version:
Audio/MIDI Format:
Steps to Reproduce:
Error Message:
This makes troubleshooting much easier.
💬 Support
For support, open a GitHub Issue or contact:
Discord: @xiunolove
📄 License
Please refer to the repository's license information for the current licensing terms.
❤️ Credits
Made with ❤️ by XibeoFlower
Repository:
https://github.com/XibeoFlower/Tetomidi-hub
If Teto Midi is useful to you, consider giving the project a ⭐ on GitHub!
⭐ Teto Midi
Turn audio into MIDI.
Turn MIDI into keyboard input.
Play music your way. 🎹
