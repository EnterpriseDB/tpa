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
LOCALDIR=/var/tmp/repltest

# above should be all the config we need

# set up local and remote connection params

RDSCON="-h $RDSHOST -U $RDSUSER"
RDSDSN="host=$RDSHOST user=$RDSUSER"
LOCALCON="-h /tmp -p $LOCALPORT"
LOCALDSN="host=/tmp port=$LOCALPORT"

# switch to run directory and make sure everything is clean

mkdir -p $LOCALDIR
cd $LOCALDIR

# clean up artefacts from old runs

test -e pid/ticker.pid && pgqd -s ticker.ini
test -e pid/master.pid && londiste3 -s master.ini
test -e pid/slave.pid && londiste3 -s slave.ini
rm -rf *

# if STOP then we are done
test "$1" = STOP && exit

# not stopping - remove old databases and recreate
psql $RDSCON -c 'drop database if exists testlon' postgres
psql $RDSCON -c 'create database testlon' postgres
psql $LOCALCON -c 'drop database if exists testrepl' postgres
psql $LOCALCON -c 'create database testrepl' postgres

# clone the pgq git repo, make the pure plpgsql setup script

git clone https://github.com/pgq/pgq.git
pushd pgq
make plonly

# install triggers and other setup on rds:
# use unlogged tables for pgq

sed -i -e 's/CREATE TABLE/CREATE UNLOGGED TABLE/' pgq_pl_only.sql
psql $RDSCON -f pgq_pl_only.sql testlon

# create a plv8 version of this hot function that performs a whole
# lot better than the original

psql $RDSCON testlon <<'EOF'
	create extension plv8;
    create or replace function pgq._urlencode(val text)
	returns text as $$
        return val.replace(/[^-_.a-zA-Z0-9]/g, 
            function(c) {
               return '%' + c.charCodeAt(0).toString(16);
            }).replace(/%20/g,'+');
$$ language plv8 strict immutable;
EOF

popd

# install standard skytools package from PGDG:

if [ -e /etc/dnf ]
then
	DNF=dnf
else
	DNF=yum
fi

sudo $DNF -y install skytools-95

# set up benchmark data on RDS
# make sure history has a PK so it can be replicated

pgbench $RDSCON -i --foreign-keys -s 10 testlon
psql $RDSCON -c 'alter table pgbench_history add hid serial primary key' testlon

# get a schema dump of the db:

pg_dump $RDSCON -s -n public -f bench-schema.sql testlon

#  create the required role in the local db - ignore "already exists" error:

psql $LOCALCON -c "create role $RDSUSER" testrepl || true

# copy in the schema:

psql $LOCALCON -f bench-schema.sql testrepl

# set up the pgq ticker:

mkdir log
mkdir pid

cat > ticker.ini <<-EOF
	[pgqd]
	base_connstr = $RDSDSN connect_timeout=100
	database_list = testlon
	logfile = log/ticker.log
	pidfile = pid/ticker.pid
EOF

pgqd -d ticker.ini

# set up the londiste configs for master and slave, and set up the nodes,
# and start the worker

# Note we're overriding psycopg's connect-timeout default

cat > master.ini <<-EOF
	[londiste3]
	db = $RDSDSN dbname=testlon connect_timeout=100
	queue_name=testlon
	loop_delay = 5
	logfile = log/master.log
	pidfile = pid/master.pid
EOF

cat > slave.ini <<-EOF
	[londiste3]
	db = $LOCALDSN dbname=testrepl 
	queue_name=testlon
	loop_delay = 5
	logfile = log/slave.log
	pidfile = pid/slave.pid
EOF

londiste3 master.ini create-root master "$RDSDSN dbname=testlon"

londiste3 -d master.ini worker

londiste3 slave.ini create-branch slave "dbname=testrepl $LOCALDSN" --provider="$RDSDSN dbname=testlon connect_timeout=100"

londiste3 -d slave.ini worker

# add tables to be replicated on master

londiste3 master.ini add-table --all

# recreate the londiste triggers with explicit PK settings to avoid
# pointless catalog lookup in the trigger

# should have a function for doing this

psql -1 $RDSCON testlon <<'EOF'

    drop trigger _londiste_testlon on public.pgbench_accounts;
    drop trigger _londiste_testlon on public.pgbench_branches;
    drop trigger _londiste_testlon on public.pgbench_history;
    drop trigger _londiste_testlon on public.pgbench_tellers;
	create trigger _londiste_testlon AFTER INSERT OR DELETE OR UPDATE 
		   ON pgbench_accounts FOR EACH ROW EXECUTE PROCEDURE pgq.logutriga('testlon','pkey=aid');
	create trigger _londiste_testlon AFTER INSERT OR DELETE OR UPDATE 
		   ON pgbench_branches FOR EACH ROW EXECUTE PROCEDURE pgq.logutriga('testlon','pkey=bid');
	create trigger _londiste_testlon AFTER INSERT OR DELETE OR UPDATE 
		   ON pgbench_history FOR EACH ROW EXECUTE PROCEDURE pgq.logutriga('testlon','pkey=hid');
	create trigger _londiste_testlon AFTER INSERT OR DELETE OR UPDATE 
		   ON pgbench_tellers FOR EACH ROW EXECUTE PROCEDURE pgq.logutriga('testlon','pkey=tid');

EOF

# add all the tables on the slave

londiste3 slave.ini add-table --all

# now do a pgbench run to generate some changes to be replicated

pgbench $RDSCON -c 8 -j 4 -T 20 testlon
