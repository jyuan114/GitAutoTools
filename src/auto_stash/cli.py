import argparse
from pathlib import Path
from .stash_watcher import (
    default_trackfile,
    load_tracklist,
    add_to_tracklist,
    remove_from_tracklist,
    run_watcher
)

APP_PROG = "auto-stash"


def build_parser():
    p = argparse.ArgumentParser(prog=APP_PROG,
                                description="Git Auto Stash Watcher.\n",
                                # epilog=(
                                #     "There are commn Git Auto Stash comment used in varios situations:\n\n"
                                    
                                # ),
                                formatter_class=argparse.RawTextHelpFormatter
                                )
    sub = p.add_subparsers(dest="cmd") #, required=True)
    
    p_track = sub.add_parser("track", help="Manage tracking list", description="Use the following subcommands to manage your tracking list.")
    sub_track = p_track.add_subparsers(dest="track_cmd")

    p_list = sub_track.add_parser("list", help="Show all tracked folders.")
    p_list.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_add = sub_track.add_parser("add", help="Add a folder to the tracking list.")
    p_add.add_argument("path")
    p_add.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_rm = sub_track.add_parser("rm", aliases=["remove"], help="Remove a folder from the tracking list.")
    p_rm.add_argument("path")
    p_rm.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_watch = sub.add_parser("watch", help="Watch folders from track list and auto-stash changes 監看清單中的所有資料夾")
    p_watch.add_argument("--cwd", default=".", help="Git repo path")
    p_watch.add_argument("--fmt", default="line", help="print style: pretty or line")
    p_watch.add_argument("--file", dest="trackfile", default=str(default_trackfile()))
    p_watch.add_argument("--intervel", "-i", type=int, default=300, help="輪尋秒數")
    p_watch.add_argument("--include-untracked", "-u", action="store_true")

    p_ver = sub.add_parser("version", aliases=["v"], help="Show version")
    p_ver.set_defaults(func=lambda args: print(f"{APP_PROG} 0.1.0"))

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
        tf = Path(args.trackfile)
        paths = load_tracklist(tf)

        run_watcher(
            paths = paths,
            interval=args.intervel,
            include_untracked=args.include_untracked,
            fmt=args.fmt
        )
        
    elif args.cmd == "version" or "v":
        args.func(args)
    
    

if __name__ == "__main__":
    main()