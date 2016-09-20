#!/usr/bin/env perl

# Wrapper script around barman which performs the "barman check"
# option with Nagios output for multiple servers and concatenates
# the output into a single service notification; the level code
# is set to the most severe and output ordered by severity.

use strict;
use warnings;


our %exit_codes = (
    'OK'       => 1,
    'WARNING'  => 2,
    'CRITICAL' => 3,
    'UNKNOWN'  => 4,
);

my @barman_servers = @ARGV;

# Collate output by severity level
my %output = (
    1 => [],
    2 => [],
    3 => [],
    4 => [],
);

my $min_exit_code_level = 1;

foreach my $server (@barman_servers) {
    my $barman_cmd = sprintf(
        q|barman check --nagios %s|,
        $server,
    );

    my $barman_result = `$barman_cmd`;

    next unless $barman_result =~ m|^BARMAN\s+(\w+) - (\w.*)$|;

    my $exit_code = $1;
    my $outp = $2;

    my $exit_code_level = $exit_codes{$exit_code};

    if($exit_code_level > $min_exit_code_level) {
        $min_exit_code_level = $exit_codes{$exit_code};
    }

    push @{$output{$exit_code_level}}, sprintf(
        q|[%s] %s|,
        $server,
        $outp,
    );
}

my $final_exit_code = undef;
foreach my $exit_code(keys %exit_codes) {
    next unless $exit_codes{$exit_code} == $min_exit_code_level;

    $final_exit_code = $exit_code;
    last;
}

my @outp;
foreach my $exit_code_level (reverse sort keys %output) {
    foreach my $outp (@{$output{$exit_code_level}}) {
        push @outp, $outp;
    }
}

printf(
    qq|BARMAN %s - %s\n|,
    $final_exit_code,
    join(' | ', @outp),
);
