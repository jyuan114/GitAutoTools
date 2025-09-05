import argparse
from .stash_watcher import run_watcher

#     parser = argparse.ArgumentParser(description="Git Auto Stash Watcher.")
#     parser.add_argument("-u", "--untracked", action="store_true", help="Include untracked files.")
#     parser.add_argument("-i", "--interval", type=int, default=20, help="Check interval in seconds.")
#     parser.add_argument("--once", action="store_true", help="Run once and exit.")

def main():
  p = argparse.ArgumentParser(prog="auto-stash", description="Git Auto Stash Watcher.")
  p.add_argument("--cwd", default=".", help="Git repo path")
  p.add_argument("-i", "--interval", type=int, default=20, help="Check interval in seconds.")
  p.add_argument("-u", "--include-untracked", action="store_true", help="Include untracked files.")
  p.add_argument("--log-file", default=None, help="Log file path")  # 若不給就用標準輸出/系統日誌

  args = p.parse_args()

  run_watcher(interval=args.interval, cwd=args.cwd,
              include_untracked=args.include_untracked,
            #   log_file=args.log_file
              )

if __name__ == "__main__":
    main()