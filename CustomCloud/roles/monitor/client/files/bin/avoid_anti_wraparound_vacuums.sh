#!/bin/bash
# 2ndQuadrant avoid_anti_wraparound_vacuums script,
# Copyright 2ndQuadrant 2015, All rights reserved
# Author Martín Marqués <martin@2ndquadrant.com>

VERSION=2.1
echo "avoid_anti_wraparound_vacuums version $VERSION"

set -e -u

unset PGDATABASE PGHOST PGPORT PGUSER PGOPTIONS

function usage() {
    echo "
The avoid_anti_wraparound_vacuums.sh script searches for relations that are 
close to anti-wraparound vacuum freeze which will issue a full table scan
and freeze tuples of all pages from the relation, and VACUUM them with 
vacuum_freeze_table_age set to 0.

Running the script at hours when the server is not very busy will prevent 
autovacuum from running an anti-wraparound vacuum (which can't be cancel 
like normal autovacuum) at busy hours.

Default connection values are:

   - Host:         /tmp (where the postgres socket normally lives)
   - Port:         5432
   - User:         postgres
   - Freeze Bound: 80%

There are optional parameters that you can use to change the behaviour
(keep in mind that it's best to run it as a postgres superuser), which
we detail next.

  -H     Specify the host to which to connect. Defaults to local socket
         connections.

  -p     Specify a port different from the default 5432.

  -U     Specify a different user other then the postgres database user.

  -t     This option lets the user specify the maximun amount of time in  
         seconds that the script will run. This is important because we may 
         not want to have the script running outside the maintanence window 
         that we have set.
         This defaults to 3600 (1 hour).

  -S     This option sets an upper bound for relation size so we run the
         vacuum only on relations which are smaller than this amount of
         bytes.
         Size is in bytes and if not set, it will not filter on upper
         bound size (other filters may appear)

  -s     This option sets a lower bound for relation size so we run the
         vacuum only on relations which are larger than this amount of
         bytes.
         Size is in bytes and if not set, it will not filter on lower
         bound size (other filters may appear)

  -b     This is used to set the percentage which we will use to select
         relations to be vacuumed.
         The value should be between 1 and 99 (100 is equivalent to 10).
         Only relations that have relfrozenxid from relation or the toast
         of the relation higher then this porcentage will be vacuumed.
         If not specified, the defualt value to use is 80%

  -c     Use this to specify if there will be special vacuum parameters to
         be used in a configuration file. The file name must be specified 
         after.
         Example: -c aawv.conf

  -h     Show help (which is what you are reading now ;) ).


To invoke it you need to:
\"./avoid_anti_wraparound_vacuums.sh -H host -p port -U user -t timeout\"

Authentication
--------------

You will probably want to create a $HOME/.pgpass file containing a line like:

host:port:*:user:password

eg:

localhost:5432:*:postgres:thepassword

to avoid being prompted for a password every time this script invokes psql.
Set the file permissions to 0600 so that psql will read it:

    chmod 0600 $HOME/.pgpass

If you get the error:

    fe_sendauth: no password supplied

during connection test then psql isn't finding your .pgpass file, it isn't 
happy with its permissions, or can't find a password for the host and 
database you're using in the file.

"
    exit 0
}

function psql_wrap()
{
    DBNAME="postgres"
    
    if [ "${1:-}" = "-d" ]; then
        DBNAME=$2
        shift
        shift
    fi

    psql --no-psqlrc -w -v ON_ERROR_STOP=1 -h "$host" -p "$port" -U "$user" -d "$DBNAME" -q -A -F " " -t  "$@"
}

function verify_conf_file_sanity()
{
    if [ "$#" -ne 1 ]; then
	return 1
    fi
    grep_str=$1

    # We only check sanity when there's a configuration file passed, else there's
    # nothing to check as there's no file to send over
    if [ -n "${vacuum_configuration_file}" ]; then
	# Debugging variables
	if [ ${debugging} -gt 0 ]; then
	    echo "DEBUG: Running grep check on file ${vacuum_configuration_file} for string ${grep_str}"
	fi
	# Run the grep check to check sanity of the configuration file passed
	if [ `grep -E -v ${grep_str} ${vacuum_configuration_file} | wc -l` -gt 0 ]; then
	    return 1
	fi
    else
	# No configuration file means it's not sane as well. We return non-zero
	return 2
    fi
    return 0
}

function vacuum_freeze()
{
    # The epoch now
    epoch_now=`date '+%s'`
    # Time that has passed since the script started
    epoch_elapse=$((epoch_now - epoch_time))
    # Time left until the script must end due to timeout parameter
    # in miliseconds, so we multiply by 1000
    new_timeout=$(((totaltime - epoch_elapse) * 1000))

    if [ $((totaltime - epoch_elapse)) -le 0 ]; then
	# No more time to execute here, so returning a non zero value
	# so appropriate measures are taken outside the funtion.
	return 1;
    fi

    load_conf_file=""
    if verify_conf_file_sanity '(^SET|^--|^$)'; then
	load_conf_file="\i "${vacuum_configuration_file}
    fi

    echo "Avoiding anti-wraparound vacuum over relation $1"
    echo ""

    # Execute the VACUUM in verbose mode
    psql_wrap -d "$database" <<EOF
-- Load parameters from conf file
${load_conf_file}
SET statement_timeout TO '${new_timeout}';
SET vacuum_freeze_table_age TO 0;
VACUUM VERBOSE $1;
-- Lets sleep for half a second
SELECT pg_sleep(0.5);
EOF

    echo ""
    return 0;
}

function count_antiwraparound_relations()
{
    # Count how many relations are in the "close to antiwraparound" interval
    for count in $(psql_wrap -d "$database" <<EOF
RESET statement_timeout;
SELECT count(*) AS count
FROM (SELECT c.oid::regclass as table_name,
(current_setting('autovacuum_freeze_max_age')::integer - greatest(age(c.relfrozenxid),age(t.relfrozenxid))) as xid_left_to_antifreeze
FROM (pg_class c JOIN pg_namespace n ON (c.relnamespace=n.oid))
LEFT JOIN pg_class t ON c.reltoastrelid = t.oid
WHERE c.relkind = 'r' and greatest(age(c.relfrozenxid),age(t.relfrozenxid)) > current_setting('autovacuum_freeze_max_age')::integer * 0.${freeze_bound}
${RELATION_SIZE_FILTER}
) AS foo;
EOF
    )
    do
        echo "$count"
    done
}

function close_to_antiwraparound_relations()
{
    # We are looking for relations which have age of relfrozenxid at 90% or
    # more of autovacuum_freeze_max_age (which triggers the full table
    # scans).
    # We will only select tables larger than 1MB.
    for relation  in $(psql_wrap -d "$database" <<EOF
SELECT table_name
FROM (SELECT c.oid::regclass as table_name,
(current_setting('autovacuum_freeze_max_age')::integer - greatest(age(c.relfrozenxid),age(t.relfrozenxid))) as xid_left_to_antifreeze,
pg_relation_size(c.oid) as size
FROM (pg_class c JOIN pg_namespace n ON (c.relnamespace=n.oid))
LEFT JOIN pg_class t ON c.reltoastrelid = t.oid
WHERE c.relkind = 'r' and greatest(age(c.relfrozenxid), age(t.relfrozenxid)) > current_setting('autovacuum_freeze_max_age')::integer * 0.${freeze_bound} 
${RELATION_SIZE_FILTER}
ORDER BY 2 ASC) AS foo;
EOF
    )
    do
	echo "$relation";
    done
}

function avoid_anti_wraparound_vacuums(){
    
    relations_left=$(count_antiwraparound_relations)

    echo "Script is going to try to vacuum ${relations_left} relations."

    for r in $(close_to_antiwraparound_relations);do
	# vacuum with vacuum_freeze_table_age = 0 the table $r returned by  
	# the close_to_antiwraparound_relations function
	vacuum_freeze "${r}"
	# vacuum_freeze will return 1 if total execution time has been used,
	# in which case the script should end.
	if [ $? -ne 0 ]; then
            echo "Execution ended due to the fact that ${totaltime} seconds passed."
            relations_left=$(count_antiwraparound_relations)
            echo "There are still ${relations_left} relations to vacuum."
	    return 0;
	fi
    done

    epoch_now=`date '+%s'`
    echo "Finished in $((epoch_now - epoch_time)) seconds running VACUUM on tables close to anti-wraparound full scan."
    return 0;
}

# New debugging feature. Can take the values on and off for now.
debugging=0

# Self explaind parameters
host="/tmp"
port="5432"
user="postgres"

# Default total execution time in seconds
totaltime="3600"

# Threshold for size of relations. 0 means no limit.
relmaxsize=0

# We will use a default bound of 80% of autovacuum_freeze_max_age, but this
# can be over-written by using the -b option
freeze_bound=80

# If we don't pass a configuration file, we should just do nothing. As what
# we actually do is execute in psql what ever is in vacuum_configuration_file
# we should initialize it empty, so it does nothing if no configuration file
# was passed.
# By the way, we don't check that the file actually exists. That's the
# sysadmin's responsibility. Non existing file will not break the script.
vacuum_configuration_file=""

# We need the epoch from now
epoch_time=`date '+%s'`

# We want to show a message with the options passed
op_passed="Options passed: "
#
# We start gathering variables passed by argument
#
while getopts ":hH:p:U:t:S:s:b:c:" optname
do
    case "$optname" in
	"H")
	    host=${OPTARG}
	    op_passed=$op_passed"host -> $host, "
            ;;
	"p")
	    port=${OPTARG}
	    op_passed=$op_passed"port -> $port, "
            ;;
	"U")
	    user=${OPTARG}
	    op_passed=$op_passed"user -> $user, "
            ;;
	"t")
	    totaltime=${OPTARG}
	    op_passed=$op_passed"total time -> $totaltime, "
            ;;
	"S")
	    relmaxsize=${OPTARG}
	    op_passed=$op_passed"max rel size -> $relmaxsize, "
            ;;
	"s")
	    relminsize=${OPTARG}
	    op_passed=$op_passed"min rel size -> $relminsize, "
	    ;;
	"b")
	    freeze_bound=${OPTARG}
	    op_passed=$op_passed"freeze limit -> $freeze_bound, "
	    ;;
	"c")
	    vacuum_configuration_file=${OPTARG}
	    ;;
	"h")
	    usage
	    exit 0;
            ;;
	"?")
            echo "Unknown option $OPTARG"
	    exit 1
            ;;
	":")
            echo "No argument value for option $OPTARG"
	    exit 1
            ;;
	*)
	    # Should not occur
            echo "Unknown error while processing options"
	    exit 5
            ;;
    esac
done

echo
echo $op_passed | sed 's/,/\n               /g' | perl -ne 'chomp;print scalar reverse;' | cut -d',' -f 2- | perl -ne 'chomp;print scalar reverse;'
echo

echo -n "Testing connection..."
if ! psql_wrap -c "SELECT 1" > /dev/null 2>/tmp/$$.psqltest; then
	echo
	echo "Connection parameters invalid or missing ~/.pgpass file."
	echo "psql failed with:"
	echo "-------------"
	cat /tmp/$$.psqltest
	echo "-------------"
	echo "Run this script without parameters for more help"
	exit 1
fi
echo ' connection ok'
rm -f /tmp/$$.psqltest


# We initialize RELATION_SIZE_FILTER as an empty string, and then concatenate
# other filters related to relation size
RELATION_SIZE_FILTER=""

# If we set a relsize larger then 0, then we prepare the WHERE to append
# a lower bound based on size
if [ ! -z ${relminsize+xx} ]; then
    RELATION_SIZE_FILTER=$RELATION_SIZE_FILTER" AND pg_relation_size(c.oid::regclass) >= "$relminsize
fi

# We now check if $relmaxsize is set, and use if to build the upper bound filter
if [ ${relmaxsize} -ne 0 ]; then
    RELATION_SIZE_FILTER=$RELATION_SIZE_FILTER" AND pg_relation_size(c.oid::regclass) <= "$relmaxsize
fi

# The intention here is to do individual avoid_anti_wraparound_vacuums
# runs for each database of the cluster with one argument which is
# the total execution time.

# timeout will be the total time this script will run.
# For that reason we will have to reduce the value of ${timeout} in each 
# run of the for loop.

# Epoch time at start time
start_time=`date '+%s'`

for database in $(psql_wrap -d "postgres" -c "select datname from pg_database where datallowconn");do
    # The epoch now
    new_epoch=`date '+%s'`
    # Time that has passed since the script started, in seconds
    epoch_elapse=$((new_epoch - start_time))
    # Time left until the script must end due to timeout parameter
    # in miliseconds, so we multiply by 1000
    timeout=$((totaltime - epoch_elapse))

    echo "Running avoid_anti_wraparound_vacuums on database ${database}"

    avoid_anti_wraparound_vacuums 

    # if the avoid_anti_wraparound_vacuums function returns a non zero
    # value, we should end execution
    if [ $? -ne 0 ]; then
	echo "Ending due to expiration of timeout"
	exit 0;
    fi

    echo "======================================"
done
