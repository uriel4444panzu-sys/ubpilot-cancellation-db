#!/usr/bin/env python3
"""Launch the local admin web interface for cancellation discovery."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from admin_tools.cancellation_discovery.webapp import main

if __name__ == "__main__":
    main()
