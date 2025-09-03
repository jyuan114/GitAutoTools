import argparse
from .stash_watcher import run_watcher

def main():
  p = argparse.ArgumentParser()
  p.add_argument("-i", "--interval", type=int, default=20)
  p.add_argument("--cwd", default=".")
  p.add_argument("u", "--include-untracked", action="store_true")
  p.add_argument("--log-file")  # 若不給就用標準輸出/系統日誌

  args = p.parse_args()

  run_watcher(interval=args.interval, cwd=args.cwd,
              include_untracked=args.include_untracked,
              log_file=args.log_file)

if __name__ == "__main__":
    main()