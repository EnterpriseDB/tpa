#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
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
        a string (i.e., the query text) or a dict with the query 'text' and
        either a list of 'args' to bind to %s placeholders in the query, or a
        dict of 'named_args' to bind to %(name)s placeholders in the query.
        All of the queries are executed in the same transaction.
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
"""

EXAMPLES = """
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
      - text: insert into y(p,q) values (%(p)s, %(q)s)
        named_args:
          p: "hello"
          q: "world"
- debug: msg="{{ query.rowcounts[0] }} rows"
- debug: msg="also {{ query.rowcount }} rows"
  when:
    query.rowcounts|length == 1
"""

RETURN = """
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
runtimes:
    description: An array of runtimes (in seconds) from each query executed.
    type: list
    sample: [
        0.003,
        1.232,
        0.015
    ]
runtime:
    description: If only one query was executed, the runtime is set separately
    as a single floating-point number (in addition to the 'runtimes' array).
    type: float
    sample: 42.321
"""

from ansible.module_utils.six import string_types
from ansible.module_utils.basic import AnsibleModule

import traceback
import time

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2_found = False
else:
    psycopg2_found = True


def get_queries(module):
    """
    Return a list of queries to process, regardless of which calling convention
    happens to be in use. May fail if the calling convention in use isn't one we
    recognise.
    """
    queries = module.params["queries"] or module.params["query"]
    if isinstance(queries, string_types):
        queries = [queries.strip()]
        if queries[0].startswith("["):
            module.fail_json(
                msg="you probably didn't mean to pass this query as a list"
            )
        if queries[0].startswith("{"):
            module.fail_json(
                msg="you probably didn't mean to pass this query as a dict"
            )
    return queries


def get_query(q):
    """
    Given an entry from 'queries', returns the text of the query as well as the
    arguments, which may be either a list (args) or a dict (named_args) or an
    empty list (if only the query text is specified).

    May modify q to reflect changes to the argument list.
    """
    text = q
    args = []
    if isinstance(q, dict):
        text = q["text"]

        # The query entry may specify either named_args for %(name)s
        # placeholders, or just args for %s placeholders. The former
        # take precedence if specified.
        named_args = q.get("named_args", {})
        args = q.get("args", [])

        # We use this test to filter out or transform omitted values
        # from the query arguments list.
        def is_null(s):
            """
            Returns true if the value passed in looks like the result of
            specifying NULL via "|default(omit)" for a query parameter.
            """
            return isinstance(s, str) and s.startswith("__omit_place_holder__")

        if named_args:
            # XXX: We'd like to support explicit NULLs with 'omit', the
            # way we do below, but hash keys don't get passed in to us
            # at all if you specify `key: "{{ omit }}"`, so we can't.
            args = named_args
        elif args:
            args = list(map(lambda s: s if not is_null(s) else None, args))
            # We modify the query entry here so that the module result includes
            # the processed arguments.
            q["args"] = args

    return text, args


def main():
    module = AnsibleModule(
        argument_spec=dict(
            conninfo=dict(default=""),
            queries=dict(type="list"),
            query=dict(type="str"),
            autocommit=dict(type="bool", default=False),
        ),
        required_one_of=[["query", "queries"]],
        mutually_exclusive=[["query", "queries"]],
        supports_check_mode=True,
    )

    if not psycopg2_found:
        module.fail_json(msg="the python psycopg2 module is required")

    conninfo = module.params["conninfo"]
    try:
        conn = psycopg2.connect(dsn=conninfo)
    except Exception as e:
        return module.fail_json(
            msg="Could not connect to database",
            err=str(e),
            exception=traceback.format_exc(),
        )

    autocommit = module.params["autocommit"]
    if autocommit:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    m = dict()
    changed = False

    queries = get_queries(module)
    m["queries"] = queries

    results = []
    runtimes = []
    rowcounts = []
    try:
        for q in queries:
            cur = conn.cursor()

            text, args = get_query(q)

            starttime = time.time()
            cur.execute(text, args)
            runtime = round(time.time() - starttime, 3)

            res = []
            if cur.description is not None:
                column_names = [desc[0] for desc in cur.description]
                for row in cur:
                    res.append(dict(list(zip(column_names, row))))
            elif cur.rowcount:
                changed = True

            rowcounts.append(cur.rowcount)
            results.append(res)
            runtimes.append(runtime)
            cur.close()
    except Exception as e:
        try:
            conn.rollback()
        except psycopg2.InterfaceError:
            pass
        module.fail_json(
            msg="Database query failed",
            err=str(e),
            exception=traceback.format_exc(),
            **m
        )
    else:
        if module.check_mode:
            conn.rollback()
        else:
            conn.commit()

    if len(results) == 1:
        results = results[0]
    if len(results) == 1 and len(results[0]) == 1:
        m.update(results[0])

    m["runtimes"] = runtimes
    if len(runtimes) == 1:
        m["runtime"] = runtimes[0]
    m["rowcounts"] = rowcounts
    if len(rowcounts) == 1:
        m["rowcount"] = rowcounts[0]

    module.exit_json(changed=changed, results=results, **m)


if __name__ == "__main__":
    main()
