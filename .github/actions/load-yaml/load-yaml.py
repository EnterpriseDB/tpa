#!/usr/bin/env python3
#  © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.
"""Load a YAML file to use as input for a Github action."""

import argparse

import yaml
import json


def get_args():
    parser = argparse.ArgumentParser('load-yaml', description="Load a YAML file for input to Github action")
    parser.add_argument('data', metavar='FILE', type=read_data, help='Path to YAML file')
    parser.add_argument('key', nargs="?", help='Optional top level key name to return')
    return parser.parse_args()


def read_data(file_name):
    with open(file_name) as fh:
        return yaml.safe_load(fh)


def main():
    args = get_args()
    data = args.data[args.key] if args.key else args.data
    print(f'::set-output name=json::{json.dumps(data)}')


if __name__ == '__main__':
    main()
