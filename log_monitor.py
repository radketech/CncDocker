import time
import os
import re
import json
import tkinter as tk
from tkinter import messagebox
import threading
import requests
from generate_overlay import generate_match_webpage, hide_overlay

# Shared event imported into main script
stop_log_event = threading.Event()


def get_matches(session_id):
    """
    Performs the same PUT request as the previous module's `get_matches()`.
    Returns the response text or raises on network errors.
    """
    url = "https://coordinator.cnctdra.ea.com:6531/Coordinator/webresources/com.petroglyph.coord.observer.match.find.matches/"

    payload = {
        "observerMatchFindMatches": {
            "sessionID": int(session_id),
            "playerName": ""
        }
    }

    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json"
    }

    print("Executing PUT request in get_matches()...")

    max_attempts = 3
    retry_statuses = {400, 403, 500}

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.put(url, json=payload, headers=headers, timeout=10)
            print(f"Attempt {attempt}: Status code: {response.status_code}")

            if response.status_code in retry_statuses:
                if attempt < max_attempts:
                    print(f"Received {response.status_code}, retrying in 10 seconds...")
                    time.sleep(10)
                    continue
                else:
                    print(f"Received {response.status_code} on final attempt, giving up.")
                    return None

            # Successful-ish response; return body
            print("HTTP Response Body:")
            print(response.text)
            return response.text

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}: Network error: {e}")
            if attempt < max_attempts:
                print("Retrying in 10 seconds...")
                time.sleep(10)
                continue
            else:
                print("Network error on final attempt, giving up.")
                return None


def tail_log_file(filepath, output_dir=None):
    print("DEBUG: tail_log_file started")

    search_text = "quickmatchfound"
    block_size = 20480  # 20 KB
    last_position = 0  # Track position to avoid re-reading

    overlay_hidden = False
    def _delayed_hide(out_dir):
        # Sleep and then attempt to hide the overlay
        time.sleep(5)
        try:
            hide_overlay(output_dir=out_dir)
            print("DEBUG: overlay hidden after match end")
        except Exception as e:
            print("ERROR hiding overlay:", e)

    while not stop_log_event.is_set():
        try:
            with open(filepath, "rb") as f:
                # Get current file size
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                # If logfile was truncated or rotated (size decreased), reset our read position
                if file_size < last_position:
                    print("DEBUG: logfile size decreased — resetting last_position to 0")
                    last_position = 0

                # If file grew, search from last position to end
                if file_size > last_position:
                    f.seek(last_position)
                    data = f.read().decode("utf-8", errors="ignore")
                    
                    # Detect match start
                    if search_text.lower() in data.lower():
                        print("DEBUG: FOUND QUICKMATCH!")
                        
                        # Find all lines containing the search text
                        lines = data.splitlines()
                        for line in reversed(lines):
                            if search_text.lower() in line.lower():
                                print("MATCH:", line)
                                map_name = parse_map_name_from_log(line)
                                print(f"PARSED MAP NAME: {map_name}")
                                if map_name:
                                    print(f"SUCCESS: Found map name {map_name}")
                                    # Safely get last session ID and call API
                                    try:
                                        sessionID = get_last_session_id(filepath)
                                        print(f"Using sessionID: {sessionID!r}")

                                        if not sessionID:
                                            print("WARNING: No sessionID found in log; skipping API call.")
                                        else:
                                            # Ensure we have a numeric session ID
                                            try:
                                                sid_int = int(str(sessionID).strip())
                                            except Exception as e:
                                                print(f"WARNING: sessionID is not numeric ({sessionID!r}):", e)
                                                print("Skipping API call due to invalid sessionID.")
                                            else:
                                                # First call the API and handle network errors separately
                                                try:
                                                    response = get_matches(sid_int)
                                                    print(f"API response: {response}")
                                                    if response is None:
                                                        print("WARNING: get_matches() failed after retries — skipping this match and continuing tail.")
                                                        # Stop processing this matched line and continue scanning the logfile
                                                        break
                                                except Exception as e:
                                                    print("ERROR calling get_matches():", e)
                                                else:
                                                    steam_id = extract_steam_id(filepath)
                                                    # Then parse player info in its own try/except
                                                    try:
                                                        time.sleep(1)
                                                        players_info = get_match_player_info(response, steam_id)
                                                        print(f"Players info: {players_info}")
                                                        
                                                        # Generate webpage with player and map info
                                                        try:
                                                            webpage_path = generate_match_webpage(players_info, map_name, output_dir=output_dir)
                                                            print(f"Webpage generated: {webpage_path}")
                                                            # reset overlay_hidden flag when a new match overlay is generated
                                                            overlay_hidden = False
                                                        except Exception as e:
                                                            print("ERROR generating webpage:", e)
                                                    except Exception as e:
                                                        print("ERROR parsing players info from API response:", e)

                                    except Exception as e:
                                        print("ERROR while retrieving sessionID or calling API:", e)

                                else:
                                    print(f"WARNING: Could not parse match ID from line: {line}")
                                break
                    
                    # Detect match end lines (e.g., a player being removed indicates match end)
                    if "removed player" in data.lower():
                        # Load settings to check whether we should close overlay on match complete
                        try:
                            settings = {}
                            if os.path.exists("settings.json"):
                                with open("settings.json", "r", encoding="utf-8") as sf:
                                    settings = json.load(sf)
                        except Exception:
                            settings = {}

                        if settings.get("close_overlay_on_match_complete", False) and not overlay_hidden:
                            print("DEBUG: Detected 'Removed player' and setting enabled — scheduling overlay hide in 5s")
                            overlay_hidden = True
                            t = threading.Thread(target=_delayed_hide, args=(output_dir,), daemon=True)
                            t.start()

                    last_position = file_size

        except Exception as e:
            print("ERROR in tail_log_file:", e)

        # Wait before scanning again
        time.sleep(10)

    print("Log monitoring stopped.")

def parse_map_name_from_log(line: str):
    """
    Extracts the mapname value from a log line containing:
    "mapname": "MOBIUS_RED_ALERT_MULTIPLAYER_9_MAP"

    Returns:
        str mapname, or None if not found.
    """
    # Case-insensitive search for: "mapname": "..."
    mapname_match = re.search(r'"mapname"\s*:\s*"([^"]+)"', line, re.IGNORECASE)
    if mapname_match:
        return mapname_match.group(1)  # Already a string
    return None

def show_match_popup(matchdata):
    root = tk.Tk()
    root.withdraw()

    msg = (
        f"🔥 Quickmatch Found!\n\n"
        f"Map: {matchdata.get('mapname', 'Unknown')}\n"
        f"Match Name: {matchdata.get('matchname', '')}\n"
        f"Match ID: {matchdata.get('matchid', '')}\n"
        f"Players: {matchdata.get('numplayers', '')}\n"
        f"Ranked Match: {'Yes' if matchdata.get('isrankedmatch', False) else 'No'}\n"
        f"Start Time: {matchdata.get('starttime', '')}"
    )

    messagebox.showinfo("Match Found!", msg)
    root.destroy()

def get_last_session_id(file_path):
    """
    Reads the log file and returns the last sessionID found.
    Matches the behavior of the Java version.
    """
    session_id = None

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "sessionID" in line:
                    start_index = line.find("sessionID") + len("sessionID") + 1  # move past 'sessionID'
                    
                    # skip potential characters like ':' or '"' or ' ' 
                    while start_index < len(line) and line[start_index] in [":", " ", "\""]:
                        start_index += 1

                    # find where the value ends
                    end_index = line.find(",", start_index)
                    if end_index == -1:
                        end_index = line.find("}", start_index)

                    if end_index != -1:
                        session_id = line[start_index:end_index].strip().replace('"', '')

        return session_id

    except Exception as e:
        print("Error reading sessionID:", e)
        return None
    
def get_match_player_info(json_response, player_id):
    """
    Parse the observer match list JSON and extract player info for the match containing a specific player_id.

    This function searches the match's `players` array (steam IDs) rather than `names`.

    Args:
        json_response (str or dict): JSON response from the API.
        player_id (int or str): The player Steam ID to search for.

    Returns:
        list of dict: Each dict contains 'name', 'team', 'elo', 'color', 'start_position', 'steam_id'.
                      Returns empty list if no match contains the player.
    """
    # Normalize player_id to int where possible
    try:
        pid_int = int(player_id)
    except Exception:
        pid_int = None

    if isinstance(json_response, str):
        try:
            data = json.loads(json_response)
        except json.JSONDecodeError as e:
            print("ERROR: Failed to parse JSON response in get_match_player_info():", e)
            return []
    else:
        data = json_response

    matches = data.get("matches", [])
    for match in matches:
        players = match.get("players", [])
        # Normalize players list to ints where possible
        norm_players = []
        for p in players:
            try:
                norm_players.append(int(p))
            except Exception:
                # keep as-is if cannot convert
                norm_players.append(p)

        # Debug: show players list for this match (comment out if noisy)
        # print("DEBUG: match players:", norm_players)

        found = False
        if pid_int is not None:
            found = pid_int in norm_players
        else:
            # fallback: string compare
            found = str(player_id) in [str(x) for x in norm_players]

        if found:
            names = match.get("names", [])
            teams = match.get("teams", [])
            elos = match.get("elos", [])
            factions = match.get("factions", [])
            colors = match.get("colors", [])
            start_positions = list(range(len(names)))

            players_info = []
            for i in range(len(names)):
                steam_val = None
                if i < len(norm_players):
                    steam_val = norm_players[i]
                players_info.append({
                    "name": names[i],
                    "team": teams[i] if i < len(teams) else None,
                    "elo": elos[i] if i < len(elos) else None,
                    "color": colors[i] if i < len(colors) else None,
                    "faction": factions[i] if i < len(factions) else None,
                    "start_position": start_positions[i],
                    "steam_id": steam_val
                })

            return players_info

    return []  # No match found with that player


def extract_steam_id(logfile):
    """Extract SteamID from log file."""
    try:
        with open(logfile, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = re.search(r"ID:\s*(\d{17})", line)
                if match:
                    return match.group(1)

    except Exception as e:
        messagebox.showerror("Error Reading Log File", str(e))
        return None

    return None

if __name__ == "__main__":
    # Example usage (runs only when executed directly)
    json_response = """<your JSON response here>"""
    match_name = "1v1 QM"
    players = get_match_player_info(json_response, match_name)
    for p in players:
        print(p)