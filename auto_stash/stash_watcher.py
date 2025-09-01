import logging  ## 未來改 log -> logging
import subprocess
import datetime
import time
import os
import argparse

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "auto_stash.log")


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def has_changes(cwd, include_untracked=False) -> bool:

    cmd = ["git", "status", "--porcelain"]

    if not include_untracked:
        cmd.append("--untracked-files=no")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd
    )
    return bool(result.stdout.strip())

def stash_changes(cwd, include_untracked=False):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd = ["git", "stash", "store",
        "$(", "git", "stash", "create", ")",
        "-m", f"auto-stash {timestamp}"]
    
    if include_untracked:
        cmd.insert(2, "--include-untracked")
        
    subprocess.run(
        cmd,
        check=True,
        cwd=cwd
    )
    print(f"Stashed changes at {timestamp}")

def run(interval=20, cwd=None):
    log("=== Git Auto Stash Watcher Started ===")
    while True:
        try:
            if has_changes(cwd):
                log("Changes detected, stashing...")
                stash_changes(cwd)
                log("Changes stashed.")
            else:
                log("No changes detected.")
        except Exception as e:
            log(f"Error: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Git Auto Stash Watcher.")
    parser.add_argument("-u", "--untracked", action="store_true", help="Include untracked files.")
    parser.add_argument("-i", "--interval", type=int, default=20, help="Check interval in seconds.")
    args = parser.parse_args()

    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.abspath(os.path.join(current_dir, ".."))

    run(interval=args.interval, include_untracked=args.untracked, cwd=parent_dir)

