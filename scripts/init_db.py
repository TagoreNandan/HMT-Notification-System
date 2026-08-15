#!/usr/bin/env python3
"""Initialize database tables. Idempotent — safe to run manually or on deploy."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.session import init_db


def main() -> None:
    init_db()
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
