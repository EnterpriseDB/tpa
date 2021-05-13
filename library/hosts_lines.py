#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'EDB'}

DOCUMENTATION = '''
---
module: hosts_lines
short_description: Ensure that the given entries exist in /etc/hosts
description:
  - Takes a path and a list of lines and ensures that each entry exists in the
    file, removing any older entries for matching IP addresses or hostnames.
    Appends any lines that are not already in the file.
version_added: "2.8"
options:
  path:
    description:
      - The path to an existing file
    required: true
  lines:
    description:
      - An array of hosts entries that must exist in the file
    required: true
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
'''

EXAMPLES = '''
- hosts_lines:
    path: /etc/hosts
    lines:
    - 127.0.0.1 localhost
    - 192.0.2.1 example.com
'''

import traceback
import tempfile
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native

def hosts_lines(module):
    m = {}

    path = module.params.get('path')
    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % path,
            'after_header': '%s (content)' % path}

    # Given a list of lines that may include comments, blank lines (which don't
    # do anything useful), and valid hosts entries comprising an IP address and
    # one or more hostnames separated by spaces. We build up the sets of lines,
    # addresses, and hostnames that we need to check existing hosts entries to
    # see if they need to be replaced.

    lines = set()
    to_replace = set()

    for l in module.params.get('lines'):
        lines.add(l)

        if not l.lstrip().startswith('#'):
            words = l.split()
            for n in words:
                to_replace.add(n)

    before_lines = []
    after_lines = []
    changes = []

    try:
        b_path = to_bytes(path, errors='surrogate_or_strict')
        with open(b_path, "r") as f:
            before_lines = f.readlines()

        for line in before_lines:
            l = line.rstrip('\r\n')

            # If a line we want is already there, we copy it to the output and
            # remove it from the list of lines to append. If the line contains
            # an address or name that overlaps with an entry we are adding, we
            # skip it. Otherwise we copy it over unmodified.

            if l in lines:
                lines.remove(l)

            elif not l.lstrip().startswith('#'):
                words = l.split()
                if set(words) & to_replace:
                    changes.append('skip')
                    continue

            after_lines.append(line)

        if lines:
            changes.append('append')
            for l in lines:
                after_lines.append(l + '\n')

        # If we didn't need to skip any existing lines, we can just append the
        # new lines to /etc/hosts. Otherwise we must replace the file, which we
        # prefer to do by writing to a temporary file and using atomic_move; but
        # that doesn't work on Docker containers, so we must overwrite in-place.

        if changes and not module.check_mode:
            contents = to_bytes(''.join(after_lines))

            if 'skip' in changes and module.params['platform'] == 'docker':
                m['operation'] = 'overwrite'
                with open(b_path, "wb") as f:
                    f.write(contents)

            elif 'skip' in changes:
                m['operation'] = 'replace'
                tmpfd, tmpfile = tempfile.mkstemp()
                with os.fdopen(tmpfd, "wb") as f:
                    f.write(contents)
                module.atomic_move(tmpfile, to_native(b_path),
                                   unsafe_writes=module.params['unsafe_writes'])

            else:
                m['operation'] = 'append'
                contents = to_bytes(''.join(map(lambda l: l+'\n', lines)))
                with open(b_path, "ab") as f:
                    f.write(contents)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    diff['before'] = ''.join(before_lines)
    diff['after'] = ''.join(after_lines)
    m['diff'] = [ diff, [] ]
    m['changed'] = bool(changes)

    return m

def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            lines=dict(type='list', required=True),
            unsafe_writes=dict(type='bool'),
            platform=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    module.exit_json(**hosts_lines(module))

if __name__ == '__main__':
    main()
