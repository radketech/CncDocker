# CnC Docker - Red Alert Match Overlay for OBS

A Python utility that monitors C&C Red Alert game logs, fetches live match data from the coordinator API, and generates a real-time HTML overlay for OBS/Streamlabs OBS streaming. The overlay displays player names, ELOs, starting positions, and faction flags.

## Features

- **Real-time Log Monitoring**: Detects when a quickmatch starts and immediately fetches match details
- **Live API Integration**: Queries the C&C Red Alert coordinator API for accurate player and match information
- **OBS-Friendly Overlay**: Generates a transparent HTML overlay with:
  - Player names (with octal escape sequence decoding)
  - ELO ratings
  - Starting positions (human-readable map labels)
  - Faction flags (displayed as embedded SVG images)
  - Dynamic layout that adjusts to the number of players
  - Automatic refresh and polling for live updates
- **PyInstaller Bundled**: Distributes as a Windows `.exe` executable for easy end-user deployment
- **Flag Embedding**: SVGs are embedded as data URIs, eliminating CEF/OBS local file access issues

## System Requirements

- Windows 10+ (or Python 3.13+ on any OS)
- C&C Red Alert game with network log file access
- OBS / Streamlabs OBS

## Installation

### Option 1: Pre-built Windows Executable

1. Download `CnCDocker.exe` from the [Releases](../../releases) page
2. Run the executable
3. Configure the log file path in the GUI (typically: `C:\Program Files\Westwood Online\Red Alert\LogFile_0.txt`)
4. Click "Run" to start monitoring
5. In OBS, add a Browser source and set the file path to `match_info.html` (created in the same folder as the exe)

### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/radketech/CncDocker.git
cd CncDocker

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python CnCDocker
```

## Usage

### GUI Application (CnCDocker.exe or CnCDocker script)

1. **Select Log File**: Browse to your Red Alert `LogFile_0.txt`
2. **Click Run**: Starts monitoring the log file in the background
3. **Add to OBS**: Add a Browser source to your OBS scene pointing to the generated `match_info.html` file

The application will:
- Display "Waiting for match..." in the overlay until a match is detected
- Automatically fetch match data when a quickmatch starts
- Update the overlay with live player information
- Continue updating every 2 seconds via JavaScript polling (independent of OBS framerate)

### Command-Line Test Runner

Generate and preview a sample overlay without running a match:

```bash
# Generate sample overlay
python .\scripts\generate_sample_overlay.py

# Generate and open in default browser
python .\scripts\generate_sample_overlay.py --open

# Generate placeholder overlay
python .\scripts\generate_sample_overlay.py --placeholder

# Specify output directory
python .\scripts\generate_sample_overlay.py --output-dir C:\temp --open
```

## Configuration

### Overlay Output Path

By default, the overlay is written to the same directory as the executable (or script). You can customize this by modifying the `output_dir` parameter in the code or through environment variables.

### Log File Format

The application expects the standard C&C Red Alert `LogFile_0.txt` which contains:
- Session initialization messages
- "quickmatchfound" event line with match/session details

### API Coordinator

The app queries the C&C Red Alert coordinator API (typically at `coordinator.westwood-online.com`) to fetch:
- Current match information
- Player details (name, ELO, faction, start position)

## Architecture

### Main Files

- **CnCDocker**: Main GUI application (tkinter-based)
- **log_monitor.py**: Core logic for file tailing, log parsing, and API integration
- **generate_overlay.py**: HTML overlay generation with data URI flag embedding
- **scripts/generate_sample_overlay.py**: Test runner for manual overlay testing

### How It Works

1. **Log Tailing**: `tail_log_file()` reads the log incrementally, detecting file truncation (new game session)
2. **Match Detection**: Looks for "quickmatchfound" event and extracts session/match IDs
3. **API Query**: `get_matches()` calls the coordinator API with retry logic (up to 3 attempts)
4. **Player Parsing**: Decodes octal-escaped names, extracts Steam IDs and factions
5. **HTML Generation**: `generate_match_webpage()` produces an overlay with:
   - Data URI-embedded SVG flags (avoids CEF file access issues)
   - Meta-refresh + JavaScript polling for live updates
   - Fully transparent background for OBS compatibility
6. **OBS Display**: Browser source renders the overlay with transparency enabled

## OBS Configuration

### Browser Source Settings

1. **URL or Local File**: Point to the generated `match_info.html` file
2. **Width**: 1200px (or adjust based on player count)
3. **Height**: 200px
4. **Transparency**: Enabled (OBS should auto-detect from the HTML `background: transparent`)
5. **Hardware Acceleration**: Optional (usually enabled by default)

### Troubleshooting OBS Transparency

If the overlay background appears black instead of transparent:
1. Ensure the Browser source has transparency enabled
2. Try using a local HTTP server instead of `file://` URLs:
   ```powershell
   cd C:\path\to\CnCDocker
   python -m http.server 8000
   # Use http://127.0.0.1:8000/match_info.html in the Browser source
   ```
3. Check that your OBS version supports CEF browser source transparency

## Development

### Building the Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build using the provided spec
.\venv\Scripts\python.exe -m PyInstaller CnCDocker.spec --clean -y

# Executable will be in: dist/CnCDocker.exe
```

### Running Tests

```bash
# Generate a sample overlay with test data
python .\scripts\generate_sample_overlay.py --open
```

## License

[See LICENSE file](LICENSE)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes with clear messages
4. Push to your fork
5. Open a Pull Request

## Troubleshooting

### Overlay not appearing in OBS
- Verify the file path in the Browser source points to `match_info.html`
- Check that OBS has read permissions to the file
- Try the local HTTP server approach (see OBS Configuration)

### Flags not rendering
- Ensure the `Flags/` directory is in the same folder as the `.exe` or script
- Check browser console in OBS (right-click Browser source → Interact)
- Data URIs should be embedded; if not, ensure `generate_overlay.py` can read SVG files

### Players not updating during matches
- Verify the log file path is correct
- Confirm the coordinator API is accessible from your network
- Check that the game session ID is being correctly parsed from logs
- Enable JavaScript in OBS Browser source settings

### High CPU usage
- The polling interval is set to 2 seconds; reduce by editing `html_template` in `generate_overlay.py`
- Ensure no other heavy processes are using the log file

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](../../issues).

---

**Version**: 1.0.0  
**Last Updated**: December 2024
