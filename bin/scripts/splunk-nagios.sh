#!/bin/bash
#
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
#
# Author: Luke Harris <luke@verypowerful.info>
#
# Splunk to Nagios is Awesome.
# This script can be triggered from a Scheduled Saved Search in Splunk to send alerts to Nagios.
# 
# Pre-requisites:
# send_nsca must be installed on your *nix Splunk server
# nsca must be listening on your Nagios server 
# The Saved Search must begin with the corresponding hostname defined in Nagios followed by a hyphen then the Service defined in Nagios, eg. server01 - XYZ Alert
# Time range:
#  Start time (optional)  = -5m@m
#  Finish time (optional) = now
# Schedule and alert:
#  tick "Schedule this search"
# Schedule type = Basic
#  Run every = 5 minutes
# Alert conditions:
#  Perform actions = if number of events
#  is greater than 0 (if an alert is to be generated when a given event occurs)
#   or
#  is equal to 0 (if an alert is to be generated when a given event does not occur)
# Alert actions:
#  tick Trigger shell script
# Filename of shell script to execute = splunk-nagios.sh
# Note: must be located in $SPLUNK_HOME/etc/apps/SplunkForNagios/bin/scripts
# Change the following variables so that they are relevant to your environment:
#      * SPLUNKSERVER=splunk01 (ie. hostname of the splunk server)
#      * WWW=splunk (ie. url of splunk search head)
#      * NSCABIN=/usr/lib/nagios/plugins (ie. location of send_nsca on your splunk server)
#      * NSCACFG=$NSCABIN (ie. location of send_nsca.cfg on your splunk server)
#      * NSCAHOST=nagios.abc.com.au (ie. Fully Qualified Domain Name of your Nagios server)
#      * NSCAPORT=5667 (ie. port number of the nsca daemon on your Nagios server)
#
# version: 2011052201
#
SPLUNKSERVER=splunk01
WWW=splunk
NSCABIN=/usr/lib/nagios/plugins
NSCACFG=$NSCABIN
NSCAHOST=nagios.abc.com.au
NSCAPORT=5667
NSCA_SERVICE_NAME=`echo $5|awk -F'[' '{print $2}'|awk -F']' '{print $1}'|sed 's/\- //g'|cut -f2- -d " "`
HOST=`echo $5|awk -F'[' '{print $2}'|awk -F']' '{print $1}'|awk '{print $1}'|tr A-Z a-z`
EVENTS=$1
URL=`echo $6|sed "s/$SPLUNKSERVER/$WWW/"`

nagios_notify () {
${NSCABIN}/send_nsca -H $NSCAHOST -p $NSCAPORT -d "," -c $NSCACFG/send_nsca.cfg <<EOF
$HOST,$NSCA_SERVICE_NAME,$NSCA_CODE,$NSCA_MSG
EOF
}

if [ $EVENTS -gt 0 ]
 then
	NSCA_CODE=1
	ERROR=`zcat $8|sed -n '2p'`
	NSCA_MSG="$5 Error: $ERROR URL: $URL"
	nagios_notify
 else
	NSCA_CODE=1
	NSCA_MSG="$5 URL: $URL"
	nagios_notify
fi
