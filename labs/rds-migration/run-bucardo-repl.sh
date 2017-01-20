#!/bin/sh
# example command used to set up the RDS instance:
# AWS_PROFILE=andrew aws rds create-db-instance --db-instance-identifier test-londiste-plpsql-triggers \
#        --db-instance-class db.t2.micro --engine postgres \
#        --master-username superad --master-user-password xxxxxxxxx --no-multi-az \
#        --allocated-storage 5 --region us-east-1 --db-subnet-group-name default-vpc-e1d87287 \
#        --publicly-accessible --vpc-security-group-ids sg-5322c72f


# the setup here is Postgres 9.5 running on RDS. The pseudo-superuser on RDS is
# "super2q". The replica is running locally on port 5532 Authentication is via
# password (.pgpass) on Amazon, and peer locally.

# we're going to replicate the new RDS database testlon into the local
# new database testrepl.

# Host machine is RHEL/Centos/Fedora with PGDG for postgres 9.5 installed

# set up the path and connection sets

export PATH=/usr/pgsql-9.5/bin:$PATH

RDSHOST=ohio-95.c40eqwi33pya.us-east-2.rds.amazonaws.com
RDSUSER=super2q
LOCALPORT=5532
LOCALDIR=/var/tmp/brepltest

# above should be all the config we need

# set up local and remote connection params

RDSCON="-h $RDSHOST -U $RDSUSER"
RDSDSN="host=$RDSHOST user=$RDSUSER"
LOCALCON="-h /tmp -p $LOCALPORT"
LOCALDSN="host=/tmp port=$LOCALPORT"

BCCONN="--dbport=$LOCALPORT --dbhost=/tmp"

RDSDB=testbucsrc
LOCALDB=testbucsink

# switch to run directory and make sure everything is clean

mkdir -p $LOCALDIR
cd $LOCALDIR

# clean up artefacts from old runs


# this section is brittle at best
if [ -e bucpid/bucardo.mcp.pid ]
then
	bucardo $BCCONN deactivate testsync 60
	# we have to wait until this drains
	while true
	do
		line=`bucardo $BCCONN status | grep testsync`
		test "$line" = "" && break
		case "$line" in
			*Good*) break ;;
			*Bad*) echo "Can't continue. manual Cleanup required" >&2; exit 1 ;;
			*) sleep 5 ;;
		esac
	done
	bucardo $BCCONN stop
fi	

rm -rf * .pgpass

# if STOP then we are done
test "$1" = STOP && exit

# not stopping - remove old databases and recreate
psql $RDSCON -c "drop database if exists $RDSDB" postgres
psql $RDSCON -c "create database $RDSDB" postgres
psql $LOCALCON -c "drop database if exists bucardo" postgres
psql $LOCALCON -c "drop database if exists $LOCALDB" postgres
psql $LOCALCON -c "create database $LOCALDB" postgres

# install standard bucardo package

if [ -e /etc/dnf ]
then
	DNF=dnf
else
	DNF=yum
fi

sudo $DNF -y install bucardo

# set up benchmark data on RDS
# make sure history has a PK so it can be replicated

pgbench $RDSCON -i --foreign-keys -s 10 $RDSDB
psql $RDSCON -c 'alter table pgbench_history add hid serial primary key' $RDSDB

# get a schema dump of the db:

pg_dump $RDSCON -s -n public -f bench-schema.sql $RDSDB

#  create the required role in the local db - ignore "already exists" error:

psql $LOCALCON -c "create role $RDSUSER" $LOCALDB || true

# copy in the schema:

psql $LOCALCON -f bench-schema.sql $LOCALDB


# NB: the local server MUSt be started with this setting, as the
# connections out of the database won't see this one
export PGPASSFILE=$LOCALDIR/.pgpass

grep $RDSUSER ~/.pgpass > $PGPASSFILE

BCPASS=`dd status=none if=/dev/urandom count=1  bs=24| base64`

echo "*:*:*:bucardo:$BCPASS" >> $PGPASSFILE
chmod og-rwx $PGPASSFILE
# export HOME=`pwd`


mkdir -p bucpid

psql $RDSCON -c "create user bucardo" postgres || true
psql $RDSCON -c "alter user bucardo password '$BCPASS'" postgres
psql $RDSCON -c "grant $RDSUSER to bucardo" postgres
psql $LOCALCON -c "create user bucardo" postgres || true
psql $LOCALCON -c "alter user bucardo password '$BCPASS'" postgres

{ echo P ; echo P; echo P; } | bucardo install $BCCONN --pid-dir=$LOCALDIR/bucpid

# helps us shut down cleanly
bucardo $BCCONN set bucardo_vac=0

bucardo $BCCONN show all || true

bucardo $BCCONN add db buc_master dbname=$RDSDB host=$RDSHOST

bucardo $BCCONN add db buc_slave  dbname=$LOCALDB host=/tmp port=$LOCALPORT  

bucardo $BCCONN add all tables db=buc_master
bucardo $BCCONN add all sequences db=buc_master


bucardo $BCCONN add relgroup benchset public.pgbench_accounts public.pgbench_branches public.pgbench_history public.pgbench_tellers public.pgbench_history_hid_seq

bucardo $BCCONN add sync testsync relgroup=benchset dbs=buc_master:source,buc_slave:target onetimecopy=2

mkdir -p bucardo_log

bucardo $BCCONN --log-destination=$LOCALDIR/bucardo_log start

# now do a pgbench run to generate some changes to be replicated

pgbench $RDSCON -c 8 -j 4 -T 20 $RDSDB
