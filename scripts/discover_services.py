#!/usr/bin/env python3
"""CLI wrapper for admin-only subscription service discovery."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from admin_tools.cancellation_discovery.discover import main

if __name__ == "__main__":
    main()
