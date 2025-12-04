"""Small CLI/test runner to generate a sample overlay for manual testing.

Usage:
  python scripts/generate_sample_overlay.py [--output-dir DIR] [--open] [--placeholder]

This will write `match_info.html` into the target directory (defaults to repo root)
and optionally open it in the default browser so you can verify flags and transparency
in OBS or a regular browser.
"""
import os
import sys
import argparse
import webbrowser
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

try:
    from generate_overlay import generate_match_webpage, generate_placeholder_overlay
except Exception as e:
    print(f"ERROR importing generate_overlay: {e}")
    raise


SAMPLE_PLAYERS = [
    {
        'name': 'Alpha\\101',  # contains octal escape example
        'elo': 1523,
        'start_position': 0,
        'color': 0,
        'faction': 4,
    },
    {
        'name': 'Bravo',
        'elo': 1689,
        'start_position': 1,
        'color': 2,
        'faction': 6,
    },
    {
        'name': 'CharlieWithAVeryLongNameThatGetsTruncated',
        'elo': 1400,
        'start_position': 2,
        'color': 5,
        'faction': 1,
    },
]


def file_url(path):
    p = os.path.abspath(path).replace('\\', '/')
    if os.name == 'nt' and not p.startswith('/'):
        return f'file:///{p}'
    return f'file://{p}'


def main():
    ap = argparse.ArgumentParser(description='Generate a sample match overlay for testing.')
    ap.add_argument('--output-dir', '-o', default=ROOT, help='Directory to write match_info.html')
    ap.add_argument('--open', action='store_true', help='Open the generated file in the default browser')
    ap.add_argument('--placeholder', action='store_true', help='Generate placeholder overlay instead of sample match')
    ap.add_argument('--name', default='match_info.html', help='Output HTML filename')
    args = ap.parse_args()

    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.placeholder:
        path = generate_placeholder_overlay(output_dir=out_dir, html_name=args.name)
    else:
        # Use a friendly map name key that the overlay may not know; code will display "Unknown Map"
        path = generate_match_webpage(SAMPLE_PLAYERS, map_name='MOBIUS_RED_ALERT_MULTIPLAYER_123_MAP', output_dir=out_dir, html_name=args.name)

    if not path:
        print('Failed to generate overlay.')
        sys.exit(2)

    print('Generated:', os.path.abspath(path))

    if args.open:
        url = file_url(path)
        print('Opening in default browser:', url)
        webbrowser.open(url)


if __name__ == '__main__':
    main()
