#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

"""Refresh the default AWS AMIs in TPA's platform map.

Reads the `images` dict from `lib/tpa/platforms/aws.py`, finds the latest
AMI in each family in AWS, and rewrites both `lib/tpa/platforms/aws.py`
and `lib/tpaexec/platforms/aws.py` if newer images are available.

Two family patterns are recognised:

* Date-suffix (Debian, Ubuntu, SLES) — the version is fixed in the AMI name
  and only the trailing date changes. Latest by CreationDate wins.
* Minor-floating (RHEL, Rocky) — the minor version is part of the AMI name.
  Pick the highest minor available, and within that the latest CreationDate.

Fails loud (non-zero exit, descriptive error on stderr) on any anomaly: the
AMI map can't be parsed, the two files are out of sync, an AMI name isn't in
a recognised family, or an AWS query returns zero matches.
"""

import ast
import os
import re
import sys
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parents[2]
FILES = [
    REPO_ROOT / "lib" / "tpa" / "platforms" / "aws.py",
    REPO_ROOT / "lib" / "tpaexec" / "platforms" / "aws.py",
]
REGION = os.environ.get("AWS_REGION", "eu-west-1")


def parse_images(path):
    """Return the `images` dict literal from the `image()` method of `aws.py`."""
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "image":
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "images"
                ):
                    return ast.literal_eval(stmt.value)
    raise RuntimeError(f"Could not locate 'images = {{...}}' in {path}")


def family_for(name):
    """Return (AWS name pattern, sort key) for an AMI name.

    The sort key is consumed by `max()`, so higher = better.
    """
    # debian-{maj}-{amd64,arm64}-{date}-{N}
    m = re.match(r"^(debian-\d+-(?:amd64|arm64)-)\d+-\d+$", name)
    if m:
        return f"{m.group(1)}*", lambda img: img["CreationDate"]

    # ubuntu/images/{storage}/ubuntu-{codename}-{ver}-{arch}-server-{date}
    m = re.match(
        r"^(ubuntu/images/[^/]+/ubuntu-[a-z]+-\d+\.\d+-(?:amd64|arm64)-server-)\d+$",
        name,
    )
    if m:
        return f"{m.group(1)}*", lambda img: img["CreationDate"]

    # suse-sles-{maj}-sp{N}-v{date}-ecs-hvm-ssd-{arch}
    m = re.match(r"^(suse-sles-\d+-sp\d+-v)\d+(-ecs-hvm-ssd-(?:x86_64|arm64).*)$", name)
    if m:
        prefix, suffix = m.group(1), m.group(2)
        return f"{prefix}*{suffix}", lambda img: img["CreationDate"]

    # RHEL-{maj}.{min}[.0]_HVM-{date}-{arch}-{N}-Hourly2-GP3
    m = re.match(
        r"^RHEL-(\d+)\.\d+(?:\.\d+)?_HVM-\d+-(x86_64|arm64)-\d+-Hourly2-GP3$",
        name,
    )
    if m:
        major, arch = m.group(1), m.group(2)
        pattern = f"RHEL-{major}.*_HVM-*-{arch}-*-Hourly2-GP3"
        minor_re = re.compile(rf"^RHEL-{major}\.(\d+)(?:\.\d+)?_HVM-")

        def sort_key(img):
            mm = minor_re.match(img["Name"])
            return (int(mm.group(1)) if mm else -1, img["CreationDate"])

        return pattern, sort_key

    # Rocky-{maj}-EC2-Base-{maj}.{min}-{date}.{N}.{arch}
    m = re.match(r"^Rocky-(\d+)-EC2-Base-\d+\.\d+-\d+\.\d+\.(x86_64|aarch64)$", name)
    if m:
        major, arch = m.group(1), m.group(2)
        pattern = f"Rocky-{major}-EC2-Base-*.{arch}"
        minor_re = re.compile(rf"^Rocky-{major}-EC2-Base-\d+\.(\d+)-")

        def sort_key(img):
            mm = minor_re.match(img["Name"])
            return (int(mm.group(1)) if mm else -1, img["CreationDate"])

        return pattern, sort_key

    raise RuntimeError(f"Unrecognised AMI family: {name!r}")


def find_latest(ec2, owner, pattern, sort_key):
    """Return the AMI dict with the highest sort_key from AWS."""
    response = ec2.describe_images(
        Owners=[owner],
        Filters=[{"Name": "name", "Values": [pattern]}],
    )
    if not response["Images"]:
        raise RuntimeError(f"AWS returned 0 AMIs for owner={owner} pattern={pattern!r}")
    return max(response["Images"], key=sort_key)


def main():
    parsed = [parse_images(f) for f in FILES]
    if parsed[0] != parsed[1]:
        print(
            f"ERROR: AMI maps in {FILES[0]} and {FILES[1]} differ; " "refusing to run.",
            file=sys.stderr,
        )
        return 1

    ec2 = boto3.client("ec2", region_name=REGION)
    updates = []

    for distro, entries in parsed[0].items():
        for current_name, attrs in entries.items():
            try:
                pattern, sort_key = family_for(current_name)
            except RuntimeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1
            try:
                latest = find_latest(ec2, attrs["owner"], pattern, sort_key)
            except RuntimeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1
            if latest["Name"] != current_name:
                print(f"  {distro}: {current_name}\n      -> {latest['Name']}")
                updates.append((current_name, latest["Name"]))

    if not updates:
        print("All AMIs are at latest; no changes needed.")
        return 0

    for path in FILES:
        text = path.read_text()
        for old, new in updates:
            text = text.replace(f'"{old}"', f'"{new}"')
        path.write_text(text)

    print(f"\nUpdated {len(updates)} AMI(s) in {len(FILES)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
