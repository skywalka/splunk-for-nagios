SplunkForNagios

Overview
   * SplunkForNagios has been developed to present events from the Open Source monitoring solution "Nagios" in Splunk, giving you the added ability to correlate problems in your environment and even trigger alerts from Splunk to Nagios. Over 40 field extractions are included with SplunkForNagios, as well as 6 saved searches, and an advanced dashboard featuring recent Warning and Critical Alerts.
   * This is version 1.0 of SplunkForNagios so any feedback, including requests for enhancement are most welcome. Email: luke AT verypowerful DOT info
   * This app has been created for the specifics of our Nagios environment, so it may or may not suit your specific purposes
   * Copyright (c) 2010 Luke Harris. All Rights Reserved.

Data Input
   * First, create an index called nagios then restart Splunk
   * Click Manager > Data inputs > Files & Directories > New
   * Set source: Monitor a file or directory
   * Full path on server: eg. /log/nagios/nagios.log
   * Set host: constant value
   * Host field value: eg. hostname.abc.com.au
   * Set sourcetype: Manual
   * Source type: nagios
   * Index: nagios
   * Click Save
 
Setup rsync cronjob
*/5 * * * * rsync -q -az --timeout=60 --bwlimit=500 hostname.abc.com.au:/opt/nagios/var/nagios.log /log/nagios/nagios.log

Splunk To Nagios
How to configure a Scheduled Saved Search in Splunk to send alerts to Nagios
   * Prerequisites:
      * send_nsca must be installed on the *nix Splunk server
      * nsca must be listening on the Nagios server 
   * The Saved Search must begin with the corresponding hostname defined in Nagios followed by a hyphen then the Service defined in Nagios, eg.
      * server01 - XYZ Alert
   * Time range:
      * Start time  = -5m@m
      * Finish time = now
   * Schedule and alert:
      * tick "Schedule this search"
   * Schedule type = Basic
      * Run every = 5 minutes
   * Alert conditions:
      * Perform actions = if number of events
         * is greater than 0 (if an alert is to be generated when a given event occurs)
            * or
         * is equal to 0 (if an alert is to be generated when a given event does not occur)
   * Alert actions:
      * tick Trigger shell script
   * Filename of shell script to execute = splunk-nagios.sh
      * Note: script is located in $SPLUNK_HOME/etc/apps/SplunkForNagios/bin/scripts

Nagios View
   * Warning Alerts - Last 60 Minutes
      * Number of Host & Service alerts with status Warning
   * Critical Alerts - Last 60 Minutes
      * Number of Host & Service alerts with status Critical
   * Warning and Critical Alerts
      * Top 5 Host & Service alerts with status Warning & Critical
   * Top 10 Service Notifications with status Warning
      * Chart of recent service notifications
   * Top 10 Service Notifications with status Critical
      * Chart of recent service notifications

Saved Searches
   * nagios - Host or Service Notifications - Last 60 minutes
   * nagios - Service Notifications with state Critical - Last 60 minutes
   * nagios - Host Down Notifications - Last 60 minutes
   * nagios - Number of Alerts - Last 60 minutes
   * nagios - Host or Service Alerts - Last 60 minutes
   * nagios - Scheduled Downtime by host and service - Last 24 Hours


