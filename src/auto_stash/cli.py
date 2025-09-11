import argparse
from pathlib import Path
from .stash_watcher import (
    default_trackfile,
    load_tracklist,
    add_to_tracklist,
    remove_from_tracklist,
    run_watcher,
    stash_clear
)

APP_PROG = "auto-stash"
VERSION = "0.1.0"

def build_parser():
    p = argparse.ArgumentParser(prog=APP_PROG,
                                description=(
                                    "Git Auto Stash Watcher.\n"
                                    "Automatically stashes changes in your tracked git repositories.\n"
                                    "Use subcommands to manage the tracking list, watch changes, or clear stashes.\n"    
                                ),
                                # epilog=(
                                #     "There are commn Git Auto Stash comment used in varios situations:\n\n"
                                    
                                # ),
                                formatter_class=argparse.RawTextHelpFormatter
                                )
    sub = p.add_subparsers(dest="cmd") #, required=True)
    
    p_track = sub.add_parser("track", help="Manage tracking list", description="Use the following subcommands to manage your tracking list.")
    sub_track = p_track.add_subparsers(dest="track_cmd")

    p_list = sub_track.add_parser("list", help="List all tracked folders.")
    p_list.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_add = sub_track.add_parser("add", help="Add a folder to tracking list.")
    p_add.add_argument("path")
    p_add.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_rm = sub_track.add_parser("rm", aliases=["remove"], help="Remove a folder from tracking list.")
    p_rm.add_argument("path")
    p_rm.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_watch = sub.add_parser("watch",
                             help="Watch tracked folders and automatically stash changes.\n"
                                  "If --cwd is provided, only that repository is watched\n"
                                  "and the tracking list is ignored.")
    p_watch.add_argument("--fmt", choices=["pretty", "line"], default="line", help="Output format: pretty or line")
    p_watch.add_argument("--cwd", help="Specify the Git repo path")
    p_watch.add_argument("--file", dest="trackfile", default=str(default_trackfile()))
    p_watch.add_argument("--interval", "-i", metavar="", type=int, default=300, help="Polling interval in secounds")
    p_watch.add_argument("--include-untracked", "-u", action="store_true", help="Include untracked files when detecting ")

    p_clear = sub.add_parser("clear", help="Clear all stashes in tracked folders.")
    p_clear.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_ver = sub.add_parser("version", aliases=["v"], help="Show program version.")
    p_ver.set_defaults(func=lambda args: print(f"{APP_PROG} {VERSION}"))

    return p

def main():
    parser = build_parser()
    # parser.add_argument("--log-file", default=None, help="Log file path")  # 若不給就用標準輸出/系統日誌
    args = parser.parse_args()
    
    if args.cmd is None:
        parser.print_help()

    elif args.cmd == "track":
        if args.track_cmd is None:
            parser._subparsers._group_actions[0].choices["track"].print_help()
            return 0
        
        tf = Path(args.trackfile)

        if args.track_cmd == "list":
            items = load_tracklist(tf)
            if not items:
                print(f"Empty list {tf}")
            else:
                print(f"List: {tf}\n---")
                for p in items:
                    print(p)
        
        elif args.track_cmd == "add":
            ok, msg = add_to_tracklist(tf, args.path)
            print(msg)
        
        elif args.track_cmd == "rm":
            ok, msg = remove_from_tracklist(tf, args.path)
            print(msg)
    
    elif args.cmd == "watch":

        if args.cwd:
            print("cwd", args.cwd)
            paths = [Path(args.cwd)]
        else:
            tf = Path(args.trackfile)
            paths = load_tracklist(tf)

        run_watcher(
            paths = paths,
            interval=args.interval,
            include_untracked=args.include_untracked,
            fmt=args.fmt
        )
        
    elif args.cmd == "clear":
        tf = Path(args.trackfile)
        paths = load_tracklist(tf)
        stash_clear(paths)

    elif args.cmd == "version" or "v":
        args.func(args)
    
    

if __name__ == "__main__":
    main()