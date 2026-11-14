#!/usr/bin/env python3
"""Command-line entry point; the score helper remains available for imports."""

from agi_benchmark.cli import main
from agi_benchmark.core import score


if __name__ == "__main__":
    raise SystemExit(main())
