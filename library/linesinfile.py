#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["stableinterface"],
    "supported_by": "2ndQuadrant",
}

DOCUMENTATION = """
---
module: linesinfile
short_description: Ensure that the given lines exist somewhere in a file
description:
  - Takes a path and a list of lines and ensures that each line exists in the
    file. Appends any lines that are not already in the file.
version_added: "2.6"
options:
  path:
    description:
      - The path to an existing file
    required: true
  lines:
    description:
      - An array of lines that must exist in the file
    required: true
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
"""

EXAMPLES = """
- linesinfile:
    path: /etc/hosts
    lines:
    - 127.0.0.1 localhost
    - 192.0.2.1 example.com
"""

import traceback

from ansible.module_utils.basic import AnsibleModule


def linesinfile(module):
    m = {}

    path = module.params.get("path")
    diff = {
        "before": "",
        "after": "",
        "before_header": "%s (content)" % path,
        "after_header": "%s (content)" % path,
    }

    lines = {}
    b_lines = []
    a_lines = []
    for l in module.params.get("lines"):
        lines[l] = 1

    try:
        with open(path, "a+") as f:
            f.seek(0)
            for line in f:
                b_lines.append(line)
                a_lines.append(line)
                line = line.rstrip("\r\n")
                if line in lines:
                    del lines[line]

            if lines:
                m["changed"] = True
                for l in lines:
                    if not module.check_mode:
                        f.write(l + "\n")
                    a_lines.append(l + "\n")
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    diff["before"] = "".join(b_lines)
    diff["after"] = "".join(a_lines)
    m["diff"] = [diff, []]

    return m


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type="path", required=True),
            lines=dict(type="list", required=True),
        ),
        supports_check_mode=True,
    )

    module.exit_json(**linesinfile(module))


if __name__ == "__main__":
    main()
