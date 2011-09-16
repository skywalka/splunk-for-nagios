#!/bin/bash
SPLUNK_HOME=/opt/splunk
/usr/bin/nc 10.20.14.114 6558 < nagiosdev-hosts > ../../lookups/nagiosdev-hosts.csv
/usr/bin/nc 10.20.14.114 6558 < nagiosdev-servicegroups > ../../lookups/nagiosdev-servicegroups.csv
$SPLUNK_HOME/etc/apps/SplunkForNagios/bin/scripts/splunk-nagiosdev-servicegroupmembers.sh > ../../lookups/nagiosdev-servicegroupmembers.csv

