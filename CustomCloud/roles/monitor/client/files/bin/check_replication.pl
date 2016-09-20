#!/usr/bin/env perl

# check_replication.pl
#
# Copyright 2ndQuadrant 2016, All rights reserved
# Author: Ian Barwick <ian.barwick@2ndquadrant.com>
#
# This script can perform following checks:
#
#  - check that all standbys are connected to their upstream server
#  - check standby replication lag (in seconds)
#  - check for stale replication slots
#
# Usage
#
#  Check that all standbys are connected to their upstream server:
#
#    check_replication.pl --check=connection \
#                         --standby xyz-server2,192.168.1.2 \
#                         --standby xyz-server3,192.168.1.3
#
#    (this runs on the primary/upstream server)
#
#  Check lag (in seconds) on a standby:
#
#    check_replication.pl --check=lag --warning 30 --critical 60 [ --peak_lag=$hour,$duration,$warning,$critical ]
#
#    `--peaklag` is to define a regular period when lag is expected to grow due
#    to bulk load operations, pg_dump runs etc.:
#      `$hour` is the hour (on the server's system) in which the peak starts;
#      `$duration` is the interval (in *minutes*) this lasts;
#      `$warning` and `$critical` are appropriate values (in *seconds*) to apply for this period
#
#    (this runs on the standby)
#
#  Check for stale (physical) slots on a primary/upstream server:
#
#    check_replication.pl --check=slot --warning=0 --critical=128
#
#    (warning/critical values represent the equivalent number of unconsumed WAL files
#    held back by the slot)

use strict;
use warnings;

use Data::Dumper;
use Getopt::Long;
use POSIX qw(strftime);

our @standbys;

our $check = undef;

our $psql_error = undef;

our %alert_options = (
    warn     => undef,
    crit     => undef,
    peak_lag => undef,
);

our %conn_options = (
    host     => undef,
    port     => '5432',
    username => 'postgres',
);

our %option_defs = (
    'check=s'      => \$check,
    'host=s'       => \$conn_options{'host'},
    'port=i'       => \$conn_options{'port'},
    'username=s'   => \$conn_options{'username'},
    'warning=i'    => \$alert_options{'warn'},
    'critical=i'   => \$alert_options{'crit'},
    'standby=s'    => \@standbys,
    'peak_lag=s'   => \$alert_options{'peak_lag'},
);

our %exit_codes = (
    'OK'       => 1,
    'WARNING'  => 2,
    'CRITICAL' => 3,
    'UNKNOWN'  => 4,
);

# For multiple checks, collate output by severity level
our %output = (
    1 => [], # OK
    2 => [],
    3 => [],
    4 => [],
);


GetOptions(%option_defs);

my %check_types = (
   'connection' => 1,
   'lag'        => 1,
   'slot'       => 1,
);

if (!defined($check) || !exists($check_types{$check})) {
    die qq|Provide option --check as one of 'connection', 'lag' or 'slot'\n|;
}

if($check eq 'connection') {
    do_check_connection();
}
elsif($check eq 'lag') {
    do_check_lag();
}
elsif($check eq 'slot') {
    do_check_slot();
}

# no other options possible


#---{ do_check_connection }---------------------------------------------

sub do_check_connection {
    if(!scalar @standbys) {
        die qq|Please provide at least one --standby parameter\n|;
    }

    my $min_exit_code_level = 1;

    foreach my $standby (@standbys) {
        my @standby_info = split(/,/, $standby);
        my $hostname_2ndq = shift @standby_info;
        my $client_addr = shift @standby_info;
        my $application_name = scalar @standby_info ? shift @standby_info : undef;

        my $connection_state = undef;
        my $exit_code_level = 1;

        my $sql = sprintf(
            q|SELECT state FROM pg_catalog.pg_stat_replication WHERE client_addr='%s'|,
            $client_addr,
        );

        if(defined($application_name)) {
            $sql = sprintf(
                q|%s AND application_name = '%s'|,
                $sql,
                $application_name,
            );
        }

        my $result = psql_exec($sql);

        if($psql_error) {
            # UNKNOWN - unable to connect
            $exit_code_level = 4;
            $connection_state = qq|unknown ("$result")|;
        }
        elsif(!length($result)) {
            # CRITICAL - no result for node found
            $exit_code_level = 3;
            # TODO - specify upstream
            $connection_state = 'not connected to upstream';
        }
        else {
            # We're expecting at least one of these four values:
            # (it's possible multiple entries in pg_stat_replication can
            #  exist for a standby, e.g. when pg_basebackup is running with
            # --xlog-method=stream)
            my %expected_states = (
                'startup'   => undef,
                'backup'    => undef,
                'catchup'   => undef,
                'streaming' => undef,
            );

            my @states = split(/\n/, $result);

            foreach my $state (@states) {
                # if "UNKNOWN" is returned, something really weird is going on and we
                # should raise an Icinga CRITICAL alert (not an unknown)
                if($state eq 'UNKNOWN') {
                    $exit_code_level = 3;
                    $connection_state = qq|replication state "${connection_state}" returned by system|;
                }
                # this should really never happen, unless a new state is introduced,
                # either way raise a CRITICAL alert so action can be taken
                elsif(!exists($expected_states{$state})) {
                    $exit_code_level = 3;
                    $connection_state = qq|unexpected replication state "${connection_state}" returned by system|;
                }
            }

            if($exit_code_level == 1) {
                $connection_state = join(', ', @states);
            }
        }

        if($exit_code_level > $min_exit_code_level) {
            $min_exit_code_level = $exit_code_level;
        }

        $connection_state = sprintf(
            q|%s: %s|,
            $hostname_2ndq,
            $connection_state,
        );

        push @{$output{$exit_code_level}}, $connection_state;
    }

    my $final_exit_code = undef;
    foreach my $exit_code(keys %exit_codes) {
        next unless $exit_codes{$exit_code} == $min_exit_code_level;

        $final_exit_code = $exit_code;
        last;
    }

    my @detail = ();
    foreach my $exit_code_level (reverse sort keys %output) {
        foreach my $outp (@{$output{$exit_code_level}}) {
            push @detail, $outp;
        }
    }

    return_status(
        'REPLICATION_CONN',
        $final_exit_code,
        join('; ', @detail),
    );
}


#---{ do_check_lag }----------------------------------------------------

sub do_check_lag {


    $alert_options{'warn'} //= 180;
    $alert_options{'crit'} //= 600;

    # Peak lag period defined - if we're in that period, adjust warning and
    # critical to those periods
    if(defined($alert_options{'peak_lag'})) {
        if($alert_options{'peak_lag'} !~ m|(\d+),(\d+),(\d+),(\d+)|) {
            die qq|Invalid setting for --peak_lag\n|;
        }

        my $start_hour = $1;
        my $duration_minutes = $2;
        my $peak_warn = $3;
        my $peak_crit = $4;

        my $start_minute = ($start_hour * 60);
        my $end_minute = $start_minute + $duration_minutes;

        # All settings and calculations based on local time, not UTC
        my $current_hour = strftime('%H', localtime);
        my $current_minute = strftime('%M', localtime);

        my $current_time = ($current_hour * 60) + $current_minute;

        # If the end of the peak lag period is after local midnight,
        # adjust start and end times so we can make a sensible comparison
        if($end_minute > 1440 && $current_hour < $start_hour) {
            $start_hour = 0;
            $end_minute -= 1440;
        }

        if($current_time >= $start_minute && $current_time <= $end_minute) {
            $alert_options{'warn'} = $peak_warn;
            $alert_options{'crit'} = $peak_crit;
        }
    }

    # sanity-check threshold parameters
    if($alert_options{'warn'} > $alert_options{'crit'}) {
        die sprintf(
            qq|Warning threshold is higher than critical threshold (%s vs %s)\n|,
            $alert_options{'warn'},
            $alert_options{'crit'},
        );
    }

    # If replay location is the same as receive location, then there's no lag
    # This assumes replication is working; if there's an issue with replication,
    # it should be caught by check on the master;
    # otherwise the lag is the difference between now and the last replayed transaction.
    # Note that checking only this difference will result in spurious lag if there's
    # no recent activity on the master.

    my $sql = <<EO_SQL;
SELECT CASE WHEN (pg_last_xlog_receive_location() = pg_last_xlog_replay_location())
        THEN 0
        ELSE EXTRACT(epoch FROM (clock_timestamp() - pg_last_xact_replay_timestamp()))::INT
       END
         AS lag_seconds
EO_SQL
    my $result = psql_exec($sql);

    # We assume the best result
    my $return_status = 'OK';

    my $details = undef;

    if($psql_error) {
        $return_status = 'UNKNOWN';
        $details = $result;
    }
    elsif(!length($result)) {
        $return_status = 'UNKNOWN';
        $details = q|No result returned for lag query - is this really a standby?|;
    }
    else {
        if($result >= $alert_options{'crit'}) {
            $return_status = 'CRITICAL';
        }
        elsif($result >= $alert_options{'warn'}) {
            $return_status = 'WARNING';
        }

        $details = sprintf(
            qq|lag=%is:%is:%is|,
            $result,
            $alert_options{'warn'},
            $alert_options{'crit'},
        );
    }

    return_status(
        'REPLICATION_LAG',
        $return_status,
        $details
    );
}


#---{ do_check_slot }---------------------------------------------------
#
# Stale slot alerts are calculated on the basis of the effective number
# of unconsumed WAL files the slot is holding back - this is easier to
# represent than a pure byte value

sub do_check_slot {
    # TODO: check reasonable default values
    $alert_options{'warn'} //= 16;

    # 64 WAL files = 1GB, which is the default `max_wal_size` in 9.5+
    $alert_options{'crit'} //= 64;

    if($alert_options{'warn'} > $alert_options{'crit'}) {
        die sprintf(
            qq|Warning threshold is higher than critical threshold (%s vs %s)\n|,
            $alert_options{'warn'},
            $alert_options{'crit'},
        );
    }

    # If a different WAL size is ever used, we'll need to update this
    # (or add a parameter)...
    my $wal_file_size = 1048576 * 16;

    my $min_exit_code_level = 1;

    my $sql = sprintf(
        <<EO_SQL,
SELECT slot_name, ((pg_catalog.pg_current_xlog_location() - restart_lsn) / %i)::INT AS slot_lag
  FROM pg_catalog.pg_replication_slots
 WHERE slot_type='physical'
   AND active IS FALSE
EO_SQL
        $wal_file_size,
    );

    my $result = psql_exec($sql);

    if($psql_error) {
        # UNKNOWN - unable to connect
        $min_exit_code_level = 4;
        push @{$output{$min_exit_code_level}}, qq|unknown ("$result")|;
    }
    elsif(!length($result)) {
        # OK - no inactive replication slots found
        push @{$output{$min_exit_code_level}}, 'no inactive replication slots found';
    }
    else {
        my @lines = split(/\n/, $result);

        foreach my $line (@lines) {
            next unless $line =~ m|^(\S+?)\s(\d+)$|;

            my $slot_name = $1;
            my $slot_lag = $2;

            my $exit_code_level = 1;

            if($slot_lag >= $alert_options{'crit'}) {
                $exit_code_level = 3;
            }
            elsif($slot_lag >= $alert_options{'warn'}) {
                $exit_code_level = 2;
            }

            if($exit_code_level > $min_exit_code_level) {
                $min_exit_code_level = $exit_code_level;
            }

            push @{$output{$exit_code_level}}, sprintf(
                q|%s: %i WAL segments stalled|,
                $slot_name,
                $slot_lag,
            );
        }
    }

    my $final_exit_code = undef;

    foreach my $exit_code(keys %exit_codes) {
        next unless $exit_codes{$exit_code} == $min_exit_code_level;

        $final_exit_code = $exit_code;
        last;
    }

    my @detail = ();
    foreach my $exit_code_level (reverse sort keys %output) {
        foreach my $outp (@{$output{$exit_code_level}}) {
            push @detail, $outp;
        }
    }

    return_status(
        'REPLICATION_SLOT',
        $final_exit_code,
        join('; ', @detail)
    );
}



#---{ psql_exec }-------------------------------------------------------

sub psql_exec {
    my $sql = shift;

    $psql_error = 0;
    my @connection_params = ();

    foreach my $param (keys %conn_options) {
        my $value = $conn_options{$param};
        next unless defined $value;

        push @connection_params, sprintf(
            q|--%s "%s"|,
            $param,
            $value,
        );
    }

    my $cmd = sprintf(
        q|psql -v ON_ERROR_STOP=1 --no-psqlrc -w -q -A -F " " -t %s -d postgres -c "%s" 2>&1|,
        join(' ', @connection_params),
        $sql,
    );

    my $result = `$cmd`;

    my $ret = $? >> 8;
    if($ret) {
        $psql_error = 1;
        my @lines = split(/\n/, $result);
        return shift @lines;
    }

    chomp $result;
    return $result;
}


#---{ return_status }---------------------------------------------------

sub return_status {
    my $check = shift;
    my $return_status = shift;
    my $info = shift;

    printf(
        qq|%s %s: %s\n|,
        $check,
        $return_status,
        $info,
    );
}
