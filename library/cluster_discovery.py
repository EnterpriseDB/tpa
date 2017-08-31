#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: cluster_discovery
short_description: Discover a Postgres server's place in a cluster
description:
   - Performs a sequence of tests against a Postgres server and returns the
     results as ordinary variables (not as ansible facts, which is why this
     module is not named postgresql_facts).
version_added: "2.4"
options:
  postgres_version:
    description:
      - The declared Postgres version number (m.n)
    required: true
  postgres_user:
    description:
      - The declared Postgres system username
    required: true
  postgres_group:
    description:
      - The declared Postgres system group name
    required: true
  postgres_home:
    description:
      - The declared Postgres system user's home directory
    required: true
  postgres_bin_dir:
    description:
      - The declared Postgres binary installation path
    required: true
  postgres_data_dir:
    description:
      - The declared Postgres data directory
    required: true
  postgres_host:
    description:
      - The declared Postgres server hostname or address
    required: true
  postgres_port:
    description:
      - The declared Postgres server port number
    required: true
  postgres_service_name:
    description:
      - The declared Postgres init service name
    required: true
notes:
   - This module requires the I(psycopg2) Python library to be installed.
requirements: [ psycopg2 ]
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
'''

EXAMPLES = '''
- name: Collect facts about the Postgres cluster
  cluster_discovery:
    postgres_version: "{{ postgres_version }}"
    postgres_user: "{{ postgres_user }}"
    postgres_group: "{{ postgres_group }}"
    postgres_home: "{{ postgres_home }}"
    postgres_bin_dir: "{{ postgres_bin_dir }}"
    postgres_data_dir: "{{ postgres_data_dir }}"
    postgres_host: "{{ postgres_host }}"
    postgres_port: "{{ postgres_port }}"
    postgres_service_name: "{{ postgres_service_name }}"
  register: p
- debug: msg="the data directory is {{ p.postgres_data_dir }}"
'''

import os
import sys

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2_found = False
else:
    psycopg2_found = True

def main():
    module = AnsibleModule(
        argument_spec=dict(
            postgres_version=dict(required=True),
            postgres_user=dict(required=True),
            postgres_group=dict(required=True),
            postgres_home=dict(required=True),
            postgres_bin_dir=dict(required=True),
            postgres_data_dir=dict(required=True),
            postgres_host=dict(required=True),
            postgres_port=dict(required=True),
            postgres_service_name=dict(required=True)
        ),
        supports_check_mode = True
    )

    if not psycopg2_found:
        module.fail_json(msg="the python psycopg2 module is required")

    m = dict(changed=False)

    module.exit_json(**m)

from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()
