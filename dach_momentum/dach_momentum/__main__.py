"""
Package entry point: python -m dach_momentum

Dispatches to submodules based on command-line argument:
    python -m dach_momentum universe              -> build the ticker universe
    python -m dach_momentum universe --refresh    -> force rebuild regardless of age
    python -m dach_momentum data                  -> download prices & filter (uses cache if fresh)
    python -m dach_momentum data --refresh        -> force full re-download
    python -m dach_momentum signals               -> compute signals
    python -m dach_momentum freshness             -> print data freshness report
    python -m dach_momentum                       -> default: universe
"""
import sys


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "universe"
    refresh = "--refresh" in args

    if cmd == "universe":
        from .universe import main as universe_main
        universe_main(refresh=refresh)
    elif cmd == "data":
        from .data import main as data_main
        data_main(refresh=refresh)
    elif cmd == "signals":
        from .signals import main as signals_main
        signals_main()
    elif cmd == "freshness":
        from .data import print_data_freshness
        print_data_freshness()
    else:
        print(f"Unknown command: {cmd}")
        print(
            "Usage: python -m dach_momentum "
            "[universe|data|signals|freshness] [--refresh]"
        )
        sys.exit(1)


main()
