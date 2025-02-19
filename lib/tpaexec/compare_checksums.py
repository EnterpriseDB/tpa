#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import argparse
import hashlib
import json
import sys
from pathlib import Path


def get_args(args=None):
    parser = argparse.ArgumentParser(
        "create checksums",
        description="Load a directory of files to create checksum hashes for each one",
    )
    parser.add_argument(
        "directory", metavar="PATH", help="Path to directory containing files"
    )
    parser.add_argument(
        "checksums_file",
        metavar="SAVE_FILE",
        help="Path to the JSON file to which file checksum data is written",
    )
    return parser.parse_args(args)


def _hash_file(path_to_file: Path):
    sha256_hash = hashlib.sha256(path_to_file.read_bytes())
    return sha256_hash


def compare_data(path_to_file: str, target_directory: str):
    mismatch_list = []
    missing_list = []
    try:
        with open(path_to_file, "r", encoding="utf-8") as in_file:
            source_checksums = json.load(in_file)
            for source_filepath, source_hash_value in source_checksums.items():
                target_filepath = Path.joinpath(Path(target_directory), source_filepath)
                if target_filepath.exists() and target_filepath.is_file():
                    calculated_hash_value = _hash_file(target_filepath).hexdigest()

                    if calculated_hash_value != source_hash_value:
                        mismatch_list.append(f"{source_filepath}")
                else:
                    missing_list.append(f"{source_filepath}")

    except IOError:
        sys.exit(1)

    return mismatch_list, missing_list


if __name__ == "__main__":  # pragma: no cover
    args = get_args()
    mismatch_list, missing_list = compare_data(
        path_to_file=args.checksums_file, target_directory=args.directory
    )
    if len(mismatch_list) == 0:
        print(
            f"Validated: {_hash_file(path_to_file=Path(args.checksums_file)).hexdigest()} [OK]"
        )
    else:
        print("Modified:", end=" ")
        print(*mismatch_list, sep=", ")
