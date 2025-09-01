import logging  ## 未來改 log -> logging
import subprocess
import datetime
import time
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "auto_stash.log")

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def has_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())

def stash_changes():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run(
        ["git", "stash", "push", "-k","-m", f"auto-stash {timestamp}"],
        check=True
    )
    print(f"Stashed changes at {timestamp}")

def run(interval=300):
    log("=== Git Auto Stash Watcher Started ===")
    while True:
        try:
            if has_changes():
                log("Changes detected, stashing...")
                stash_changes()
                log("Changes stashed.")
            else:
                log("No changes detected.")
        except Exception as e:
            log(f"Error: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    run()
            
