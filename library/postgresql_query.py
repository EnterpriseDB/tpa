#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: postgresql_query
short_description: Query a Postgres server
description:
   - Perform a query against a PostgreSQL server and return an array of result
     rows, each one a dict mapping field names to values.
version_added: "2.4"
options:
  query:
    description:
      - Text of an SQL query to execute. (This form does not accept text and
        args separately; if you want to use placeholders, use 'queries'.)
        You must specify exactly one of 'query' or 'queries'.
    required: true
  queries:
    description:
      - A list of SQL queries to execute. Each element in the list may be either
        a string (i.e., the query text) or a dict with the query 'text' and a
        list of 'args' to bind to %s placeholders in the query. All of the
        queries are executed in the same transaction.
        You must specify exactly one of 'query' or 'queries'.
    required: true
  conninfo:
    description:
      - A conninfo string to define connection parameters
    required: false
    default: "''"
  autocommit:
    description:
      - Defines if queries should be run with AUTOCOMMIT isolation mode.
        Some queries like VACUUM or CREATE DATABASE can't run within a transaction.
        For such statements autocommit should be set to 'yes'.
    required: false
    default: 'no'
notes:
   - This module requires the I(psycopg2) Python library to be installed.
   - This module can execute any sort of query, but you may need to cast some
     result values (e.g., float) to text to retrieve them, because of code in
     Ansible that has limited support for the data types it can handle.
requirements: [ psycopg2 ]
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
'''

EXAMPLES = '''
- postgresql_query:
    query: SELECT 42 as a
    conninfo: "dbname=postgres"
  register: query
- debug: msg="the answer is {{ query.results[0].a }}"
- debug: msg="the answer is also {{ query.a }}"
  when:
    query.rowcounts[0] == 1
- postgresql_query:
    queries:
      - text: insert into x(a,b) values (%s, %s)
        args:
          - 42
          - foo
      - SELECT 42 as a
- debug: msg="{{ query.rowcounts[0] }} rows"
- debug: msg="also {{ query.rowcount }} rows"
  when:
    query.rowcounts|length == 1
'''

RETURN = '''
rowcounts:
    description: An array of rowcounts from each query executed.
    type: list
    sample: [
        1,
        2,
        3
    ]
rowcount:
    description: If only one query was executed, the rowcount is set separately
    as a single integer (in addition to the 'rowcounts' array).
    type: int
    sample: 42
results:
    description: An array of dicts, each containing data from a single row of
    query results. If multiple queries are specified, then this is an array of
    arrays of dicts instead.
    returned: success, changed
    type: list
    sample: [
        {
            "a": 42,
            "b": 31
        }
    ]
'''

from ansible.module_utils.six import string_types
import traceback

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2_found = False
else:
    psycopg2_found = True

def main():
    module = AnsibleModule(
        argument_spec=dict(
            conninfo=dict(default=""),
            queries=dict(type='list'),
            query=dict(type='str'),
            autocommit=dict(type='bool', default=False),
        ),
        required_one_of=[['query','queries']],
        mutually_exclusive=[['query','queries']],
        supports_check_mode = True
    )

    if not psycopg2_found:
        module.fail_json(msg="the python psycopg2 module is required")

    conninfo = module.params["conninfo"]
    try:
        conn = psycopg2.connect(dsn=conninfo)
    except Exception as e:
        module.fail_json(msg="Could not connect to database",
            err=str(e), exception=traceback.format_exc())

    autocommit = module.params["autocommit"]
    if autocommit:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    queries = module.params['queries'] or module.params['query']
    if isinstance(queries, string_types):
        queries = [queries.strip()]
        if queries[0].startswith('['):
            module.fail_json(msg="you probably didn't mean to pass this query as a list")
        if queries[0].startswith('{'):
            module.fail_json(msg="you probably didn't mean to pass this query as a dict")

    m = dict()
    changed = False

    results = []
    rowcounts = []
    try:
        for q in queries:
            cur = conn.cursor()

            text = q
            args = []
            if isinstance(q, dict):
                text = q['text']
                args = q.get('args', [])

            cur.execute(text, args)

            res=[]
            if cur.description is not None:
                column_names = [desc[0] for desc in cur.description]
                for row in cur:
                    res.append(dict(zip(column_names, row)))
            elif cur.rowcount:
                changed=True

            rowcounts.append(cur.rowcount)
            results.append(res)
            cur.close()
    except Exception as e:
        try:
            conn.rollback()
        except psycopg2.InterfaceError:
            pass
        module.fail_json(msg="Database query failed",
            err=str(e), exception=traceback.format_exc())
    else:
        if module.check_mode:
            conn.rollback()
        else:
            conn.commit()

    if len(results) == 1:
        results = results[0]
    if len(results) == 1 and len(results[0]) == 1:
        m.update(results[0])

    m['rowcounts'] = rowcounts
    if len(rowcounts) == 1:
        m['rowcount'] = rowcounts[0]

    module.exit_json(changed=changed, results=results, **m)

from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()
