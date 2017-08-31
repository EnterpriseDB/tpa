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
  conninfo:
    description:
      - A conninfo string for this server
    required: false
    default: ""
notes:
   - This module requires the I(psycopg2) Python library to be installed.
requirements: [ psycopg2 ]
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
'''

EXAMPLES = '''
- name: Collect facts about the Postgres cluster
  cluster_discovery:
    conninfo: dbname=postgres
  register: p
- debug: msg="the data directory is {{ p.postgres_data_dir }}"
'''

import io
import os
import sys
import pwd
import grp

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2_found = False
else:
    psycopg2_found = True

def main():

    # We are passed in all of the overridable values set by postgres/vars, and
    # have to test to see if they match this instance in reality. Then we can
    # query the server and discover its role in the cluster.

    module = AnsibleModule(
        argument_spec=dict(
            conninfo=dict(default=""),
        ),
        supports_check_mode = True
    )

    if not psycopg2_found:
        module.fail_json(msg="the python psycopg2 module is required")

    m = dict(changed=False)

    # We need to connect to Postgres as a superuser. The caller must provide a
    # suitable conninfo string and invoke this module as a user that can use it
    # to connect.

    conninfo = module.params['conninfo']
    try:
        conn = psycopg2.connect(dsn=conninfo)
        cur = conn.cursor()

        m['pg_settings'] = settings = {}
        cur.execute('SELECT name,setting FROM pg_settings')
        for s in cur.fetchall():
            settings.update({s[0]: s[1]})

        m['postgres_port'] = int(settings['port'])
        m['postgres_data_dir'] = settings['data_directory']

        cur.execute('SELECT version()')
        m['postgres_version_string'] = cur.fetchone()[0]
        m['postgres_version_int'] = conn.server_version
        m['postgres_version'] = '%d.%d.%d' % (
            (conn.server_version/10000)%10,
            (conn.server_version/100)%10,
            (conn.server_version)%10,
        )

        cur.execute('SELECT pg_backend_pid()')
        pid = cur.fetchone()[0]
        m['postgres_bin_dir'] = os.path.dirname(os.readlink('/proc/%d/exe' % pid))

        with io.open('/proc/%d/status' % pid, 'r') as status:
            for line in status:
                s = line.split()

                if s[0] == 'Uid:':
                    ent = pwd.getpwuid(int(s[1]))
                    m['postgres_user'] = ent.pw_name
                    m['postgres_home'] = ent.pw_dir
                    
                elif s[0] == 'Gid:':
                    ent = grp.getgrgid(int(s[1]))
                    m['postgres_group'] = ent.gr_name

        cur.execute('SELECT pg_is_in_recovery()')
        m['postgres_is_in_recovery'] = cur.fetchone()[0]

    except Exception as e:
        m['error'] = str(e)

    # If we can't connect, all we can do is to check a few likely
    # places to see if we can find matches for the basic OS-level facts.

    m['failed'] = 'error' in m

    module.exit_json(**m)

from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()
