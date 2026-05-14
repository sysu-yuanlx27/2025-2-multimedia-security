#!/usr/bin/env python3
"""Command entry point for the robust JPEG steganography lab."""

from __future__ import annotations

import argparse

from src.prepare_data import prepare
from src.run_experiment import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare", help="prepare raw datasets for experiments")
    subparsers.add_parser("run", help="run J-UNIWARD and J-UNIWARD-P experiments")

    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "run":
        run()


if __name__ == "__main__":
    main()

