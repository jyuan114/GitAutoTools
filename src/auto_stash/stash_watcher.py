import logging  ## 未來改 log -> logging
import subprocess
import datetime
import time
import os
from pathlib import Path
from typing import List, Tuple

APP_NAME = "GitAutoStash"
DEFAULT_INTERVAL = 20 # second
# Use pathlib for cross-platform path handling and resolve the log file location
LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "auto_stash.log"


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

    print(f"[{ts}] {msg}")

def is_git_repo(path):
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip() == "true"
    
    except subprocess.CalledProcessError:
        return False


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

    create_cmd = ["git", "stash", "create"] 

    if include_untracked:
        create_cmd.append("--include-untracked")

    res = subprocess.run(
        create_cmd,
        capture_output=True,
        text=True,
        cwd=cwd
    )

    ref = res.stdout.strip()

    store_cmd = ["git", "stash", "store", ref,
        "-m", f"auto-stash {timestamp}"]
    
    subprocess.run(
        store_cmd,
        check=True,
        cwd=cwd
    )
    print(f"Stashed changes at {timestamp}")

def do_stash_job(cwd, include_untracked):
    if has_changes(cwd, include_untracked):
        log("Changes detected, stashing...")
        stash_changes(cwd, include_untracked)
        log("Changes stashed.")
    else:
        log("No changes detected.")

def run_watcher(interval=20, cwd=None, include_untracked=False):
    log("=== Git Auto Stash Watcher Started ===")
    next_run = time.time()

    try:
        while True:
            now = time.time()
            if now >= next_run:
                start = time.time()
                try:
                    do_stash_job(cwd, include_untracked)

                    next_run += interval
                    while next_run < now:
                        next_run += interval

                except Exception as e:
                    log(f"Error: {e}")

                elapsed = time.time() - start
                log(f"Job finished in {elapsed:.2f}s, next run at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(next_run))}")

            else:
                sleep_time = next_run - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
    except KeyboardInterrupt:
        log("=== Git Auto Stash Watcher Stopped by user ===")

def default_trackfile():
    """
    Default list location:
      - Windows: %APPDATA%/GitAutoStash/tracklist.txt
      - Others: ~/.config/git-auto-stash/tracklist.txt
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME / "tracklist.txt"
    
    else:
        return Path.home() / ".config" / "git-auto-stash" / "tracklist.txt"

def _normalize_path(p: str) -> str:

    return str(Path(os.path.expandvars(os.path.expanduser(p))).resolve())

def load_tracklist(trackfile: Path) -> List[Path]:
    if not trackfile.exists():
        return []
    
    items = []
    seen = set()

    with open(trackfile, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            
            if not line or line.startswith("#"):
                continue

            norm = _normalize_path(line)
            if norm not in seen:
                items.append(Path(norm))
                seen.add(norm)

    return items

def save_tracklist(trackfile: Path, items: List[Path]) -> None:
    trackfile.parent.mkdir(parents=True, exist_ok=True)

    tmp = trackfile.with_suffix(trackfile.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("# GitAutoStash track list\n")
        f.write("# 一行一個資料夾；支援 ~ 與環境變數，註解以 # 開頭\n\n")

        for p in sorted({str(p.resolve()) for p in items}):
            f.write(p + "\n")
    tmp.replace(trackfile)

def add_to_tracklist(trackfile: Path, path: str) -> Tuple[bool, str]:
    items = load_tracklist(trackfile)
    norm = Path(_normalize_path(path))

    if norm in items:
        return False, f"Existed: {norm}"
    
    items.append(norm)
    save_tracklist(trackfile, items)
    return True, f"Added: {norm}"

def remove_from_tracklist(trackfile: Path, path: str) -> Tuple[bool, str]:
    items = load_tracklist(trackfile)
    norm = Path(_normalize_path(path))
    
    new_items = [p for p in items if p != norm]
    
    if len(new_items) == len(items):
        return False, f"Not found: {norm}"
    
    save_tracklist(trackfile, new_items)
    return True, f"Removed: {norm}"


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Git Auto Stash Watcher.")
#     parser.add_argument("-u", "--untracked", action="store_true", help="Include untracked files.")
#     parser.add_argument("-i", "--interval", type=int, default=20, help="Check interval in seconds.")
#     parser.add_argument("--once", action="store_true", help="Run once and exit.")

#     args = parser.parse_args()

#     current_dir = os.path.dirname(__file__)
#     parent_dir = os.path.abspath(os.path.join(current_dir, ".."))

#     if args.once:
#         do_stash_job(parent_dir, args.untracked)
#     else:
#         run_watcher(interval=args.interval, include_untracked=args.untracked, cwd=parent_dir)

