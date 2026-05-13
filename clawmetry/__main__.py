"""Allow `python3 -m clawmetry` to invoke the CLI entry point.

Without this module Python emits "No module named clawmetry.__main__".
The CLI's argparse-based `main()` lives in clawmetry.cli.
"""

from clawmetry.cli import main

if __name__ == "__main__":
    main()
