#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

import pytest

from pathlib import Path
from tpaexec.compare_checksums import (
    _hash_file,
    compare_data,
    get_args,
)


@pytest.fixture(scope="session")
def setup():
    directory = "lib/tests/checksums/test_directory"
    tampered_missing_directory = "lib/tests/checksums/tampered_missing_test_directory"
    tampered_nested_directory = "lib/tests/checksums/tampered_nested_test_directory"
    paths = list(Path(directory).glob("**/*"))
    extensions = [".json", ".txt", ".yml"]
    source_checksums = "lib/tests/checksums/checksums.json"
    nonexistent_checksums = "lib/tests/checksums/nonexistent_checksums.json"

    return locals()


def test_get_args(setup):
    args = get_args(args=[setup["directory"], setup["source_checksums"]])
    assert args.directory == setup["directory"]
    assert args.checksums_file == setup["source_checksums"]


def test_hash_file(setup):
    for path in setup["paths"]:
        if path.is_file() and path.exists():
            checksum = _hash_file(path_to_file=path)
            assert len(checksum.digest()) == 32
            assert len(checksum.hexdigest()) == 64


def test_compare_data(setup):
    mismatch_list, missing_list = compare_data(
        path_to_file=setup["source_checksums"], target_directory=setup["directory"]
    )
    assert len(mismatch_list) == 0
    assert len(missing_list) == 0

    mismatch_list, missing_list = compare_data(
        path_to_file=setup["source_checksums"],
        target_directory=setup["tampered_nested_directory"],
    )
    assert len(mismatch_list) == 4
    assert len(missing_list) == 0

    mismatch_list, missing_list = compare_data(
        path_to_file=setup["source_checksums"],
        target_directory=setup["tampered_missing_directory"],
    )
    assert len(mismatch_list) == 1
    assert len(missing_list) == 4

    with pytest.raises(SystemExit) as exit:
        compare_data(
            path_to_file=setup["nonexistent_checksums"],
            target_directory=setup["directory"],
        )
    assert exit.type == SystemExit
