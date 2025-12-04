"""
Helper module to generate a small HTML overlay for OBS.

This version shows only: player names, ELOs, start positions, and the map name.
Each player's name is enclosed in a colored box according to the provided mapping.
The page auto-refreshes every `refresh_interval` seconds so OBS will display updated info
when the HTML file is rewritten.
"""

import os
import html
from datetime import datetime


def generate_match_webpage(players_info, map_name, output_path=None, refresh_interval=5):
    """
    """
    Helper module to generate an OBS overlay and a small JSON state file that the overlay
    will poll via JavaScript. The page updates dynamically without a full reload.
    """

    import os
    import json
    import html
    from datetime import datetime


    def generate_match_webpage(players_info, map_name, output_dir=None, refresh_interval=3,
                               json_name="match_info.json", html_name="match_info.html"):
        """
        Write a JSON state file and an HTML overlay that polls it.

        Args:
            players_info (list): list of dicts with keys: 'name','elo','start_position','color', optionally 'steam_id'.
            map_name (str): Map name string.
            output_dir (str): Directory to write files. Defaults to module directory.
            refresh_interval (int): Poll interval in seconds used by the HTML/JS.
            json_name (str): Filename for JSON state.
            html_name (str): Filename for generated HTML.

        Returns:
            tuple: (json_path, html_path) or (None, None) on error.
        """
        if output_dir is None:
            output_dir = os.path.dirname(__file__)

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            """
            Helper module to generate an OBS overlay and a small JSON state file that the overlay
            will poll via JavaScript. The page updates dynamically without a full reload.
            """

            import os
            import json
            import html
            from datetime import datetime


            def generate_match_webpage(players_info, map_name, output_dir=None, refresh_interval=3,
                                       json_name="match_info.json", html_name="match_info.html"):
                """
                Write a JSON state file and an HTML overlay that polls it.

                Args:
                    players_info (list): list of dicts with keys: 'name','elo','start_position','color', optionally 'steam_id'.
                    map_name (str): Map name string.
                    output_dir (str): Directory to write files. Defaults to module directory.
                    refresh_interval (int): Poll interval in seconds used by the HTML/JS.
                    json_name (str): Filename for JSON state.
                    html_name (str): Filename for generated HTML.

                Returns:
                    tuple: (json_path, html_path) or (None, None) on error.
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

                # Prepare JSON data
                state = {
                    "map_name": map_name or "Unknown Map",
                    "players": players_info or [],
                    "updated": datetime.utcnow().isoformat() + "Z",
                }

                json_path = os.path.join(output_dir, json_name)
                html_path = os.path.join(output_dir, html_name)

                try:
                    with open(json_path, "w", encoding="utf-8") as jf:
                        json.dump(state, jf, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"ERROR writing JSON state: {e}")
                    return None, None

                # Build HTML that fetches the JSON and updates the DOM
                safe_map = html.escape(str(map_name or "Unknown Map"))

                js = f"""
            async function fetchAndRender() {{
              try {{
                const resp = await fetch('{json_name}?_=' + Date.now());
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                render(data);
              }} catch (err) {{
                console.debug('fetch error', err);
              }}
            }}

            function render(data) {{
              document.getElementById('map').textContent = data.map_name || 'Unknown Map';
              const container = document.getElementById('players');
              container.innerHTML = '';
              const players = data.players || [];
              if (players.length === 0) {{
                const div = document.createElement('div');
                div.className = 'player';
                div.innerHTML = `<div class="name-box" style="background:#666;color:#fff">No players</div>`;
                container.appendChild(div);
                return;
              }}
              players.forEach(p => {{
                const name = p.name || 'Unknown';
                const elo = (p.elo === null || p.elo === undefined) ? 'N/A' : p.elo;
                const start = p.start_position || '-';
                const colorIdx = p.color;
                const color = ({json.dumps(color_map)})[colorIdx] || '#CCCCCC';

                const div = document.createElement('div');
                div.className = 'player';
                div.innerHTML = `\n      <div class="name-box" style="background:${{color}};">${{escapeHtml(name)}}</div>\n      <div class="meta"><span>Start: ${{escapeHtml(String(start))}}</span><span>ELO: ${{escapeHtml(String(elo))}}</span></div>`;
                container.appendChild(div);
              }});
            }}

            function escapeHtml(s) {{
              return String(s)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
            }}

            // initial fetch and interval
            fetchAndRender();
            setInterval(fetchAndRender, {int(refresh_interval) * 1000});
            """

                html_content = f"""
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>Match Overlay</title>
              <style>
                body {{ font-family: Segoe UI, Tahoma, Arial, sans-serif; background: transparent; color: #fff; }}
                .wrap {{ padding: 12px; min-width: 320px; }}
                .map {{ font-size: 20px; font-weight: 700; color: #ffd166; margin-bottom: 8px; }}
                .players {{ display: flex; gap: 8px; flex-wrap: wrap; }}
                .player {{ background: rgba(0,0,0,0.45); padding: 8px 10px; border-radius: 6px; min-width: 160px; }}
                .name-box {{ display:inline-block; padding:6px 10px; border-radius:4px; font-weight:700; color:#000; }}
                .meta {{ margin-top:6px; font-size:13px; color:#ddd; display:flex; justify-content:space-between; }}
              </style>
            </head>
            <body>
              <div class="wrap">
                <div id="map" class="map">{safe_map}</div>
                <div id="players" class="players"></div>
                <div style="margin-top:10px; font-size:12px; color:#aaa;">Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}</div>
              </div>
              <script>
              {js}
              </script>
            </body>
            </html>
            """

                try:
                    with open(html_path, 'w', encoding='utf-8') as hf:
                        hf.write(html_content)
                    print(f"Webpage generated successfully: {os.path.abspath(html_path)}")
                    return json_path, html_path
                except Exception as e:
                    print(f"ERROR writing HTML overlay: {e}")
                    return None, None
