#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

# Connects to each of the given conninfos and issues insert queries every second
# into a test table. Reconnects and retries if there's any error, and reports on
# any interruptions.

from __future__ import absolute_import, division, print_function

import sys, time, datetime
import psycopg2
from psycopg2 import Error

connections = {}
states = {}
nodes = {}
bad_times = {}
last_errors = {}


def connect(conninfo):
    conn = psycopg2.connect(conninfo, connect_timeout=2)
    conn.autocommit = True
    return conn


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            create table if not exists tpa_proxy_monitor (
                t timestamp with time zone not null,
                conninfo text not null,
                node text not null)"""
        )


def wait_for_replication(conn):
    with conn.cursor() as cur:
        cur.execute("select bdr.wait_slot_confirm_lsn(null, null)")


def current_node(conn):
    with conn.cursor() as cur:
        cur.execute("show cluster_name")
        res = cur.fetchone()
        return res[0]


def insert_row(conn, now, conninfo, node):
    with conn.cursor() as cur:
        cur.execute(
            "insert into tpa_proxy_monitor (t, conninfo, node) values (%s, %s, %s)",
            (now, conninfo, node),
        )


def main():
    if len(sys.argv) == 1:
        sys.exit(f"Usage: {sys.argv[0]} 'conninfo' 'conninfo' …")

    conninfos = sys.argv[1:]

    start = datetime.datetime.now()

    while True:
        now = datetime.datetime.now()

        if (now - start) / datetime.timedelta(seconds=1) > 3600:
            print(f"[{now}] Exiting after one hour")
            sys.exit(0)

        for conninfo in conninfos:
            try:
                conn = connections.get(conninfo)

                if not conn:
                    conn = connections[conninfo] = connect(conninfo)

                node = nodes[conninfo] = current_node(conn)

                if not states.get(conninfo):
                    create_table(conn)
                    wait_for_replication(conn)
                    states[conninfo] = "initialised"

                insert_row(conn, now, conninfo, node)

                # If we reached here, we've successfully connected, perhaps
                # created the table, and now executed an INSERT. If it's the
                # first time, or the first time after a series of errors, we
                # should say something about it. To reduce chatter, we remain
                # quiet when things are running as expected, and emit updates
                # only when we transition states or something goes wrong.

                if states[conninfo] == "initialised":
                    print(f"[{now}] connected to {node} via '{conninfo}'")

                elif states[conninfo] == "bad":
                    delta = round(
                        (now - bad_times[conninfo]) / datetime.timedelta(seconds=1)
                    )
                    print(
                        f"[{now}] connected to {node} via '{conninfo}' "
                        f"(after downtime of {delta} seconds)"
                    )
                    del last_errors[conninfo]
                    del bad_times[conninfo]

                states[conninfo] = "excellent"

            except Error as e:
                err = str(e).strip()
                node = nodes.get(conninfo, "unknown")

                # If we failed while trying to create the tables, retrying isn't
                # likely to improve matters. Safest to just bail out.

                if not states.get(conninfo):
                    print(
                        f"[{now}] FATAL: initialisation failed (connected to "
                        f"{node} via '{conninfo}'): {err}"
                    )
                    sys.exit(-1)

                # Other than that, errors while trying to connect or run a query
                # are just ordinary events to keep track of.

                else:
                    if err != last_errors.get(conninfo):
                        if not connections.get(conninfo):
                            print(f"[{now}] connection failed (to '{conninfo}'): {err}")
                        else:
                            print(
                                f"[{now}] query failed (connected to {node} "
                                f"via '{conninfo}'): {err}"
                            )

                    states[conninfo] = "bad"
                    last_errors[conninfo] = err
                    if conninfo not in bad_times:
                        bad_times[conninfo] = now

                    # We could catch OperationalError here, to differentiate
                    # between problems that do or do not require the connection
                    # to be abandoned. In practice, we know the queries we run,
                    # and we know that connection errors are most likely.
                    #
                    # XXX Are we leaking something by not closing the connection
                    # here, though?

                    connections[conninfo] = None

            sys.stdout.flush()
        time.sleep(1)


if __name__ == "__main__":
    main()
