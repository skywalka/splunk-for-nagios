#!/usr/bin/perl -w
# nagios: -epn
use Getopt::Std;
use Net::SNMP qw(:snmp);
#    ---------------------------------------------------------------------------
#    8/17/2011 by Mike Pagano
#    Added ability to choose between MGCP and H323 Gateways.
#    MGCP is default.
#    ---------------------------------------------------------------------------
#    CCME PSTN statistics - in/out/total calls per minute  on PRI/BRI interfaces
#    Copyright 2010 Lionel Cottin (cottin@free.fr)
#    ---------------------------------------------------------------------------
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    ---------------------------------------------------------------------------
#
my $version = "0.2";
my $release = "2011/08/17";

#
# Interesting MIB entries
# -----------------------
my $chCount    = ".1.3.6.1.2.1.10.20.1.3.2.1.6"; # base OID for channel count
my $bChannels  = ".1.3.6.1.4.1.9.10.19.1.1.3";   # base OID for b-channels in use

#-------------------------------------------------------------------------------
#    Global variable declarations
#-------------------------------------------------------------------------------
my @str = ("OK", "WARNING", "CRITICAL", "UNKNOWN"); # Nagios status strings
my (
   $usage,              # Help message
   $hostname,           # Target router
   $community,          # SNMP community (v2c only)
   $gateway,		# MGCP or H323 Gateway
   $base_oid,           # Base OID
   $short,              # Message for $SERVICEOUTPUT$
   $result,             # Temp variable to store SNMP results
   @oids,
   $warn,
   $crit
);

my $total = 0;
my $used  = 0;

#-------------------------------------------------------------------------------
#    Global variable initializations
#-------------------------------------------------------------------------------
$usage = <<"EOF";
usage:  $0 [-h] -H <hostname> -C <community> -g <gateway type> -w <warning> -c <critical>

Version: $version
Released on: $release

Nagios plugin to monitor PRI/BRI B-Channel usage on Cisco gateways

[-h]                  : Print this message
[-H] <hostname>       : IP Address or Hostname
[-C] <community>      : SNMP Community String  (default = "public")
[-g] <gateway type>   : Use h for H323 gateway (default = MGCP)
[-w] <free channels>  : Below this number, raise a Warning status
[-c] <free channels>  : Below this number, raise a Critical status
[-d]                  : enable debug output
 
EOF

#-------------------------------------------------------------------------------
#                              Input Phase
#-------------------------------------------------------------------------------
die $usage if (!getopts('hH:C:g:w:c:d') || $opt_h);
die $usage if (!$opt_H || !$opt_C || !$opt_c || !$opt_w || $opt_h);
$hostname = $opt_H;
$community = $opt_C || "public"; undef $opt_C; #use twice to remove Perl warning
$gateway = $opt_g || "MGCP"; undef $opt_g;
$warn = $opt_w;
$crit = $opt_c;

#-------------------------------------------------------------------------------
# Check if -g option was used to change from MGCP to H323
#-------------------------------------------------------------------------------
if	($gateway eq "h") {
	$bChannels  = ".1.3.6.1.4.1.9.10.19.1.1.4";   # H323 OID for b-channels in use
	$gateway = "H323"
	} else {
	$gateway = "MGCP"
	}

if($opt_d) {
  print "Target hostname  : $hostname\n";
  print "SNMPv2 community : $community\n";
  print "SNMP MIB         : $bChannels\n";
  print "Gateway type     : $gateway\n";
  print "Warning level    : $warn free channels\n";
  print "Critical level   : $crit free channels\n";
}

#-------------------------------------------------------------------------------
# Open an SNMPv2 session with the remote agent
#-------------------------------------------------------------------------------
my ($session, $error) = Net::SNMP->session(
        -version     => 'snmpv2c',
        -nonblocking => 1,
        -timeout     => 2,
        -hostname    => $hostname,
        -community   => $community
);

if (!defined($session)) {
  printf("ERROR: %s.\n", $error);
  exit (-1);
}

#-------------------------------------------------------------------------------
# Retrieve chCount
#-------------------------------------------------------------------------------
$base_oid = $chCount;
$result = $session->get_bulk_request(
        -callback       => [\&cb_bulk, {}],
        -maxrepetitions => 20,
        -varbindlist => [$base_oid]
);
if (!defined($result)) {
  printf("ERROR: %s.\n", $session->error);
  $session->close;
  exit (-1);
}
snmp_dispatcher();
undef $result;

#-------------------------------------------------------------------------------
# Retrieve bChannels
#-------------------------------------------------------------------------------
$base_oid = $bChannels;
$result = $session->get_bulk_request(
        -callback       => [\&cb_bulk, {}],
        -maxrepetitions => 20,
        -varbindlist => [$base_oid]
);
if (!defined($result)) {
  printf("ERROR: %s.\n", $session->error);
  $session->close;
  exit (-1);
}
snmp_dispatcher();
undef $result;

#-------------------------------------------------------------------------------
# Process results
#-------------------------------------------------------------------------------
my $state = 0;
my $free = $total - $used;
if ( $free <= $warn ) { $state = 1 };
if ( $free <= $crit ) { $state = 2 };
if ( $total == 0    ) { $state = 3 };
$short = "B-Channels: ($used in use / $free free / $total in total) ";
$perf = "total=$total used=$used";
$short = $short . ": $str[$state]";
print "$short | $perf\n";
exit $state;

#-------------------------------------------------------------------------------
# Subroutines
#-------------------------------------------------------------------------------
sub cb_bulk
{
  my ($session, $table) = @_;
  if (!defined($session->var_bind_list)) {
    printf("ERROR: %s\n", $session->error);
    exit 3;
  } else {
    #---------------------------------------------------------------
    # Loop through each of the OIDs in the response and assign
    # the key/value pairs to the anonymous hash that is passed
    # to the callback.  Make sure that we are still in the table
    # before assigning the key/values.
    #---------------------------------------------------------------
    my $next;
    foreach my $oid (oid_lex_sort(keys(%{$session->var_bind_list}))) {
      if (!oid_base_match($base_oid, $oid)) {
        $next = undef;
        last;   
      }      
      $next = $oid;
      $table->{$oid} = $session->var_bind_list->{$oid};
    } 
    #---------------------------------------------------------------
    # If $next is defined we need to send another request
    # to get more of the table.
    #---------------------------------------------------------------
    if (defined($next)) {
      $result = $session->get_bulk_request(
                -callback       => [\&get_bulk, $table],
                -maxrepetitions => 20,
                -varbindlist    => [$next]
                );
      if (!defined($result)) {
        printf("ERROR: %s\n", $session->error);
        exit -1;
      } 
    } else {
      #-------------------------------------------------------
      # We are no longer in the table, so print the results.
      #-------------------------------------------------------
      foreach my $oid (oid_lex_sort(keys(%{$table}))) {
        #-----------------------------------------------
        # Handle result from chCount walk
        #-----------------------------------------------
        if ($oid =~ /^$chCount.(\d+)$/) {
          my $index = $1;
          print "chCount $1: $table->{$oid}\n" if $opt_d;
          $total = $total + $table->{$oid};
        #-----------------------------------------------
        # Handle result from bChannels walk
        #-----------------------------------------------
        } elsif ($oid =~ /^$bChannels.(\d+)$/) {
          my $index = $1;
          print "inUse $1: $table->{$oid}\n" if $opt_d;
          $used = $used + $table->{$oid};
        }
      }
    }
  }
}
