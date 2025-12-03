import time
import os
import json
import tkinter as tk
from tkinter import messagebox
import threading

# Shared event imported into main script
stop_log_event = threading.Event()


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
                                break
                    
                    last_position = file_size

        except Exception as e:
            print("ERROR in tail_log_file:", e)

        # Wait before scanning again
        time.sleep(10)

    print("Log monitoring stopped.")



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
