#!/usr/bin/perl -w

#  -------------------------------------------------------
#                   -=- <check_pgpool-II.pl> -=-
#  -------------------------------------------------------
#
#  Description : this plugin will check how many backends
#  are connected with PgPool-II and will check if their status
#  are "down"
#
#  Version : 0.1.1
#  -------------------------------------------------------
#  In :
#     - see the How to use section
#
#  Out :
#     - print on the standard output 
#
#  Features :
#     - perfdata output
#
#  Fix Me/Todo :
#     - catch connection errors
#     - too many things ;) but let me know what do you think about it
#
# ####################################################################

# ####################################################################
# GPL v3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ####################################################################

# ####################################################################
# How to use :
# ------------
#
#   - first you have to configure PgPool to accept PCP commands.
#   To do this, I recommand to follow this tutorial: 
#                   http://yoolink.to/jvG
#
#   - then display the help of this plugin to see how to use it
#       ./check_pgpool-II.pl --help
#
# ####################################################################

# ####################################################################
# Changelog :
# -----------
#
# --------------------------------------------------------------------
#   Date:18/03/2011   Version:0.1.1     Author:Erwan Ben Souiden
#   >> little update of the help
# --------------------------------------------------------------------
#   Date:10/03/2011   Version:0.1     Author:Erwan Ben Souiden
#   >> creation
# ####################################################################

# ####################################################################
#            Don't touch anything under this line!
#        You shall not pass - Gandalf is watching you
# ####################################################################

use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case);

# Generic variables
# -----------------
my $version = '0.1.1';
my $author = 'Erwan Labynocle Ben Souiden';
my $a_mail = 'erwan@aleikoum.net';
my $script_name = 'check_pgpool-II.pl';
my $verbose_value = 0;
my $version_value = 0;
my $more_value = 0;
my $help_value = 0;
my $perfdata_value = 0;
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# Plugin default variables
# ------------------------
my $display = 'CHECK_PGPOOL-II - ';
my ($critical,$warning,$timeout,$backends) = (2,1,10,0);
my ($pcp_directory,$pcp_host,$pcp_port,$pcp_user,$pcp_password) = ('','127.0.0.1','9898','admin','adminpassword');

Getopt::Long::Configure("no_ignore_case");
my $getoptret = GetOptions(
			'd|pcp-dir=s'		=> \$pcp_directory,
			'H|host=s'		    => \$pcp_host,
			'P|port=s'	    	=> \$pcp_port,
			'U|user=s'  		=> \$pcp_user,
			'W|password=s'		=> \$pcp_password,
			'w|warning=i'		=> \$warning,
			'c|critical=i'		=> \$critical,
			'b|backends=i'		=> \$backends,
			't|timeout=i'		=> \$timeout,
			'V|version' 		=> \$version_value,
			'h|help'     		=> \$help_value,
    		'D|display=s' 		=> \$display,
    		'p|perfdata' 		=> \$perfdata_value,
    		'v|verbose' 		=> \$verbose_value
);

print_usage() if ($help_value);
print_version() if ($version_value);

# Syntax check of your specified options
# --------------------------------------

print 'DEBUG: pcp_directory: '.$pcp_directory.'; pcp_host: '.$pcp_host.'; pcp_port: '.$pcp_port."\n" if ($verbose_value);
print 'DEBUG: pcp_user: '.$pcp_user.'; pcp_password: '.$pcp_password."\n" if ($verbose_value);

if (($pcp_directory eq "") or ($pcp_host eq "") or ($pcp_user eq "")) {
    print $display.'one or more following arguments are missing: pcp_directory/pcp_host/pcp_user'."\n";
    exit $ERRORS{"UNKNOWN"};
}

if ((! -e "$pcp_directory/pcp_node_count") or (! -e "$pcp_directory/pcp_node_info")) {
    print $display.' cannot find pcp_node_count or pcp_node_info in'."$pcp_directory\n";
    exit $ERRORS{"UNKNOWN"};
}

# Core script
# -----------
my $pcp_command_arg="$timeout $pcp_host $pcp_port $pcp_user $pcp_password";
my $pcp_command_node_count = "$pcp_directory/pcp_node_count $pcp_command_arg";
my $pcp_command_node_info = "$pcp_directory/pcp_node_info $pcp_command_arg";
my ($ok_count,$down_count) = (0,0);
my ($return,$node_return) = ('','');
my $plugstate = 'OK';

# how many nodes ?
my $node_count=`$pcp_command_node_count`;
chomp $node_count;
print 'DEBUG: node_count: '.$node_count."\n" if ($verbose_value);

# check node info
for (my $node_to_check = 0; $node_to_check < $node_count; $node_to_check++) {
	my @node_array = split(/ /, `$pcp_command_node_info $node_to_check`);
	print 'DEBUG: node ip: '.$node_array[0].'; node status: '.$node_array[2]."\n" if ($verbose_value);
	if ($node_array[2] == 3) {
		$down_count ++;
		$node_return .= " ($node_array[0],$node_array[2])";
	}
}

$return = $node_count.' backends detected';
$return .= ' and '.$backends.' waiting' if ($backends > $node_count);
$plugstate = 'WARNING' if ($down_count >= $warning);
$plugstate = 'CRITICAL' if (($down_count >= $critical) or ($backends > $node_count));
$return .= ' - nodes detected down '.$node_return if ($down_count >= $critical);
$return .= ' | down_nodes='.$down_count.' nodes_count='.$node_count if ($perfdata_value);
print $display.$plugstate.' - '.$return."\n";
exit $ERRORS{$plugstate};

# ####################################################################
# function 1 :  display the help
# ------------------------------
sub print_usage {
    print <<EOT;
$script_name version $version by $author
Usage : /<path-to>/$script_name -d /path/to/pcp-commands/ -H pgpool-II.hosttocheck.net -P 9898 -U username -W password [-p] [-D "$display"] [-v] [-c 2] [-w 1] [-t 10] [-b 0]
Options:
 -h, --help
    Print detailed help screen
 -V, --version
    Print version information
 -D, --display=STRING
    To modify the output display... 
    default is "CHECK_PGPOOL-II - "
 -p, --perfdata
    If you want to activate the perfdata output
 -v, --verbose
    Show details for command-line debugging (Nagios may truncate the output)
 -c, --critical=INT
    Specify a critical threshold of backend in down state
    default is 2
 -w, --warning=INT
    Specify a warning threshold of backend in down state
    default is 1
 -b, --backends=INT
    Specify the number of waiting backends
    default is 0
 -t, --timeout=INT
    Specify the connection timeout value in seconds. pcp command exits on timeout
    default is 10
 -d, --pcp-dir=STRING
    Specify the path to pcp commands binaries directory
    e.g. : /usr/local/pgpool-II/bin/
 -H, --host=STRING
    Specify the pgpool-II hostname 
 -p, --port=STRING
    Specify the PCP port
 -U, --user=STRING
    Specify the username for PCP authentication
 -W, --password=STRING
    Specify the password for PCP authentication
.................
  
Send email to $a_mail if you have questions
regarding use of this software. To submit patches or suggest improvements,
send email to $a_mail
This plugin has been created by $author
Hope you will enjoy it ;)
Remember :
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
EOT
    exit $ERRORS{"UNKNOWN"};
}

# function 2 :  display version information
# -----------------------------------------
sub print_version {
    print <<EOT;
$script_name version $version
EOT
    exit $ERRORS{"UNKNOWN"};
}
