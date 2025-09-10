import logging  ## 未來改 log -> logging
import subprocess
import datetime
import time
import os
from pathlib import Path
from typing import List, Tuple, Optional

APP_NAME = "GitAutoStash"
DEFAULT_INTERVAL = 20 # second
LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "auto_stash.log"

# -------------- Format / Print utils -------------
class Colors:
    RESET = "\x1b[0m"
    GRAY = "\x1b[90m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"

def _colorize(s: str, code: str, enable: bool) -> str:
    return f"{code}{s}{Colors.RESET}" if enable else s

def _icon_status(status: str) -> str:
    return {
        "STASHED": "✅",
        "NO_CHANGES": "∅",
        "ERROR": "⚠",
        "SKIPPED": "⏭",
    }.get(status,  "•")

def _short(s: Optional[str], n: int = 8) -> Optional[str]:
    if not s:
        return None
    return s[:n]

def log(msg: str, ts=True):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

    if ts:
        print(f"[{ts}] {msg}")
    else:
        print(f"{msg}")


# -------------- Git utils ------------------
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
    message = f"auto-stash {timestamp}"

    store_cmd = ["git", "stash", "store", ref, "-m", message]
    
    subprocess.run(
        store_cmd,
        check=True,
        cwd=cwd
    )

    return ref, message

# -------------- Core Job --------------------
def do_stash_job(cwd: Path, include_untracked: bool):
    """
    回傳統一結構
    {
      "repo": str,
      "status": "STASHED" | "NO_CHANGES" | "ERROR",
      "stash_id": Optional[str],
      "message": Optional[str],
      "detail": Optional[str],
    }
    """
    try:
        if not is_git_repo(cwd):
            return {"repo": str(cwd), "status": "SKIPPED", "detail": "not a git repository"}

        if has_changes(cwd, include_untracked):
            ret = stash_changes(cwd)
            stash_id: Optional[str] = None
            message: Optional[str] = None

            if isinstance(ret, tuple):
                if len(ret) >= 1:
                    stash_id = ret[0]
                if len(ret) >= 2:
                    message = ret[1]
                
            return {
                "repo": str(cwd),
                "status": "STASHED",
                "stash_id": stash_id,
                "message": message,
            }
        
        else:
            return {"repo": str(cwd), "status": "NO_CHANGES"}

    except Exception as e:
        return {
            "repo": str(cwd),
            "status": "ERROR",
            "detail": str(e)
        }

def run_watcher(paths: List[Path], interval=20, include_untracked=False, fmt: str="line", color: bool=True):
    log("=== Git Auto Stash Watcher Started ===")
    next_run = time.time()
    run_id = 0

    try:
        while True:
            now = time.time()
            if now >= next_run:
                run_id += 1
                start = time.time()

                results: List[dict] = []
                try:
                    for cwd in paths:
                        res = do_stash_job(cwd, include_untracked)
                        results.append(res)

                    next_run += interval
                    while next_run < now:
                        next_run += interval

                except Exception as e:
                    results.append({
                        "repo": "<run-level>",
                        "status": "ERROR",
                        "detail": str(e)
                    })
                elapsed = time.time() - start

                if fmt == "pretty":
                    _render_pretty(run_id, start, elapsed, next_run, results, color)
                else:
                    _render_line(start, elapsed, next_run, results, color)

            else:
                sleep_time = next_run - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
    except KeyboardInterrupt:
        log("=== Git Auto Stash Watcher Stopped by user ===")

# -------------- Track list Management -------

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

# --------- Render Function --------
def _render_pretty(run_id: int, started_at: float, duration: float, next_run: float,
                   results: List[dict], color: bool ):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(started_at))
    head = f"Run #{run_id}  (took {duration:.2f}s)  Next: {time.strftime('%H:%M:%S', time.localtime(next_run))}"
    log(head)

    repo_width = max([len(r["repo"]) for r in results] + [24])
    status_width = 11

    for i, r in enumerate(results):
        icon = _icon_status(r["status"])
        status_text = r["status"]

        # Color
        if r["status"] == "STASHED":
            status_text = _colorize(status_text, Colors.GREEN, color)
        elif r["status"] == "NO_CHANGES" or r["status"] == "SKIPPED":
            status_text = _colorize(status_text, Colors.GRAY, color)
        elif r["status"] == "ERROR":
            status_text = _colorize(status_text, Colors.YELLOW, color)

        prefix = "└─" if i == len(results) - 1 else "├─"
        line = f"  {prefix} repo: {r['repo']:<{repo_width}}  status: {icon} {status_text:<{status_width}}"

        if r.get("stash_id"):
            line += f"  stash: {_short(r['stash_id'])}"
        # if r.get("message"):
        #     line += f"  msg: {r['message']}"
        if r.get("detail"):
            line += f"  detail: {r['detail']}"

        log(line)

    total = len(results)
    stashed = sum(1 for r in results if r["status"] == "STASHED")
    nochg = sum(1 for r in results if r["status"] == "NO_CHANGES")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    summary_parts = [f"Summary: {total} repos"]
    if stashed != 0:
        summary_parts.append(f"stashed: {stashed}")
    if nochg != 0:
        summary_parts.append(f"no changes: {nochg}")
    if skipped != 0:
        summary_parts.append(f"skipped: {skipped}")
    if errors != 0:
        summary_parts.append(f"errors: {errors}")
    log(" | ".join(summary_parts))

def _render_line(start: float, duration: float, next_run: float, results: List[dict], color: bool):
    for r in results:
        status = r['status']
        if status == "STASHED":
            status = _colorize(status, Colors.GREEN, color)
        elif status in ("NO_CHANGES", "SKIPPED"):
            status = _colorize(status, Colors.GRAY, color)
        elif status == "ERROR":
            status = _colorize(status, Colors.YELLOW, color)

        parts = [f"{status}", f"repo={r['repo']}"]

        if r.get("stash_id"):
            parts.append(f"stash={_short(r['stash_id'])}")
        if r.get("message"):
            parts.append(f'msg="{r["message"]}"')
        if r.get("detail"):
            parts.append(f'detail="{r["detail"]}"')

        log("  ".join(parts),ts=False)

    total = len(results)
    stashed = sum(1 for r in results if r["status"] == "STASHED")
    nochg = sum(1 for r in results if r["status"] == "NO_CHANGES")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    summary_parts = [f"Summary  repos={total}"]
    if stashed != 0:
        summary_parts.append(f"stashed={stashed}")
    if nochg != 0:
        summary_parts.append(f"no_changes={nochg}")
    if skipped != 0:
        summary_parts.append(f"skipped={skipped}")
    if errors != 0:
        summary_parts.append(f"errors={errors}")
    log(" ".join(summary_parts))



