"""Compatibility entrypoint.

Keep this file temporarily so existing commands like:
    python burr_compare.py ...
still work after the refactor.
"""

from compare.burr_compare.cli import main


if __name__ == "__main__":
    main()