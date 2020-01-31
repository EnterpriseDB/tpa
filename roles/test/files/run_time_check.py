#!/usr/bin/env python

from __future__ import print_function

import psycopg2
import csv
import sys
import time
from datetime import datetime
import os

origin_dsn = sys.argv[1]
partner_dsn = sys.argv[2]
local_dsn = sys.argv[3]
csvfile = sys.argv[4]
test_table = sys.argv[5]
expected_xacts = sys.argv[6]
conn_origin=0
conn_partner=0
# datetime object containing current date and time
now = datetime.now()
csvRow = [now, expected_xacts]
emptyRow = ["","","","",""]
all_committed = False
myquery = "SELECT 1 FROM pg_catalog.pg_class c INNER JOIN pg_catalog.pg_namespace n ON (c.relnamespace = n.oid) WHERE relname ='{}'".format(test_table)
if os.path.exists(csvfile):
  os.remove(csvfile)

# register csv dialect and enter first header
csv.register_dialect('mydialect',
delimiter = '|',
quoting=csv.QUOTE_NONE,
skipinitialspace=True)
with open(csvfile, "a") as fp:
    wr = csv.writer(fp, dialect='mydialect')
    wr.writerow(["timestamp","expected_xacts","origin","origin_xact","origin_prepared_xact","partner_connected", "partner_ready","partner","partner_xact","partner_prepared_xact","partner_connected", "partner_ready"])
fp.close()

# Generate a csv report of statistics collected
def generate_report():
    with open(csvfile, "a") as fp:
        wr = csv.writer(fp, dialect='mydialect')
        wr.writerow(csvRow)
    fp.close()

def get_stats(conn):
    try:
        cur = conn.cursor()
        cur.execute('SELECT interface_name from bdr.local_node_summary')
        node_name = cur.fetchone()[0]
        cur.execute('SELECT count(*) FROM camo_test')
        xacts = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM pg_prepared_xacts')
        prepared_xacts = cur.fetchone()[0]
        cur.execute('SELECT bdr.is_camo_partner_connected()')
        partner_connected = cur.fetchone()[0]
        cur.execute('SELECT  bdr.is_camo_partner_ready()')
        partner_ready = cur.fetchone()[0]
        newRow = [node_name, xacts, prepared_xacts,partner_connected,partner_ready]
        csvRow.extend(newRow)
        #closing database connnection.
        cur.close()
        conn.close()
         
    except:
        print("Something wrong with the connection or queries")
        csvRow.extend(emptyRow)



# Get local connection
# Continue to get statistics until tets table exists
try:
    conn_local=psycopg2.connect(local_dsn)
    cur_local=conn_local.cursor()
    cur_local.execute(myquery)
    test_valid = cur_local.fetchone()[0]
    cur_local.close()
    conn_local.close()
except:
    test_valid = 0

while test_valid:
   
    # Try to get connection to origin
    try:
        conn_origin=psycopg2.connect(origin_dsn, connect_timeout=5)
    except:
        print("I am unable to connnect to the origin: '%s'" % origin_dsn)
        
    # Try to get connection to partner
    try:
        conn_partner=psycopg2.connect(partner_dsn,connect_timeout=5)
    except:
        print("I am unable to connnect to the partner: '%s'" % partner_dsn)
        
    # If connection ito origin is established
    # get statistics from the node else enter empty values
    if(conn_origin):
        get_stats(conn_origin)
    else:
        csvRow.extend(emptyRow)
        
    
    # If connection to partner is established
    # get statistics from the node else enter empty values
    if(conn_partner):
        get_stats(conn_partner)
    else:
        csvRow.extend(emptyRow)
    
    # Generate a csv report with above statistics
    generate_report()
    
    # Continue until test runs. `camo_test` table is deleted at the end of the tests
    retry_counter = 12
    while True:
        try:
            conn_local=psycopg2.connect(local_dsn)
            break
        except:
            print("Retry establishing local connection")
            time.sleep(5)
            retry_counter = retry_counter - 1
        if(retry_counter == 0):
            print("Could not establish local connection. Exiting")
            sys.exit()
        
    cur_local=conn_local.cursor()
    cur_local.execute(myquery)
    table_exists=cur_local.fetchone()
    if table_exists and not all_committed:
        if long(csvRow[1]) == csvRow[3] == csvRow[8]:
            all_committed = True
        test_valid = 1
        time.sleep(3)
        now = datetime.now()
        csvRow = [now, expected_xacts]
    else: 
        cur_local.close()
        conn_local.close()
        sys.exit()
