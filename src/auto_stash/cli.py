import argparse
import yaml
import pprint
from pathlib import Path
from .stash_watcher import (
    default_trackfile,
    load_tracklist,
    add_to_tracklist,
    remove_from_tracklist,
    run_watcher,
    stash_clear,
    load_config,
    default_config,
    init_config
)

APP_PROG = "auto-stash"
VERSION = "0.1.0"

def build_parser():
    p = argparse.ArgumentParser(prog=APP_PROG,
                                description=(
                                    "Git Auto Stash Watcher.\n"
                                    "Automatically stashes changes in your tracked git repositories.\n"
                                    "Use subcommands to add, remove, list tracked folders, watch repositories,\n"
                                    "clear stashes, or manage configuration.\n"    
                                ),
                                # epilog=(
                                #     "There are commn Git Auto Stash comment used in varios situations:\n\n"
                                    
                                # ),
                                formatter_class=argparse.RawTextHelpFormatter
                                )
    sub = p.add_subparsers(dest="cmd") #, required=True)

    p_list = sub.add_parser("list", help="List all tracked folders.")
    p_list.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_add = sub.add_parser("add", help="Add a folder to tracked list.")
    p_add.add_argument("path")
    p_add.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_rm = sub.add_parser("rm", aliases=["remove"], help="Remove a folder from tracked list.")
    p_rm.add_argument("path")
    p_rm.add_argument("--file", dest="trackfile", default=str(default_trackfile()))
    
    p_watch = sub.add_parser("watch",
                             help="Watch tracked folders and automatically stash changes.\n"
                                  "If --cwd is provided, only that repository is watched\n"
                                  "and the tracking list is ignored.")
    p_watch.add_argument("--fmt", choices=["pretty", "line"], help="Set output format: pretty or line.")
    p_watch.add_argument("--cwd", help="Watch only the specified Git repo.")
    p_watch.add_argument("--file", dest="trackfile", default=str(default_trackfile()))
    p_watch.add_argument("--interval", "-i", metavar="", type=int, default=300, help="Set polling interval in secounds.")
    p_watch.add_argument("--include-untracked", "-u", action="store_true", help="Include untracked files when detecting changes.")

    p_clear = sub.add_parser("clear", help="Clear all stashes in tracked folders.")
    p_clear.add_argument("--file", dest="trackfile", default=str(default_trackfile()))

    p_config = sub.add_parser("config", help="Show configutation.")
    sub_config = p_config.add_subparsers(dest="config_cmd")

    cfg_list = sub_config.add_parser("list", help="Show effective config.")
    cfg_get = sub_config.add_parser("get", help="Get a config value.")
    cfg_set = sub_config.add_parser("set", help="Set a config value.")
    cfg_unset = sub_config.add_parser("unset", help="Remove a config key.")
    cfg_edit = sub_config.add_parser("edit", help="Edit config in $EDITOR.")

    for cfg_ in (cfg_list, cfg_get, cfg_set, cfg_unset, cfg_edit):
        cfg_.add_argument("--path", help="Target repo dir")

    p_ver = sub.add_parser("version", aliases=["v"], help="Show program version.")
    p_ver.set_defaults(func=lambda args: print(f"{APP_PROG} {VERSION}"))

    return p

def main():
    parser = build_parser()
    # parser.add_argument("--log-file", default=None, help="Log file path")  # 若不給就用標準輸出/系統日誌
    args = parser.parse_args()
    
    if args.cmd is None:
        parser.print_help()

    elif args.cmd == "list":
        tf = Path(args.trackfile)
        items = load_tracklist(tf)
        if not items:
            print(f"Empty list {tf}")
        else:
            print(f"List: {tf}\n---")
            for p in items:
                print(p)

    elif args.cmd == "add":
        tf = Path(args.trackfile)
        ok, msg = add_to_tracklist(tf, args.path)
        print(msg)
        
    elif args.cmd == "rm":
        tf = Path(args.trackfile)
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

    elif args.cmd == "config":
        
        if not args.config_cmd:
            parser._subparsers._group_actions[0].choices["config"].print_help()
            return 0
        
        cf = Path(default_config())
        data = load_config(cf)
        if not data:
            init_config(cf)
            data = load_config(cf)
            print(yaml.dump(data))
        else:
            print(yaml.dump(data))

    elif args.cmd in {"version", "v"}:
        args.func(args)
    
    
if __name__ == "__main__":
    main()