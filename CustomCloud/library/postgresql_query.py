#!/usr/bin/python
# -*- coding: utf-8 -*-

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
      - Text of the SQL query to execute.
    required: true
    default: null
  conninfo:
    description:
      - A conninfo string to define connection parameters
    required: true
    default: ""
notes:
   - This module requires the I(psycopg2) Python library to be installed.
requirements: [ psycopg2 ]
author: "Abhijit Menon-Sen <ams@2ndQuadrant.com>"
'''

EXAMPLES = '''
- postgresql_query:
    query: "SELECT 42 as a"
    conninfo: "dbname=postgres"
  register: query
- debug: msg="the answer is {{ query.results[0].a }}"
'''

RETURN = '''
results:
    description: Name of the schema
    returned: success, changed
    type: string
    sample: "acme"
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
            query=dict(required=True),
            conninfo=dict(default=""),
        ),
        supports_check_mode = False
    )

    if not psycopg2_found:
        module.fail_json(msg="the python psycopg2 module is required")

    query = module.params["query"]
    conninfo = module.params["conninfo"]
    changed = False
    results = []

    try:
        conn = psycopg2.connect(dsn=conninfo)
    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to connect to database: %s" %(text, str(e)))

    try:
        cur = conn.cursor()
        cur.execute(query)
        column_names = [desc[0] for desc in cur.description]
        for row in cur:
            results.append(dict(zip(column_names, row)))
        cur.close()
        conn.close()
    except NotSupportedError:
        e = get_exception()
        module.fail_json(msg=str(e))
    except SystemExit:
        # Avoid catching this on Python 2.4
        raise
    except Exception:
        e = get_exception()
        module.fail_json(msg="Database query failed: %s" % (str(e)))

    module.exit_json(changed=changed, results=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.database import *

if __name__ == '__main__':
    main()
