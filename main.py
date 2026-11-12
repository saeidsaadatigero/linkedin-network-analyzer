# main.py
"""Entry point: python main.py [--input PATH]"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.config import OUTPUT_DIR, PROCESSED_DIR, RAW_DATA_PATH
from src.exceptions import ProjectError
from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    """Parse CLI args; input defaults to the fixed synthetic data file."""
    parser = argparse.ArgumentParser(description="Synthetic profile graph and skill analysis.")
    parser.add_argument("--input", type=Path, default=RAW_DATA_PATH, help="Path to raw profiles JSON.")
    return parser.parse_args()


def main() -> int:
    """Wire logging, run the pipeline, convert project errors to exit code 1."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    args = parse_args()
    try:
        run_pipeline(args.input, PROCESSED_DIR, OUTPUT_DIR)
    except ProjectError as exc:
        logging.getLogger("main").error("Pipeline failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
