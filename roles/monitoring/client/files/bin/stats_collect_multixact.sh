#!/bin/bash

# Script to collect MultiXact statistics from pg_controldata and store
# it in a local table.
# The structure of such table should be this:
#
# CREATE TABLE stats_2ndq.controldata_multixact (
#        ts timestamp default  now() primary key,
#        txid                  int8 not null,
#        next_multixact_id     int8 not null,
#        next_multixact_offset int8 not null,
#        oldest_multixact_id   int8 not null,
#        oldest_multixact_db   int8 not null
# );
#
# Arguments for this script are:
#
# - Postgres binary directory (the postgres bindir)
# - PGDATA
# - database where the stats table is
# - sudo user, if it should sudo. It should normally be an OS user owner of the database directory, i.e.: postrges
#
# For example:
# ./stats_collect_multixact.sh -b /usr/lib/postgresql/bin -D  /var/lib/postgresql/9.3/main -d 2ndq -s postgres

# We don't want to have strange locale change the output of pg_controldata
unset LANG

# Set some default values, but don't trust them
PG_BIN=/usr/lib/postgresql/bin
PGDATA=/var/lib/postgresql/9.3/main
database=2ndq
sudo_user=""

#
# We start gathering variables passed by argument
#
while getopts ":hp:d:D:s:b:" optname
do
    case "$optname" in
        "d")
            database=${OPTARG}
            ;;
        "b")
            PG_BIN=${OPTARG}
            ;;
        "D")
            PGDATA=${OPTARG}
            ;;
        "s")
            sudo_user="sudo -u "${OPTARG}
            ;;
        "h")
            echo "./stats_collect_multixact.sh -d database -D PGDATA -b pg_bindir -s sudo_user"
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

# Let's gather the relevant information we want stored for stats
next_multixact_id=$($sudo_user $PG_BIN/pg_controldata $PGDATA | grep NextMultiXactId | cut -d":" -f2 |  sed -e 's/^ *//g;s/ *$//g')
next_multixact_offset=$($sudo_user $PG_BIN/pg_controldata $PGDATA | grep NextMultiOffset | cut -d":" -f2 |  sed -e 's/^ *//g;s/ *$//g')
oldest_multixact_id=$($sudo_user $PG_BIN/pg_controldata $PGDATA | grep oldestMultiXid | cut -d":" -f2 |  sed -e 's/^ *//g;s/ *$//g')
oldest_multixact_db=$($sudo_user $PG_BIN/pg_controldata $PGDATA | grep "oldestMulti's DB" | cut -d":" -f2 |  sed -e 's/^ *//g;s/ *$//g')

sql="INSERT INTO stats_2ndq.controldata_multixact VALUES (now(), txid_current(), $next_multixact_id, $next_multixact_offset, $oldest_multixact_id, $oldest_multixact_db)"

$sudo_user $PG_BIN/psql -d ${database} -c "${sql}"
