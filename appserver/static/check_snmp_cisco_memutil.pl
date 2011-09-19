#!/usr/bin/perl
#
#
# AUTHORS:
#	Copyright (C) 2003-2011 Opsera Limited. All rights reserved
#
#    This file is part of Opsview
#
#    Opsview is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Opsview is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Opsview; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

use lib qw ( /usr/local/nagios/lib );
use Net::SNMP;
use Getopt::Std;

$script         = "check_snmp_cisco_memutil";
$script_version = "2.1.0";

$metric          = 1;
$oid_sysDescr    = ".1.3.6.1.2.1.1.1.0";
$oid_mem5minUsed = "1.3.6.1.4.1.9.9.48.1.1.1.5.1";
$oid_mem5minFree = "1.3.6.1.4.1.9.9.48.1.1.1.6.1";

$ipaddress    = "192.168.10.30";
$version      = "1";
$community    = "public";
$timeout      = 2;
$warning      = 90;
$critical     = 95;
$status       = 0;
$returnstring = "";

$configfilepath = "/usr/local/nagios/etc";

# Do we have enough information?
if ( @ARGV < 1 ) {
    print "Too few arguments\n";
    usage();
}

getopts("h:H:C:w:c:");
if ($opt_h) {
    usage();
    exit(0);
}
if ($opt_H) {
    $hostname = $opt_H;

    # print "Hostname $opt_H\n";
}
else {
    print "No hostname specified\n";
    usage();
}
if ($opt_C) {
    $community = $opt_C;

    # print "Using community $opt_C\n";
}
else {

    # print "Using community $community\n";
}
if ($opt_w) {
    $warning = $opt_w;

    # print "Warning threshold: $opt_w%\n";
}
if ($opt_c) {
    $critical = $opt_c;

    # print "Critical threshold: $opt_c%\n";
}

# Create the SNMP session
my ( $s, $e ) = Net::SNMP->session(
    -community => $community,
    -hostname  => $hostname,
    -version   => $version,
    -timeout   => $timeout,
);

main();

# Close the session
$s->close();

if ( $returnstring eq "" ) {
    $status = 3;
}

if ( $status == 0 ) {
    print "Status is OK - $returnstring\n";

    # print "$returnstring\n";
}
elsif ( $status == 1 ) {
    print "Status is a WARNING level - $returnstring\n";
}
elsif ( $status == 2 ) {
    print "Status is CRITICAL - $returnstring\n";
}
else {
    print "Status is UNKNOWN - $returnstring\n";
}

exit $status;

####################################################################
# This is where we gather data via SNMP and return results         #
####################################################################

sub main {

    if ( !defined( $s->get_request($oid_mem5minUsed) ) ) {
        if ( !defined( $s->get_request($oid_sysDescr) ) ) {
            $returnstring = "SNMP agent not responding";
            $status       = 3;
            return 3;
        }
        else {
            $returnstring = "SNMP OID does not exist";
            $status       = 1;
            return 1;
        }
    }
    foreach ( $s->var_bind_names() ) {
        $mem5minused = $s->var_bind_list()->{$_};
    }

    if ( !defined( $s->get_request($oid_mem5minFree) ) ) {
        if ( !defined( $s->get_request($oid_sysDescr) ) ) {
            $returnstring = "SNMP agent not responding";
            $status       = 3;
            return 3;
        }
        else {
            $returnstring = "SNMP OID does not exist";
            $status       = 1;
            return 1;
        }
    }
    foreach ( $s->var_bind_names() ) {
        $mem5minfree = $s->var_bind_list()->{$_};
    }

    $memtotal = $mem5minused + $mem5minfree;
    $mempcused = ( ( 100 / $memtotal ) * $mem5minused );

    $temp = sprintf 'MEMORY: total: %.2f MB, used: %.2f MB (%.0f%%), free: %.2f MB | MemTotal=%1$.2f ; MemUsed=%2$.2f ; MemFree=%4$.2f', ( $memtotal / 1000000 ), ( $mem5minused / 1000000 ), $mempcused, ( $mem5minfree / 1000000 );

    append($temp);

    if ( $mempcused >= $warning ) {
        $status = 1;
    }
    if ( $mempcused >= $critical ) {
        $status = 2;
    }
}

####################################################################
# help and usage information                                       #
####################################################################

sub usage {
    print << "USAGE";
--------------------------------------------------------------------	 
$script v$script_version

Memory utilisation on Cisco devices

Usage: $script -H <hostname> -c <community> [...]
Options: -H 		Hostname or IP address
                 -C 		Community (default is public)
                 -w 		Warning threshold (as %)
                 -c 		Critical threshold (as %)

--------------------------------------------------------------------	 
Copyright (C) 2003-2011 Opsera Limited. All rights reserved	 
	 
This program is free software; you can redistribute it or modify
it under the terms of the GNU General Public License
--------------------------------------------------------------------

USAGE
    exit 1;
}

####################################################################
# Appends string to existing $returnstring                         #
####################################################################

sub append {
    my $appendstring = @_[0];
    $returnstring = "$returnstring$appendstring";
}
