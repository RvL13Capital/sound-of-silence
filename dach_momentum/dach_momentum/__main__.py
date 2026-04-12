"""
Package entry point: python -m dach_momentum

Dispatches to submodules based on command-line argument:
    python -m dach_momentum universe   -> build the ticker universe
    python -m dach_momentum data       -> download prices & filter
    python -m dach_momentum            -> default: universe
"""
import sys


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "universe"

    if cmd == "universe":
        from .universe import main as universe_main
        universe_main()
    elif cmd == "data":
        from .data import main as data_main
        data_main()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python -m dach_momentum [universe|data]")
        sys.exit(1)


main()
