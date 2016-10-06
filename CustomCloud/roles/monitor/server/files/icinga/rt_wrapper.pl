#!/usr/bin/perl

use strict;
use warnings;

if((exists $ENV{SERVICENOTIFICATIONNUMBER} and $ENV{SERVICENOTIFICATIONNUMBER} == 0)
	or (exists $ENV{HOSTNOTIFICATIONNUMBER} and $ENV{HOSTNOTIFICATIONNUMBER} == 0)) {
	exit 0;
} else {
	exec("/opt/rt4/bin/rt", @ARGV);
}
