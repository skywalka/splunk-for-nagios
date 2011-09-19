#!/usr/bin/perl -w
#
# check_iftraffic.pl - Nagios(r) network traffic monitor plugin
# Copyright (C) 2004 Gerd Mueller / Netways GmbH
# Changes make by Ektanoor on 2010
# $Id: check_iftraffic.pl 1119 2010-12-23 13:30:09Z ektanoor $
#
# mw = Markus Werner mw+nagios@wobcom.de
# Remarks (mw):
#
#	I adopted as much as possible the programming style of the origin code.
#
#	There should be a function to exit this programm,
#	instead of calling print and exit statements all over the place.
#
#
# minor changes by mw
# 	The snmp if_counters on net devices can have overflows.
#	I wrote this code to address this situation.
#	It has no automatic detection and which point the overflow
#	occurs but it will generate a warning state and you
#	can set the max value by calling this script with an additional
#	arg.
#
# minor cosmetic changes by mw
#	Sorry but I couldn't sustain to clean up some things.
#
# gj = Greg Frater gregATfraterfactory.com
# Remarks (gj):
# minor (gj):
# 
#	* fixed the performance data, formating was not to spec
# 	* Added a check of the interfaces status (up/down).
#	  If down the check returns a critical status.
# 	* Allow either textual or the numeric index value.
#	* If the interface speed is not specified on the command line
#	  it gets it automatically from IfSpeed
#	* Added option for second ifSpeed to allow for asymetrcal links
#	  such as a DSL line or cable modem where the download and upload
#	  speeds are different
#	* Added -B option to display results in bits/sec instead of Bytes/sec
#	* Added the current usage in Bytes/s (or bit/s) to the perfdata output
#	* Added ability for plugin to determine interface to query by matching IP 
#	  address of host with entry in ipAdEntIfIndex (.1.3.6.1.2.1.4.20.1.2) 
#	* Added -L flag to list entries found in the ipAdEntIfIndex table
#	Otherwise, it works as before.
#
#	2011/08/09 by mp
#	* Added -P option to check of port-channels. Does not support 10 Gig interfaces.
#	* Modified output by adding bandwidth for charting purposes.  Very useful for charting in Splunk.
#
# Ektanoor
#	Had to radically change several snippets of code to make calculations more consistent
#	Internally all is calculated on bits. This is the basic unit for traffic calculation, so it shall stay as such.
#	No internal calculations for dimensions. All megas, gigas and kilos are made only at the beginning and ending.
#	Had to turn SNMP to version 2 as we need 64-bit counters. The 32-bit overflow too fast and too frequently.
#	Changed the way to calculate overflow. The new one is more rational and solid.
#	All errors go to stop().
#	Final note: The new version works but it can be made a lot better. All I have done was to make it workable with fast speed interfaces.
#
#       4.1 - Several changes, most of them to fit better an ISP environment:
#       - bits per second are the default now. Use -B for bytes.
#       - RX, TX and absolute values show bytes/octets only.
#       - We now use Perl's given-where "switch" in some places. Look for the correct "use" for your version of perl.
#
#
# based on check_traffic from Adrian Wieczorek, <ads (at) irc.pila.pl>
#
# Send us bug reports, questions and comments about this plugin.
# Latest version of this software: http://www.nagiosexchange.org
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307

#For perl 5.12. We use it.
#use 5.012;
#For perl 5.10
#use feature qw(switch say);
#For older versions of perl
#use Switch;

use strict;

use Net::SNMP;
use Getopt::Long;
&Getopt::Long::config('bundling');

use Data::Dumper;

my $host_ip;
my $host_address;
my $iface_number;
my $iface_descr;
my $iface_speed;
my $iface_speedOut;
my $index_list;
my $opt_h;
my $units;
my $pcstate = "";
my $iface_pcspeed = 0;
my $iface_pctest = 0;
my $session;
my $error;
my $port         = 161;
my $snmp_version = 2;

my @snmpoids;

# SNMP OIDs for Traffic
my $snmpIfOperStatus 	= '1.3.6.1.2.1.2.2.1.8';
#Older 32-bit counter:
#my $snmpIfInOctets  	= '1.3.6.1.2.1.2.2.1.10';
my $snmpIfInOctets  	= '1.3.6.1.2.1.31.1.1.1.6';
#Older 32-bit counter:
#my $snmpIfOutOctets 	= '1.3.6.1.2.1.2.2.1.16';
my $snmpIfOutOctets 	= '1.3.6.1.2.1.31.1.1.1.10';
my $snmpIfDescr     	= '1.3.6.1.2.1.2.2.1.2';
my $snmpIfSpeed     	= '1.3.6.1.2.1.2.2.1.5';
my $snmpIPAdEntIfIndex 	= '1.3.6.1.2.1.4.20.1.2';

my $response;

# Path to  tmp files
my $TRAFFIC_FILE = "/tmp/traffic";

my %STATUS_CODE =
  ( 'UNKNOWN' => '3', 'OK' => '0', 'WARNING' => '1', 'CRITICAL' => '2' );

#default values;
my $state = "UNKNOWN";
my $if_status = '4';
my ( $in_bits, $out_bits ) = 0;
my $warn_usage = 85;
my $crit_usage = 98;
my $COMMUNITY  = "public";
my $output = "";
my $bytes = undef; 
my $suffix = "bps";
my $label = "Bytes";

my $max_value;
my $max_bits;

#Need to check this
my $use_reg    =  undef;  # Use Regexp for name

sub print_usage {
	print <<EOU;
    Usage: check_iftraffic3.pl -H host [ -C community_string ] [ -i if_index|if_descr ] [ -r ] [ -b if_max_speed_in | -I if_max_speed_in ] [ -O if_max_speed_out ] [ -P port_channel_speed ] [ -u ] [ -B ] [ -A IP Address ] [ -L ] [ -M ] [ -w warn ] [ -c crit ]

    Example 1: check_iftraffic3.pl -H host1 -C sneaky
    Example 2: check_iftraffic3.pl -H host1 -C sneaky -i "Intel Pro" -r -B  
    Example 3: check_iftraffic3.pl -H host1 -C sneaky -i 5
    Example 4: check_iftraffic3.pl -H host1 -C sneaky -i 5 -B -b 100 -u m 
    Example 5: check_iftraffic3.pl -H host1 -C sneaky -i 5 -B -b 20 -O 5 -u m 
    Example 6: check_iftraffic3.pl -H host1 -C sneaky -A 192.168.1.1 -B -b 100 -u m 
	Example 7: check_iftraffic3.pl -H host1 -C sneaky -i Port-channel50 -b 2 -u g -P 2000000000

    Options:

    -H, --host STRING or IPADDRESS
        Check interface on the indicated host.
    -B, --bytes
        Display results in Bytes per second B/s (default: bits/s)
    -C, --community STRING 
        SNMP Community (version 1 doesnt work!).
    -i, --interface STRING
        Interface Name
    -b, --bandwidth INTEGER
    -I, --inBandwidth INTEGER
        Interface maximum speed in kilo/mega/giga/bits per second.  Applied to 
        both IN and OUT if no second (-O) max speed is provided.
    -O, --outBandwidth INTEGER
        Interface maximum speed in kilo/mega/giga/bits per second.  Applied to
        OUT traffic.  Uses the same units value given for -b.
	-P,	--portchannel
		Checks if interface leaves Port-channel by compareing Port-channel speed to number.
		Enter Port-channel bandwidth total. Does not work with 10G interfaces.
    -r, --regexp
        Use regexp to match NAME in description OID
    -u, --units STRING
        g=gigabits/s,m=megabits/s,k=kilobits/s,b=bits/s.  Required if -b, -I, or 
    -O are used.
    -w, --warning INTEGER
        % of bandwidth usage necessary to result in warning status (default: 85%)
    -c, --critical INTEGER
        % of bandwidth usage necessary to result in critical status (default: 98%)
    -M, --max INTEGER
        Max Counter Value of net devices in kilo/mega/giga/bytes.
    -A, --address STRING (IP Address)
        IP Address to use when determining the interface index to use.  Can be 
        used when the index changes frequently or as in the case of Windows 
        servers the index is different depending on the NIC installed.
EOU

}

# Print results and exit script
sub stop {
 my $result = shift;
 my $exit_code = shift;
 print $result . "\n";
 exit ( $STATUS_CODE{$exit_code} );
};

sub bytes2bits {
 return unit2bytes(@_)*8;
};

#Converts an input value to value in bytes
sub unit2bytes {
 my ( $value, $unit ) = @_;
 #given ($unit) {
 # when ('G') { return $value*1073741824; }
 # when ('M') { return $value*1048576; }
 # when ('K') { return $value*1024; }
 # default { return $value }
 #};
 if ($unit eq 'G') {
   return $value*1073741824;
 } 
 elsif ($unit eq 'M') {
   return $value*1048576;
 }
 elsif ($unit eq 'K') {
   return $value*1024;
 }
 else { return $value }

};

sub unit2bits {
 my ( $value, $unit ) = @_;
 #given ($unit) {
 # when ('g') { return $value*1000000000; }
 # when ('m') { return $value*1000000; }
 # when ('k') { return $value*1000; }
 # default { return $value }
 #};
 if ($unit eq 'g') {
   return $value*1_000_000_000;
 }
 elsif ( $unit eq 'm' ) {
   return $value*1_000_000;
 }
 elsif ( $unit eq 'k' ) {
   return $value*1000
 } 
 else { return $value }

};

# Added 20100405 by gj
# Lookup hosts ip address
sub get_ip {
 use Net::DNS;

 my ( $host_name ) = @_;
 my $res = Net::DNS::Resolver->new;
 my $query = $res->search($host_name);

 if ($query) {
  foreach my $rr ($query->answer) {
   next unless $rr->type eq "A";
   return $rr->address;
  }
 } else {
  stop("Error: IP address not resolved\n","UNKNOWN");
 }
};

sub fetch_Ip2IfIndex {
 my $response;
 my $snmpkey;
 my $answer;
 my $key;

 my ( $session, $host ) = @_;

 # Determine if we have a host name or IP addr
 if ( $host !~ /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/ ) {
  $host = get_ip ( $host );
 };

 # Quit if results not found
 if ( !defined( $response = $session->get_table($snmpIPAdEntIfIndex) ) ) {
  $answer = $session->error;
  $session->close;
  stop("CRITICAL: SNMP error: $answer\n", "CRITICAL");
 };

 my %resp = %{$response};
 foreach $key ( keys %resp ) {
  # Check for ip address matching in returned index results
  if ( $key =~ /$host$/ ) {
   $snmpkey = $resp{$key};
  }
 }
 unless ( defined $snmpkey ) {
  $session->close;
  stop("CRITICAL: Could not match $host\n", "CRITICAL");
 }
 return $snmpkey;
};

sub fetch_ifdescr {
 my $response;
 my $snmpkey;
 my $answer;
 my $key;

 my ( $session, $ifdescr ) = @_;

 if ( !defined( $response = $session->get_table($snmpIfDescr) ) ) {
  $answer = $session->error;
  $session->close;
  stop("UNKNOWN: SNMP error: $answer\n", "UNKNOWN");
 };

 foreach $key ( keys %{$response} ) {

  # added 20070816 by oer: remove trailing 0 Byte for Windows :-(
  my $resp=$response->{$key};
  $resp =~ s/\x00//;

  my $test = defined($use_reg) ? $resp =~ /$ifdescr/ : $resp eq $ifdescr; 

  if ($test) {
   $key =~ /.*\.(\d+)$/;
   $snmpkey = $1;
  }
 }
 unless ( defined $snmpkey ) {
  $session->close;
  stop("CRITICAL: Could not match $ifdescr\n", "CRITICAL");
 }
 return $snmpkey;
};

sub format_volume {
 my $prefix_x="";
 my ($x)=@_;

 if ( $x>1000000000000000000 ) {
  $x=$x/1000000000000000000;
  $prefix_x="E";
 };
 if ( $x>1000000000000000 ) {
  $x=$x/1000000000000000;
  $prefix_x="P";
 };
 if ( $x>1000000000000 ) {
  $x=$x/1000000000000;
  $prefix_x="T";
 };
 if ( $x>1000000000 ) {
  $x=$x/1000000000;
  $prefix_x="G";
 };
 if ( $x>1000000 ) {
  $x=$x/1000000;
  $prefix_x="M";
 };
 if ( $x>1000 ) {
  $x=$x/1000;
  $prefix_x="K";
 };
 $x=sprintf("%.2f",$x);
 return $x.$prefix_x;
};

sub format_volume_bytes {
 my $prefix_x;
 my ($x)=@_;

 if ( $x>1152921504606846976 ) {
  $x=$x/1152921504606846976;
  $prefix_x="E";
 };
 if ( $x>1125899906842624 ) {
  $x=$x/1125899906842624;
  $prefix_x="P";
 };
 if ( $x>1099511627776 ) {
  $x=$x/1099511627776;
  $prefix_x="T";
 };
 if ( $x>1073741824 ) {
  $x=$x/1073741824;
  $prefix_x="G";
 };
 if ( $x>1048576 ) {
  $x=$x/1048576;
  $prefix_x="M";
 };
 if ( $x>1024 ) {
  $x=$x/1024;
  $prefix_x="K";
 };
 $x=sprintf("%.2f",$x);
 return $x.$prefix_x;
};


my $status = GetOptions(
 "A|address=s"   => \$host_ip,
 "B|Bytes"       => \$bytes,
 "b|bandwidth|I|inBandwidth=i" => \$iface_speed,
 "P|portchannel=i"  => \$iface_pcspeed,
 "C|community=s" => \$COMMUNITY,
 "c|critical=s"  => \$crit_usage,
 "H|hostname=s"  => \$host_address,
 "h|help"        => \$opt_h,
 "i|interface=s" => \$iface_descr,
 "M|max=i"       => \$max_value,
 "O|outBandwidth=i" => \$iface_speedOut,
 "p|port=i"      => \$port,
 "r|noregexp"    => \$use_reg,
 "u|units=s"     => \$units,
 "w|warning=s"   => \$warn_usage
);

# Check for missing options
if (!$host_address)  {
 print  "\nMissing host address!\n\n";
 stop(print_usage(),"UNKNOWN");
};
if (($iface_speed) and (!$units) ){
 print "\nMissing units!\n\n";
 stop(print_usage(),"UNKNOWN");
};
if (($units) and ((!$iface_speed) and  (!$iface_speedOut))) {
 print "\nMissing interface maximum speed!\n\n";
 stop(print_usage(),"UNKNOWN");
};
if (($iface_speedOut) and (!$units)) {
 print "\nMissing units for Out maximum speed!\n\n";
 stop(print_usage(),"UNKNOWN");
};
if (!$units) {
 $units="b";
};
if (($iface_speed) and ($bytes)) {
 $iface_speed = bytes2bits( $iface_speed, $units );
 if ( $iface_speedOut ) { $iface_speedOut = bytes2bits( $iface_speedOut, $units ); };
} elsif ($iface_speed) {
 $iface_speed = unit2bits( $iface_speed, $units );
 if ( $iface_speedOut ) { $iface_speedOut = unit2bits( $iface_speedOut, $units ); };
};


# If no -M Parameter was set, set it to 64Bit Overflow
if ( !$max_value ) {
  $max_bits = 18446744073709551616;
} else {
 if (!$bytes) {
  $max_bits = unit2bits( $max_value, $units );
 }
 else {
  $max_bits = bytes2bits( $max_value, $units );
 };
};


if ( $snmp_version =~ /[12]/ ) {
 ( $session, $error ) = Net::SNMP->session(
  -hostname  => $host_address,
  -community => $COMMUNITY,
  -port      => $port,
  -version   => $snmp_version
 );
 if ( !defined($session) ) {
  stop("UNKNOWN: $error","UNKNOWN");
 };
}
elsif ( $snmp_version =~ /3/ ) {
 $state = 'UNKNOWN';
 stop("$state: No support for SNMP v3 yet\n",$state);
}
else {
 $state = 'UNKNOWN';
 stop("$state: Unknown SNMP v$snmp_version\n",$state);
};


# Neither Interface Index nor Host IP address were specified 
if ( !$iface_descr ) {
 if ( !$host_ip ) {
 # try to resolve host name and find index from ip addr
 $iface_descr = fetch_Ip2IfIndex( $session, $host_address );
 } else {
  # Use ip addr to find index
  $iface_descr = fetch_Ip2IfIndex( $session, $host_ip );
 }
}

# Detect if a string description was given or a numberic interface index number 
if ( $iface_descr =~ /[^0123456789]+/ ) {
 $iface_number = fetch_ifdescr( $session, $iface_descr );
} else {
 $iface_number = $iface_descr;
}

push( @snmpoids, $snmpIfSpeed . "." . $iface_number );
push( @snmpoids, $snmpIfOperStatus . "." . $iface_number );
push( @snmpoids, $snmpIfInOctets . "." . $iface_number );
push( @snmpoids, $snmpIfOutOctets . "." . $iface_number );

if ( !defined( $response = $session->get_request(@snmpoids) ) ) {
 my $answer = $session->error;
 $session->close;
 stop("WARNING: SNMP error: $answer\n", "WARNING");
}

if ( !$iface_speed ) {
 $iface_speed = $response->{ $snmpIfSpeed . "." . $iface_number };
}

# Check if Out max speed was provided, use same if speed for both if not
if (!$iface_speedOut) {
 $iface_speedOut = $iface_speed;
}



$if_status = $response->{ $snmpIfOperStatus . "." . $iface_number };
$in_bits  = $response->{ $snmpIfInOctets . "." . $iface_number }*8;
$out_bits = $response->{ $snmpIfOutOctets . "." . $iface_number }*8;

#We retain the absolute values in bytes for RRD. It doesn't matter that the counter may overflow.
my $in_traffic_absolut=$response->{ $snmpIfInOctets . "." . $iface_number };
my $out_traffic_absolut=$response->{ $snmpIfOutOctets . "." . $iface_number };

$session->close;

my $update_time = time;
my $last_check_time = $update_time - 1;

if ( $if_status != 1 ) {
 stop("UNKNOWN: SNMP error: Interface $iface_descr is down!\n", "UNKNOWN");
};

my $row;
my $last_in_bits   = $in_bits;
my $last_out_bits  = $out_bits;

if ( open(FILE,"<".$TRAFFIC_FILE."_if".$iface_number."_".$host_address)) {
 while ( $row = <FILE> ) {
  ( $last_check_time, $last_in_bits, $last_out_bits ) = split( ":", $row );
  if (!$last_in_bits) { $last_in_bits=$in_bits;  }
  if (!$last_out_bits) { $last_out_bits=$out_bits; }
  if ($last_in_bits !~ m/\d/) { $last_in_bits=$in_bits; }
  if ($last_out_bits !~ m/\d/) { $last_out_bits=$out_bits; }
 }
 close(FILE);
}

if ( open(FILE,">".$TRAFFIC_FILE."_if".$iface_number."_".$host_address )) {
 printf FILE ("%s:%.0ld:%.0ld\n", $update_time, $in_bits, $out_bits );
 close(FILE);
};

my $in_traffic=0;
my $out_traffic=0;

if ( $in_bits < $last_in_bits ) {
  $in_bits = $in_bits + ($max_bits-$last_in_bits);
  $in_traffic = $in_bits/($update_time-$last_check_time);
} else { $in_traffic = ($in_bits-$last_in_bits)/($update_time-$last_check_time); };

if ( $out_bits < $last_out_bits ) {
  $out_bits = $out_bits + ($max_bits-$last_out_bits);
  $out_traffic = $out_bits/($update_time-$last_check_time);
} else { $out_traffic = ($out_bits-$last_out_bits)/($update_time-$last_check_time); };

# Calculate usage percentages
my $in_usage  = ($in_traffic*100)/$iface_speed;
my $out_usage = ($out_traffic*100)/$iface_speedOut;

if ($bytes) {
 # Convert output from bits to bytes
 $in_traffic = $in_traffic/8;
 $out_traffic = $out_traffic/8;
 $suffix = "Bs";
}
# Added 2011/08/09 mp
# Option -P Check Port-Channel speed to determine if all members are operational
# Compares user input speed to actual
if ( $iface_pcspeed != 0 ) { 
	$iface_pctest = $response->{ $snmpIfSpeed . "." . $iface_number };
	if ( $iface_pctest != $iface_pcspeed ) {
	$pcstate = "WARNING";
}
}

my $in=format_volume($in_traffic);
my $out=format_volume($out_traffic);

my $rx=format_volume_bytes($in_traffic_absolut);
my $tx=format_volume_bytes($out_traffic_absolut);

#Convert percentages to a more visual format
$in_usage  = sprintf("%.2f", $in_usage);
$out_usage = sprintf("%.2f", $out_usage);

#Output results of Port-Channel test with Warning
if ($pcstate eq "WARNING" ) {
	$state = "WARNING";
	$output = "Interface $iface_descr has a member interface down! ";
}

#Convert performance to a more visual format
$in_traffic  = sprintf("%.2f", $in_traffic);
$out_traffic = sprintf("%.2f", $out_traffic);

$output .= "Average IN: ".$in.$suffix." (".$in_usage."%), "
        ."Average OUT: ".$out.$suffix." (".$out_usage."%) ";
$output .= "Total RX: ".$rx.$label.", Total TX: ".$tx.$label;
$state = "OK";

if (($in_usage>$warn_usage) or ($out_usage>$warn_usage)) {
 $state = "WARNING";
}

if (($in_usage>$crit_usage) or ($out_usage>$crit_usage)) {
 $state = "CRITICAL";
}

$output = "$state - $output" if ( $state ne "OK" );

$output .=
"|inUsage=$in_usage%;$warn_usage;$crit_usage outUsage=$out_usage%;$warn_usage;$crit_usage"
  ." inBandwidth=".$in_traffic.$suffix." outBandwidth=".$out_traffic.$suffix 
  ." inAbsolut=$in_traffic_absolut outAbsolut=$out_traffic_absolut Bandwidth=$iface_speed";

stop($output, $state);

