#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This module expects to be invoked on an instance «with: 'postgres' in role».

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
  become_user: "{{ postgres_user }}"
  become: yes
  register: p
- debug: msg="the data directory is {{ p.postgres_data_dir }}"
'''

import os, io, sys, pwd, grp

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

    conn = None
    conninfo = module.params['conninfo']
    try:
        conn = psycopg2.connect(dsn=conninfo)
        cur = conn.cursor()

        # First, we discover postgres_version and its variants.

        cur.execute('SELECT version()')
        m['postgres_version_string'] = cur.fetchone()[0]
        m['postgres_version_int'] = conn.server_version
        m['postgres_version'] = '%d.%d' % (
            (conn.server_version/10000)%10,
            (conn.server_version/100)%10,
        )

        # We collect and return everything in pg_settings, and use that to also
        # fill in postgres_data_dir and postgres_port. (There's no easy way to
        # discover postgres_host, but we wouldn't have been able to connect to
        # Postgres in the first place if we didn't have a pretty good idea of
        # what it was set to.)

        m['pg_settings'] = settings = {}
        cur.execute('SELECT name,setting FROM pg_settings')
        for s in cur.fetchall():
            settings.update({s[0]: s[1]})

        m['postgres_port'] = int(settings['port'])
        m['postgres_data_dir'] = settings['data_directory']

        # A backend pid leads us to /proc/<pid>/{exe,status}, whence we can find
        # postgres_bin_dir, postgres_user, postgres_group, and postgres_home. We
        # assume that we are either running as root, or have permission to read
        # this because we're running as the same user as postgres.

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

        # We're done with the basic system facts, so we move on to querying the
        # server to get an idea of its place in the world^Wcluster.

        m['query'] = query = {}
        cur.execute('SELECT pg_is_in_recovery()')
        query['pg_is_in_recovery'] = cur.fetchone()[0]

    except Exception as e:
        m['error'] = str(e)
        if conn is not None:
            m['failed'] = 'error' in m

    # If we can't connect, all we can do is to check a few likely
    # places to see if we can find matches for the basic OS-level facts.

    module.exit_json(**m)

from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()
