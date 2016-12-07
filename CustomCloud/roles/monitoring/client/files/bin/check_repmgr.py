#!/usr/bin/env python
import sys
import argparse
import psycopg2
from datetime import timedelta
import re

def get_seconds(td):
	#Get total seconds of a timedelta, not using datetime.timedelta.total_seconds for backward compatibility with Python < 2.7
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

def arg_to_timedelta(arg_string):
	#Get the value and unit from user input using regex. Accepted input includes e.g. "5 minutes" or "1h", if no unit is given we asume seconds
	time_unit_regex = '^\s*(\d+(?:\.\d+)?)\s*(\w*)\s*$'
	matches = re.search(time_unit_regex, arg_string)

	try:
		value = int(matches.group(1))
		#If we get no unit, we set it to seconds
		if matches.group(2) == '':
			unit = 's'
		else:
			unit = matches.group(2)[0]
	except:
		unit = None

	#Evaluating the unit to use with timedelta
	if unit == 's':
		return timedelta(seconds=value)
	elif unit == 'm':
		return timedelta(minutes=value)
	elif unit == 'h':
		return timedelta(hours=value)
	elif unit == 'd':
		return timedelta(days=value)
	elif unit == 'w':
		return timedelta(weeks=value)
	else:
		raise Exception("unrecognized time unit")

def main(argv):
	#Arguments definition
	parser = argparse.ArgumentParser(description="Checks time lag in a Postgres replication cluster using repmgr")
	parser.add_argument('-H','--host', help="Hostname to connect to", default = None)
	parser.add_argument('-p','--port', help="Host port", default = None)
	parser.add_argument('-db','--dbname', help="Name of the database", default = None)
	parser.add_argument('-u','--dbuser', help="Database user", default = None)
	parser.add_argument('-P','--dbpass', help="Database user password", default = None)
	parser.add_argument('-C','--cluster', help="Name of the cluster", required=True)
	parser.add_argument('-n','--node', help="Number of the node", required=True)
	parser.add_argument('-w','--warning', help="Warning limit (supported units: s[econds], m[inutes], h[ours], d[ays] and w[eeks]. Seconds assumed if no unit is specified)", default = '0 s')
	parser.add_argument('-c','--critical', help="Critical limit (supported units: s[econds], m[inutes], h[ours], d[ays] and w[eeks]. Seconds assumed if no unit is specified)", default = '0 s')
	args = parser.parse_args()

	try:
		#Database connection
		conn = psycopg2.connect(host=args.host, port=args.port, database=args.dbname, user=args.dbuser, password=args.dbpass)
		cur = conn.cursor()
		cur.execute("SET search_path TO %s", ['repmgr_' + str(args.cluster)])
		cur.execute("SELECT replication_time_lag FROM repl_status WHERE standby_node = %s", [args.node])
		r = cur.fetchone()

		cur.close()
		conn.close()

		#Convert warning and critical user input into timedelta
		warning = get_seconds(arg_to_timedelta(args.warning))
		critical = get_seconds(arg_to_timedelta(args.critical))

		#Check if result is empty
		if cur.rowcount <= 0:
			raise Exception("Query didn't return a valid result for the specified cluster/node")
		else:
			value = get_seconds(r[0])

		#Preparing the performance data
		perfdata =  's|time_lag=' + str(value) + 's;' + str(warning) + ';' + str(critical)

	except Exception as ex:
		print 'REPMGR_LAG UNKNOWN: error: ' + str(ex)
                sys.exit(3)

	#We raise the right exit code for every case
	if value >= critical:
		print 'REPMGR_LAG CRITICAL: time_lag=' + str(value) + perfdata
		sys.exit(2)
	elif value >= warning:
		print 'REPMGR_LAG WARNING: time_lag=' + str(value) + perfdata
		sys.exit(1)
	else:
		print 'REPMGR_LAG OK: time_lag=' + str(value) + perfdata
		sys.exit(0)

if __name__=='__main__':
	main(sys.argv)
