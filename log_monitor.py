import time
import os
import re
import json
import tkinter as tk
from tkinter import messagebox
import threading
import requests

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

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)

        print("Status code:", response.status_code)

        # Retry logic for 400/403/500 like the original
        if response.status_code in [400, 403, 500]:
            print("Bad request, retrying in 10 seconds...")
            time.sleep(10)
            return get_matches(session_id)

        # Print raw JSON body
        print("HTTP Response Body:")
        print(response.text)

        return response.text

    except requests.exceptions.RequestException as e:
        print("Network error:", e)
        print("Retrying in 10 seconds...")
        time.sleep(10)
        return get_matches(session_id)


def tail_log_file(filepath):
    print("DEBUG: tail_log_file started")

    search_text = "quickmatchfound"
    block_size = 20480  # 20 KB
    last_position = 0  # Track position to avoid re-reading

    while not stop_log_event.is_set():
        try:
            with open(filepath, "rb") as f:
                # Get current file size
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                # If file grew, search from last position to end
                if file_size > last_position:
                    f.seek(last_position)
                    data = f.read().decode("utf-8", errors="ignore")
                    
                    if search_text.lower() in data.lower():
                        print("DEBUG: FOUND QUICKMATCH!")
                        
                        # Find all lines containing the search text
                        lines = data.splitlines()
                        for line in reversed(lines):
                            if search_text.lower() in line.lower():
                                print("MATCH:", line)
                                match_id = parse_match_id_from_log(line)
                                print(f"PARSED MATCH ID: {match_id}")
                                if match_id:
                                    print(f"SUCCESS: Found match ID {match_id}")
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
                                                except Exception as e:
                                                    print("ERROR calling get_matches():", e)
                                                else:
                                                    # Then parse player info in its own try/except
                                                    try:
                                                        time.sleep(5)
                                                        # Extract first player's Steam ID from API response to find the match
                                                        first_player_steam_id = get_first_player_steam_id(response)
                                                        print(f"First player Steam ID: {first_player_steam_id}")
                                                        if first_player_steam_id:
                                                            players_info = get_match_player_info(response, first_player_steam_id)
                                                            print(f"Players info: {players_info}")
                                                        else:
                                                            print("WARNING: Could not extract first player Steam ID from API response")
                                                    except Exception as e:
                                                        print("ERROR parsing players info from API response:", e)

                                    except Exception as e:
                                        print("ERROR while retrieving sessionID or calling API:", e)

                                else:
                                    print(f"WARNING: Could not parse match ID from line: {line}")
                                break
                    
                    last_position = file_size

        except Exception as e:
            print("ERROR in tail_log_file:", e)

        # Wait before scanning again
        time.sleep(10)

    print("Log monitoring stopped.")

def parse_match_id_from_log(line: str):
    """
    Extracts the matchid value from a log line containing:
    "matchid": 7253785

    Returns:
        int matchid, or None if not found.
    """

    # Case-insensitive search for: "matchid": 1234567
    match = re.search(r'"matchid"\s*:\s*(\d+)', line, re.IGNORECASE)
    if match:
        return int(match.group(1))
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

def get_first_player_steam_id(json_response):
    """
    Extract the first player's Steam ID from the API response.
    
    Args:
        json_response (str or dict): JSON response from the API.
    
    Returns:
        int: First player's Steam ID, or None if not found.
    """
    if isinstance(json_response, str):
        try:
            data = json.loads(json_response)
        except json.JSONDecodeError as e:
            print("ERROR: Failed to parse JSON in get_first_player_steam_id():", e)
            return None
    else:
        data = json_response

    matches = data.get("matches", [])
    if matches:
        first_match = matches[0]
        players = first_match.get("players", [])
        if players:
            return players[0]
    
    return None
    
def get_match_player_info(json_response, first_player_steam_id):
    """
    Parse the observer match list JSON and extract player info for the match containing the given Steam ID.

    Args:
        json_response (str or dict): JSON response from the API.
        first_player_steam_id (int): Steam ID of the first player to search for.

    Returns:
        list of dict: Each dict contains 'name', 'team', 'elo', 'color', 'start_position', 'steam_id'
                      Returns empty list if match not found.
    """
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
        # Check if the first player's Steam ID is in this match's players list
        players = match.get("players", [])
        if first_player_steam_id in players:
            players_info = []
            names = match.get("names", [])
            teams = match.get("teams", [])
            elos = match.get("elos", [])
            colors = match.get("colors", [])
            # Start positions are derived from player index in the match
            start_positions = list(range(len(names)))

            for i in range(len(names)):
                players_info.append({
                    "name": names[i],
                    "team": teams[i] if i < len(teams) else None,
                    "elo": elos[i] if i < len(elos) else None,
                    "color": colors[i] if i < len(colors) else None,
                    "start_position": start_positions[i],
                    "steam_id": players[i] if i < len(players) else None
                })

            return players_info

    return []  # No match found

if __name__ == "__main__":
    # Example usage (runs only when executed directly)
    json_response = """<your JSON response here>"""
    match_name = "1v1 QM"
    players = get_match_player_info(json_response, match_name)
    for p in players:
        print(p)