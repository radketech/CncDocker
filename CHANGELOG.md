# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-12-04

### Added
- Initial public release
- Real-time log file monitoring for C&C Red Alert quickmatches
- Coordinator API integration with retry logic (up to 3 attempts)
- Player information parsing including:
  - Steam ID extraction
  - Faction detection and mapping
  - Octal escape sequence decoding for player names
  - ELO rating display
- HTML overlay generation with modern futuristic CSS styling
- SVG flag embedding as data URIs for OBS compatibility
- Dynamic container width calculation based on player count
- JavaScript polling mechanism (2-second interval) for live updates independent of OBS framerate
- Transparent background support for OBS/Streamlabs OBS
- PyInstaller bundling with asset inclusion (Flags directory)
- Windows `.exe` executable distribution
- Test/sample overlay generator (`scripts/generate_sample_overlay.py`)
- Comprehensive documentation (README.md, CHANGELOG.md)

### Fixed
- CEF/OBS local file access issues by embedding SVG flags as data URIs
- Overlay transparency support in Streamlabs OBS by removing opaque outer background
- Thread argument passing (ensure tuple format for thread args)
- Meta-refresh dependency by adding JavaScript polling fallback

### Changed
- Refactored `tail_log_file()` into separate `log_monitor.py` module for code cleanliness
- Removed background blur and opaque overlay container for full transparency
- Implemented safe HTML template + token replacement instead of f-string embedding for JavaScript/CSS
- Player box shadows reduced for better transparency appearance

### Technical Details
- Python 3.13
- Dependencies: tkinter (built-in), requests, (see requirements.txt)
- Bundling: PyInstaller with custom spec for Windows distribution
- API: C&C Red Alert Coordinator (westwood-online.com)

---

## Version History

### Planning & Development
- Log monitoring and incremental file tailing
- Robust file truncation detection
- Coordinator API integration with exponential retry backoff
- Player name octal-decoding
- Faction-to-flag mapping
- Overlay HTML generation with dynamic styling
- OBS transparency and CEF compatibility fixes
