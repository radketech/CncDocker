"""
Module to generate a static HTML overlay with meta-refresh.
Decodes octal escape sequences in player names.
"""

import os
import html
import re
import sys
import urllib.parse
from datetime import datetime


def generate_placeholder_overlay(output_dir=None, html_name="match_info.html"):
    """
    Generate a placeholder overlay HTML file while waiting for a match.
    This allows users to add the file to OBS before starting to play.
    
    Args:
        output_dir (str): Output directory. Defaults to module directory.
        html_name (str): Output HTML filename.
    
    Returns:
        str: Path to generated HTML file, or None on error.
    """
    if output_dir is None:
        output_dir = os.path.dirname(__file__)

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass

    html_content = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Match Overlay</title>
    <style>
        /* Futuristic / modern styles */
        html, body {{ height:100%; background: transparent !important; }}
        body {{ margin:0; padding:0; font-family: 'Orbitron', 'Segoe UI', Tahoma, Arial, sans-serif; background: transparent !important; color: #e6f0ff; }}
        /* Removed opaque outer background to ensure OBS transparency works (Streamlabs/CEF) */
        .wrap {{ padding: 18px; box-sizing: border-box; background: transparent; border-radius: 0; backdrop-filter: none; width: 420px; }}
        .placeholder {{ font-size: 24px; font-weight: 800; color: #9ff0ff; text-align: center; letter-spacing: 0.6px; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 0 4px 12px rgba(0,0,0,0.6); }}
    </style>
</head>
<body>
    <div class="wrap">
        <div class="placeholder">⏳ Waiting for match...</div>
    </div>
</body>
</html>
"""

    html_path = os.path.join(output_dir, html_name)

    try:
        with open(html_path, 'w', encoding='utf-8') as hf:
            hf.write(html_content)
        print(f"Placeholder overlay created: {os.path.abspath(html_path)}")
        return html_path
    except Exception as e:
        print(f"ERROR writing placeholder overlay: {e}")
        return None


def decode_octal_escapes(s):
    """
    Decode octal escape sequences like \\314\\265 to their UTF-8 characters.
    
    Example: "/\\314\\265\\315\\207..." -> actual Unicode text
    """
    if not s:
        return s
    
    try:
        # Replace octal sequences \nnn with their byte values
        def octal_to_byte(match):
            octal_str = match.group(1)
            byte_val = int(octal_str, 8)
            return chr(byte_val)
        
        # Match backslash followed by 1-3 octal digits
        decoded = re.sub(r'\\(\d{1,3})', octal_to_byte, s)
        return decoded
    except Exception as e:
        print(f"Warning: Failed to decode octal in '{s}': {e}")
        return s


def _get_resource_dir():
    """Return the directory where bundled resources live.

    When running under PyInstaller one-file, resources are unpacked into
    sys._MEIPASS. Otherwise use the module directory.
    """
    try:
        return getattr(sys, '_MEIPASS')
    except Exception:
        return os.path.dirname(__file__)


def _flag_to_data_uri(flag_filename, output_dir=None):
    """Return a data URI for the given SVG flag, or fallback to a file:// URL.

    The function tries these locations in order:
    - bundled resource directory (PyInstaller _MEIPASS or module dir)/Flags/<flag_filename>
    - output_dir/Flags/<flag_filename>
    If a file is found, it's URL-encoded and returned as a data:image/svg+xml URI to
    avoid CEF/OBS local-file access quirks.
    """
    if not flag_filename:
        return None

    locations = []
    # resource dir (handles PyInstaller)
    res_dir = _get_resource_dir()
    locations.append(os.path.join(res_dir, 'Flags', flag_filename))
    # output_dir (where HTML is written)
    if output_dir:
        locations.append(os.path.join(output_dir, 'Flags', flag_filename))
    # fallback to project-relative
    locations.append(os.path.join(os.path.dirname(__file__), 'Flags', flag_filename))

    for p in locations:
        try:
            if os.path.exists(p):
                # Read SVG and produce a data URI
                with open(p, 'rb') as fh:
                    data = fh.read()
                try:
                    text = data.decode('utf-8')
                except Exception:
                    # If decoding fails, base64-encode instead
                    import base64
                    b64 = base64.b64encode(data).decode('ascii')
                    return f'data:image/svg+xml;base64,{b64}'

                # URL-encode the SVG text for safe inclusion
                svg_escaped = urllib.parse.quote(text)
                return f'data:image/svg+xml;utf8,{svg_escaped}'
        except Exception:
            continue

    # If none found, try a best-effort absolute file:// path using output_dir or module dir
    fallback = None
    try:
        fallback_path = os.path.abspath(os.path.join(output_dir or os.path.dirname(__file__), 'Flags', flag_filename))
        fallback_url = fallback_path.replace('\\', '/')
        if os.name == 'nt':
            fallback = f'file:///{fallback_url}'
        else:
            fallback = f'file://{fallback_url}'
    except Exception:
        fallback = None

    return fallback


def generate_match_webpage(players_info, map_name, output_dir=None, refresh_interval=5,
                           html_name="match_info.html"):
    """
    Generate a static HTML overlay with meta-refresh.
    
    Args:
        players_info (list): List of dicts with keys: 'name', 'elo', 'start_position', 'color', etc.
        map_name (str): Map name string.
        output_dir (str): Output directory. Defaults to module directory.
        refresh_interval (int): Page refresh interval in seconds. Default 5.
        html_name (str): Output HTML filename.
    
    Returns:
        str: Path to generated HTML file, or None on error.
    """
    if output_dir is None:
        output_dir = os.path.dirname(__file__)

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception:
        pass

    color_map = {
        0: "#FFFF00",
        1: "#00FFFF",
        2: "#FF3333",
        3: "#00FF00",
        4: "#FFA500",
        5: "#3366FF",
        6: "#800080",
        7: "#FF69B4",
    }

    # Map faction numbers to flag filenames in the Flags/ directory
    flag_map = {
        4: "su.svg",
        6: "ua.svg",
        1: "tr.svg",
        8: "fr.svg",
        7: "de.svg",
        3: "gr.svg",
        2: "es.svg",
        5: "gb.svg",
    }

    # (safe_map will be derived from the friendly mapping below; do not expose raw map keys)

    # Map-specific display names and start-position labels
    map_position_mappings = {
        "MOBIUS_RED_ALERT_MULTIPLAYER_123_MAP": {
            "display": "Bullseye",
            "positions": {
                0: "Top Right",
                1: "Bot Left",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_COMMUNITY_2_MAP": {
            "display": "Tournament Arena",
            "positions": {
                0: "Bot Right",
                1: "Top Left",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_22_MAP": {
            "display": "Path Beyond",
            "positions": {                
                0: "Bot Right",
                1: "Top Left",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_COMMUNITY_3_MAP": {
            "display": "Ore Rift",
            "positions": {
                0: "Left",
                1: "Right",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_5_MAP": {
            "display": "Keep Off the Grass",
            "positions": {
                0: "Top Left",
                1: "Bot Right",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_COMMUNITY_1_MAP": {
            "display": "Canyon",
            "positions": {
                0: "Top Right",
                1: "Bot Left",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_K0_MAP": {
            "display": "Arena Valley",
            "positions": {
                0: "Bot Right",
                1: "Top Left",
            }
        },
        "MOBIUS_RED_ALERT_MULTIPLAYER_9_MAP": {
            "display": "North by Northwest",
            "positions": {
                0: "Top Right",
                1: "Right Top",
                2: "Right Bot",
                3: "Bot Right",
                4: "Bot Left",
                5: "Left Bot",
                6: "Left Top",
                7: "Top Left",
            }
        },
    }

    def get_position_label(map_key, pos):
        try:
            info = map_position_mappings.get(map_key, None)
            if info and isinstance(pos, int):
                return info["positions"].get(pos, str(pos))
        except Exception:
            pass
        return str(pos)

    # Prefer friendly display name when available; do NOT show raw map keys
    try:
        map_info = map_position_mappings.get(str(map_name), None)
        display_map = map_info.get("display") if map_info else None
    except Exception:
        display_map = None
    # If no friendly name is available, show a generic placeholder (do not expose raw map key)
    display_map = display_map or "Unknown Map"
    safe_map = html.escape(str(display_map))

    # Build player HTML rows
    player_html = ""
    if players_info:
        for p in players_info:
            name = p.get("name", "Unknown")
            # Decode octal escapes in the name
            name = decode_octal_escapes(name)
            name = html.escape(name)
            
            elo = p.get("elo", "N/A")
            if isinstance(elo, (int, float)):
                elo_text = f"{elo:.0f}"
            else:
                elo_text = html.escape(str(elo))
            
            start = p.get("start_position", "-")
            color_idx = p.get("color", None)
            try:
                color_hex = color_map.get(int(color_idx), "#CCCCCC")
            except Exception:
                color_hex = "#CCCCCC"

            faction = p.get("faction", None)
            faction_text = html.escape(str(faction)) if faction is not None else ""

            # Map start position to human-readable label where possible
            try:
                start_int = int(start)
            except Exception:
                start_int = None
            if start_int is not None:
                start_label = get_position_label(str(map_name), start_int)
            else:
                start_label = str(start)
            # Only show start position in the left meta; faction is represented by the flag image
            left_meta = f"Start: {html.escape(str(start_label))}"
            # Determine flag path, if available
            flag_filename = None
            try:
                faction_val = p.get("faction", None)
                if faction_val is not None:
                    faction_int = int(faction_val)
                    flag_filename = flag_map.get(faction_int)
            except Exception:
                flag_filename = None

            flag_html = ""
            if flag_filename:
                # Prefer embedding the SVG as a data URI so OBS/CEF can render it
                flag_src = _flag_to_data_uri(flag_filename, output_dir=output_dir)
                if flag_src:
                    flag_html = f"<img class=\"flag\" src=\"{flag_src}\" alt=\"flag\">"
                else:
                    # Last-resort: use a relative path
                    flag_path = os.path.join("Flags", flag_filename).replace('\\', '/')
                    flag_html = f"<img class=\"flag\" src=\"{flag_path}\" alt=\"flag\">"

            # render player block with left column (name + meta) and right column (elo)
            player_html += f"""
            <div class="player">
                {flag_html}
                <div class="player-left">
                    <div class="name-box" style="border-color:{color_hex};">{name}</div>
                    <div class="meta"><div class="left">{left_meta}</div><div class="elo">{elo_text}</div></div>
                </div>
            </div>
"""
    else:
        player_html = """
      <div class="player">
        <div class="name-box" style="background:#666; color:#fff;">No players</div>
      </div>
"""

    # Compute container width so it fits the player boxes snugly but doesn't leave excessive empty space.
    try:
        players_count = len(players_info) if players_info else 1
    except Exception:
        players_count = 1

    # Measurements (keep in sync with CSS .player flex-basis and gaps)
    player_box_width = 260  # matches flex-basis used for .player (includes padding/border due to box-sizing)
    gap = 12
    padding = 18  # left+right padding from .wrap (wrap uses border-box)

    total_width = players_count * player_box_width + max(0, players_count - 1) * gap
    # Add a small extra margin to account for shadows/borders and rounding
    extra_margin = 24
    total_width += extra_margin
    # Clamp to reasonable bounds so overlay isn't absurdly small or huge
    min_width = 420
    max_width = 1200
    wrap_width = int(max(min_width, min(total_width, max_width)))

    html_content = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="{int(refresh_interval)}">
    <title>Match Overlay</title>
    <style>
        /* Futuristic / modern styles */
        html, body {{ height:100%; background: transparent !important; }}
        body {{ margin:0; padding:0; font-family: 'Orbitron', 'Segoe UI', Tahoma, Arial, sans-serif; background: transparent !important; color: #e6f0ff; }}
        .wrap {{ padding: 18px; box-sizing: border-box; background: rgba(8,10,14,0.35); border-radius: 12px; }}
        .map {{ font-size: 30px; font-weight: 900; color: #9ff0ff; margin: 0 0 12px 0; letter-spacing: 0.6px; text-align: center; /* center the map title */
             /* darker outline using multiple shadows for better contrast */
             text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 0 4px 12px rgba(0,0,0,0.6); }}
          /* Force player boxes to sit horizontally next to each other.
              The outer container width is computed to fit the players, so
              we don't need a horizontal scrollbar. */
          .players {{ display: flex; gap: 12px; flex-wrap: nowrap; overflow: visible; }}
        .player {{ background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding: 10px; border-radius: 10px; flex: 0 0 260px; display:flex; align-items:center; gap:10px; border:1px solid rgba(160,220,255,0.06); box-shadow: 0 8px 24px rgba(0,0,0,0.6); overflow: hidden; box-sizing: border-box; }}
        .flag {{ width:28px; height:18px; vertical-align:middle; margin-right:8px; border-radius:2px; box-shadow:0 2px 6px rgba(0,0,0,0.6); }}
        .player-left {{ display:flex; flex-direction:column; flex:1; min-width:0 }}
        .name-box {{ display:inline-block; padding:8px 12px; border-radius:8px; font-weight:800; color:#fff; background:transparent; border:2px solid rgba(255,255,255,0.04); backdrop-filter: blur(2px); max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .meta {{ margin-top:8px; font-size:13px; color:#cfd8e6; display:flex; justify-content:space-between; align-items:center }}
        .meta .left {{ font-size:13px; color:#cfd8e6; }}
        .meta .elo {{ font-size:20px; font-weight:900; color:#ffffff; padding:6px 10px; border-radius:8px; background:linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); box-shadow: 0 4px 12px rgba(0,0,0,0.6); }}
    </style>
</head>
<body>
    <div class="wrap" style="width:{wrap_width}px;">
        <div class="map">{safe_map}</div>
        <div class="players">{player_html}
        </div>
    </div>
</body>
</html>
"""

    html_path = os.path.join(output_dir, html_name)

    try:
        with open(html_path, 'w', encoding='utf-8') as hf:
            hf.write(html_content)
        print(f"Webpage generated successfully: {os.path.abspath(html_path)}")
        return html_path
    except Exception as e:
        print(f"ERROR writing HTML overlay: {e}")
        return None


def hide_overlay(output_dir=None, html_name="match_info.html"):
    """Overwrite the overlay HTML with a minimal fully-transparent page.

    This keeps the same filename so OBS Browser sources remain pointed to the
    same path but nothing is visible on the stream until the next match.
    """
    if output_dir is None:
        output_dir = os.path.dirname(__file__)

        # Create a minimal transparent page that still runs the JS poller.
        # The poller will fetch the same file every 2s and inject any new map/players
        # HTML when a match overlay is written, so OBS will update automatically.
        html = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Overlay Hidden</title>
    <style>
        html,body{height:100%;background:transparent!important;margin:0;padding:0}
        .map{display:none}
        .players{display:none}
    </style>
</head>
<body>
    <div class="map"></div>
    <div class="players"></div>
    <script>
    (function(){
        const pollInterval = 2000; // ms
        async function fetchAndUpdate(){
            try{
                const url = window.location.href.split('#')[0].split('?')[0] + '?_=' + Date.now();
                const res = await fetch(url, {cache: 'no-store'});
                if(!res.ok) return;
                const text = await res.text();
                // Try to extract the map/players sections from the fetched HTML
                const mapMatch = text.match(/<div class=\"map\">([\s\S]*?)<\/div>/i);
                const playersMatch = text.match(/<div class=\"players\">([\s\S]*?)<\/div>/i);
                if(mapMatch && playersMatch){
                    const curMap = document.querySelector('.map');
                    const curPlayers = document.querySelector('.players');
                    if(curMap && curPlayers){
                        const newMapHtml = mapMatch[1];
                        const newPlayersHtml = playersMatch[1];
                        // If found, replace DOM and make visible
                        if(curMap.innerHTML !== newMapHtml) curMap.innerHTML = newMapHtml;
                        if(curPlayers.innerHTML !== newPlayersHtml) curPlayers.innerHTML = newPlayersHtml;
                        curMap.style.display = '';
                        curPlayers.style.display = '';
                    }
                }
            }catch(e){/* ignore */}
        }
        setInterval(fetchAndUpdate, pollInterval);
        // also run immediately once
        fetchAndUpdate();
    })();
    </script>
</body>
</html>
"""

    path = os.path.join(output_dir, html_name)
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(html)
        print(f"Overlay hidden: {os.path.abspath(path)}")
        return path
    except Exception as e:
        print(f"ERROR writing hidden overlay: {e}")
        return None
