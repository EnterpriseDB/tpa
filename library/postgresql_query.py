#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
      - Text of the SQL query to execute, or a list of queries. Instead of the
        query text alone, may also be a dict with 'text' and 'args'. All of the
        queries are executed in the same transaction.
    required: true
  conninfo:
    description:
      - A conninfo string to define connection parameters
    required: false
    default: "''"
notes:
   - This module requires the I(psycopg2) Python library to be installed.
requirements: [ psycopg2 ]
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
'''

EXAMPLES = '''
- postgresql_query:
    query: SELECT 42 as a
    conninfo: "dbname=postgres"
  register: query
- debug: msg="the answer is {{ query.results[0].a }}"
- postgresql_query:
    query:
      - text: insert into x(a,b) values (%s, %s)
        args:
          - 42
          - foo
      - SELECT 42 as a
- debug: msg="{{ query.rowcounts[0] }} rows"
'''

RETURN = '''
rowcounts:
    description: An array of rowcounts from each query executed.
    type: list
results:
    description: An array of dicts, each containing data from a single row of
    query results. If multiple queries are specified, then this is an array of
    arrays of dicts instead.
    returned: success, changed
    type: list
    sample: [
        {
            "a": 42
        }
    ]
'''

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2_found = False
else:
    psycopg2_found = True


class NotSupportedError(Exception):
    pass


def main():
    module = AnsibleModule(
        argument_spec=dict(
            conninfo=dict(default=""),
            query=dict(required=True, type='list'),
        ),
        supports_check_mode = False
    )

    if not psycopg2_found:
        module.fail_json(msg="the python psycopg2 module is required")

    conninfo = module.params["conninfo"]
    try:
        conn = psycopg2.connect(dsn=conninfo)
    except Exception, e:
        module.fail_json(msg="Could not connect to database", err=str(e))

    m = dict()
    changed = False

    results = []
    rowcounts = []
    try:
        for q in module.params['query']:
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
    except Exception, e:
        conn.rollback()
        module.fail_json(msg="Database query failed", err=str(e))
    else:
        conn.commit()

    if len(results) == 1:
        results = results[0]
    if len(results) == 1 and len(results[0]) == 1:
        for k,v in results[0].iteritems():
            m[k] = v

    m['changed'] = changed
    m['rowcounts'] = rowcounts
    module.exit_json(results=results, **m)

from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()
