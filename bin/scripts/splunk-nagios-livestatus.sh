#!/bin/bash
SPLUNK_HOME=/opt/splunk
/usr/bin/nc 10.20.14.114 6557 < nagios-hosts > ../../lookups/nagios-hosts.csv
/usr/bin/nc 10.20.14.114 6557 < nagios-servicegroups > ../../lookups/nagios-servicegroups.csv
$SPLUNK_HOME/etc/apps/SplunkForNagios/bin/scripts/splunk-nagios-servicegroupmembers.sh > ../../lookups/nagios-servicegroupmembers.csv

