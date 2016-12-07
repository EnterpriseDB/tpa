#!/usr/bin/env perl

# check_disk.pl
#
# Alternative for when nagios/icinga check_disk utility not available
#
# NOTE: not a full drop-in replacement for check_disk!

use strict;
use warnings;

#use Data::Dumper;
use Getopt::Long;

our %options = (
    warning  => '10%',
    critical => '5%',
    path     => undef,
);

our %option_defs = (
    'warning:s'  => \$options{'warning'},
    'critical:s' => \$options{'critical'},
    'path:s'     => \$options{'path'},
);

my %parsed_options = (
    'warning'  => undef,
    'critical' => undef,
);

our @output_fields = (
    'source',
    'fstype',
    'itotal',
    'iused',
    'iavail',
    'ipcent',
    'size',
    'used',
    'avail',
    'pcent',
    'target',
);

my $return_status = 'OK';

GetOptions(%option_defs);

# Sanity checks
# -------------

foreach my $pc_param ('warning','critical') {
    if($options{$pc_param} !~ m|^(\d+)\%|) {
        die(qq|--$pc_param must be percentage value\n|);
    }

    my $value = $1;
    if($value < 0 || $value > 100) {
        die(qq|--$pc_param must be percentage value between 0% and 100%\n|);
    }

    $parsed_options{$pc_param} = 100 - $value;
}

if($parsed_options{'warning'} >= $parsed_options{'critical'}) {
    die(qq|--warning must be higher than --critical\n|);
}

if(!defined($options{'path'})) {
    die(qq|--path required\n|);
}

if(!-e $options{'path'}) {
    die(qq|--path=$options{'path'} not found\n|);
}

my $cmd = sprintf(
    q|df -BM --output=%s %s|,
    join(',', @output_fields),
    $options{'path'},
);

my @res = `$cmd`;
shift @res;

#print join('', @res);

my @fields = split(/\s+/, $res[0]);

my %res = ();

my $ix = 0;

foreach my $field (@output_fields) {
    my $value = $fields[$ix];
    $value =~ s|\%$||;
    $res{$field} = $value;
    $ix++;
}


my $used_pcent = $res{'pcent'};

if($used_pcent > $parsed_options{'critical'}) {
    $return_status = 'CRITICAL';
}
elsif($used_pcent > $parsed_options{'warning'}) {
    $return_status = 'WARNING';
}

printf(
    qq{DISK %s - free space: %s %sB (%i%% inode=%i%%);| %s=%sB;\n},
    $return_status,
    $options{'path'},
    $res{'avail'},
    100 - $used_pcent,
    100 - $res{'ipcent'},
    $options{'path'},
    $res{'size'},
);

