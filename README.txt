Splunk for Nagios
=================

Overview
--------
   * Splunk for Nagios integrates the open source monitoring solution "Nagios" with Splunk
   * Features:
     * Schedule Saved Searches in Splunk to send alerts to Nagios
     * Status Dashboard featuring recent Warning and Critical Alerts and Notifications
     * Alerts Dashboard with an auto-populating drop-down list of device names to easily display relevant alert history
     * Host Dashboards with Graphs of metal level metrics (CPU, Memory, Swap, Load, Disk Usage, Network Interface Utilization, Processes, etc) sourced from Nagios Plugin Performance Data (Linux, AIX and Windows hosts supported)
     * NAS Dashboards with Graphs of Storage Usage, Quota Usage, SAVVOL Usage, Connections by Protocol, etc (EMC Isilon and Celerra supported)
     * Search Nagios alerts and notifications and trend problems over time
     * Over 40 field extractions, compliant with the Common Information Model
     * 6 Saved Searches
   * This is version 1.1.1 of SplunkForNagios so any feedback, including requests for enhancement are most welcome. Email: luke@verypowerful.info
   * This app has been created for the specifics of our Nagios environment, so it may or may not suit your specific purposes
   * Copyright (c) 2011 Luke Harris. All Rights Reserved.


Setup Splunk for Nagios
-----------------------
Add an Index to Splunk:
   * Create an index called nagios then restart Splunk
      * Note: all of the dashboards use searches based on index = nagios

Add new Data Inputs:
   * Note: Users who have upgraded from Splunk for Nagios v. 1.0 to v. 1.1.1 are required to add two additional data inputs (host-perfdata & service-perfdata)

Here are two methods to ingest the nagios log files from your Nagios server to your Splunk indexer (chose only one method):

1. Configure a 'Universal Forwarder' on the Nagios server
   * http://www.splunk.com/base/Documentation/latest/Deploy/Deployanixdfmanually
      * cd $SPLUNK_HOME/bin (eg. cd /opt/splunkforwarder/bin)
         * ./splunk start
         * ./splunk add forward-server splunk.abc.com.au:9997
         * Note: replace $NAGIOS_HOME with the relevant directory (eg. /opt/nagios)
            * ./splunk add monitor $NAGIOS_HOME/var/nagios.log -sourcetype nagios -hostname hostname.abc.com.au
            * ./splunk add monitor $NAGIOS_HOME/var/host-perfdata -sourcetype nagioshostperf -hostname hostname.abc.com.au
            * ./splunk add monitor $NAGIOS_HOME/var/service-perfdata -sourcetype nagiosserviceperf -hostname hostname.abc.com.au
      * edit $SPLUNK_HOME/etc/apps/search/local/inputs.conf on the Nagios server and add the following key/value pair:
         * index = nagios
      * restart the Splunk UF agent:
         * ./splunk restart

OR

2. Configure nagios log file ingestion using 'rsync' on the Splunk indexer

a/ nagios.log :-
   * Click Manager > Data inputs > Files & Directories > New
   * Specify the source: Continuously index data from a file or directory this Splunk instance can access
   * Full path to your data: eg. /log/nagios/nagios.log
   * Tick More settings
   * Set host: constant value
   * Host field value: eg. hostname.abc.com.au
   * Set the source type: Manual
   * Source type: nagios
   * Index: nagios
   * Click Save
 
b/ host-perfdata :-
   * Click Manager > Data inputs > Files & Directories > New
   * Specify the source: Continuously index data from a file or directory this Splunk instance can access
   * Full path to your data: eg. /log/nagios/host-perfdata
   * Tick More settings
   * Set host: constant value
   * Host field value: eg. hostname.abc.com.au
   * Set the source type: Manual
   * Source type: nagioshostperf
   * Index: nagios
   * Click Save
 
c/ service-perfdata :-
   * Click Manager > Data inputs > Files & Directories > New
   * Specify the source: Continuously index data from a file or directory this Splunk instance can access
   * Full path to your data: eg. /log/nagios/service-perfdata
   * Tick More settings
   * Set host: constant value
   * Host field value: eg. hostname.abc.com.au
   * Set the source type: Manual
   * Source type: nagiosserviceperf
   * Index: nagios
   * Click Save
 

Nagios Configuration (REQUIRED)
-------------------------------
1/ Update the following configuration options in $NAGIOS_HOME/etc/nagios.cfg

perfdata_timeout=5
process_performance_data=1
host_perfdata_command=nagios-process-host-perfdata
service_perfdata_command=nagios-process-service-perfdata
host_perfdata_file_mode=a
service_perfdata_file_mode=a
host_perfdata_file_processing_interval=86400
service_perfdata_file_processing_interval=86400
host_perfdata_file_processing_command=nagios-process-host-perfdata-file
service_perfdata_file_processing_command=nagios-process-service-perfdata-file

Reference:
http://nagios.sourceforge.net/docs/3_0/configmain.html


2/ Update the following configuration options in $NAGIOS_HOME/etc/objects/commands.cfg
Note: replace /opt/nagios with your $NAGIOS_HOME

# 'nagios-process-host-perfdata' command definition
define command{
        command_name    nagios-process-host-perfdata
        command_line    /usr/bin/printf "%b" "$TIMET$ src_host=\"$HOSTNAME$\" perfdata=\"HOSTPERFDATA\" hoststate=\"$HOSTSTATE$\" attempt=\"$HOSTATTEMPT$\" statetype=\"$HOSTSTATETYPE$\" executi ontime=\"$HOSTEXECUTIONTIME$\" reason=\"$HOSTOUTPUT$\" result=\"$HOSTPERFDATA$\"\n" >> /opt/nagios/var/host-perfdata
        }

# 'nagios-process-service-perfdata' command definition
define command{
        command_name    nagios-process-service-perfdata
        command_line    /usr/bin/printf "%b" "$TIMET$ src_host=\"$HOSTNAME$\" perfdata=\"SERVICEPERFDATA\" name=\"$SERVICEDESC$\" severity=\"$SERVICESTATE$\" attempt=\"$SERVICEATTEMPT$\" statet ype=\"$SERVICESTATETYPE$\" executiontime=\"$SERVICEEXECUTIONTIME$\" latency=\"$SERVICELATENCY$\" reason=\"$SERVICEOUTPUT$\" result=\"$SERVICEPERFDATA$\"\n" >> /opt/nagios/var/service-perfdata
        }

# 'nagios-process-host-perfdata-file' command definition
define command{
        command_name    nagios-process-host-perfdata-file
        command_line    /bin/cat /dev/null > /opt/nagios/var/host-perfdata
        }

# 'nagios-process-service-perfdata-file' command definition
define command{
        command_name    nagios-process-service-perfdata-file
        command_line    /bin/cat /dev/null > /opt/nagios/var/service-perfdata
        }

Reference:
http://nagios.sourceforge.net/docs/3_0/perfdata.html


3/ Update the following configuration options in $NAGIOS_HOME/etc/objects/templates.cfg
Note: ensure that the following variable is updated for BOTH host AND service templates :-
process_perf_data               1               ; Process performance data

Reference:
http://nagios.sourceforge.net/docs/3_0/objectdefinitions.html#host
http://nagios.sourceforge.net/docs/3_0/objectdefinitions.html#service


4/ Run the following command to check your Nagios configuration file for errors:
$NAGIOS_HOME/bin/nagios -v $NAGIOS_HOME/etc/nagios.cfg

5/ If everything is ok, you may issue the following command to reload Nagios:
/etc/init.d/nagios reload

Setup rsync cron jobs on the Splunk server
------------------------------------------
Note: replace /opt/nagios with your $NAGIOS_HOME
*/5 * * * * rsync -q -az --timeout=60 --bwlimit=500 hostname.abc.com.au:/opt/nagios/var/nagios.log /log/nagios/nagios.log
*/5 * * * * rsync -q -az --timeout=60 --bwlimit=500 hostname.abc.com.au:/opt/nagios/var/host-perfdata /log/nagios/host-perfdata
*/5 * * * * rsync -q -az --timeout=60 --bwlimit=500 hostname.abc.com.au:/opt/nagios/var/service-perfdata /log/nagios/service-perfdata


Nagios Plugins supported by Splunk for Nagios
---------------------------------------------
   * All Official Nagios Plugins: http://www.nagios.org/download/plugins/
   * Check EMC Isilon: http://exchange.nagios.org/directory/Plugins/Hardware/Storage-Systems/SAN-and-NAS/Check-EMC-Isilon/details
   * Check EMC Celerra: http://exchange.nagios.org/directory/Plugins/Hardware/Storage-Systems/SAN-and-NAS/Check-EMC-Celerra/details
   * Check CPU Performance: http://exchange.nagios.org/directory/Plugins/System-Metrics/CPU-Usage-and-Load/Check-CPU-Performance/details
   * check_mem.pl: http://exchange.nagios.org/directory/Plugins/System-Metrics/Memory/check_mem-2Epl/details
   * check_iftraffic_nrpe: http://exchange.nagios.org/directory/Uncategorized/check_iftraffic_nrpe/details
      * Note: check_iftraffic_nrpe requires a patch to work with Splunk for Nagios :-
         1/ Download the script from the url above
         2/ Convert the script from dos format to *nix:
            # dos2unix check_iftraffic_nrpe.pl
         3/ Apply the patch which is located at $SPLUNK_HOME/etc/apps/SplunkForNagios/appserver/static/check_iftraffic_nrpe.pl.patch
            # patch < check_iftraffic_nrpe.pl.patch


How To Send Alerts From Splunk to Nagios
----------------------------------------
Configure a Scheduled Saved Search in Splunk to send alerts to Nagios:
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


Edit the script located at $SPLUNK_HOME/etc/apps/SplunkForNagios/bin/scripts/splunk-nagios.sh 
and change the following variables so that they are relevant to your environment:
      * SPLUNKSERVER=splunk01 (ie. hostname of the splunk server)
      * WWW=splunk (ie. url of splunk search head)
      * NSCABIN=/usr/lib/nagios/plugins (ie. location of send_nsca on your splunk server)
      * NSCACFG=$NSCABIN (ie. location of send_nsca.cfg on your splunk server)
      * NSCAHOST=nagios.abc.com.au (ie. Fully Qualified Domain Name of your Nagios server)
      * NSCAPORT=5667 (ie. port number of the nsca daemon on your Nagios server)


Common Information Model compliant fields:
------------------------------------------
src_host = Hostname of Nagios Client (tranforms existing fields: hostalert hostcurrent hostexternal hostpassive hostnotification hostservicestate)
severity = Nagios Alert Severity, eg. OK, WARNING, CRITICAL, UNKNOWN (tranforms existing fields: status servicestatus statusnotification)
reason = Nagios Alert Message (tranforms existing fields: statusinfoexternal statusinfo notificationinfo passiveserviceinfo hostcurrentinfo servicestateinfo hostinfo hostnotificationinfo)
name = Nagios Plugin Name (tranforms existing fields: servicealertname servicepassivename serviceexternal servicenamenotification servicestatename downtimeservicename hoststatus)
user_id = User id of Nagios User receiving a host or service notification (tranforms existing field: username)

Saved Searches
--------------
   * nagios - Host or Service Notifications - Last 60 minutes
   * nagios - Service Notifications with state Critical - Last 60 minutes
   * nagios - Host Down Notifications - Last 60 minutes
   * nagios - Number of Alerts - Last 60 minutes
   * nagios - Host or Service Alerts - Last 60 minutes
   * nagios - Scheduled Downtime by host and service - Last 24 Hours

Status Dashboard
------------------
   * Warning Alerts - Last 60 Minutes
      * Displays the number of Host & Service alerts with a severity of Warning
   * Critical Alerts - Last 60 Minutes
      * Displays the number of Host & Service alerts with a severity of Critical
   * Warning and Critical Alerts
      * Displays the top 5 Host & Service alerts with a severity of Warning & Critical
   * Top 10 Service Notifications with a severity of Warning
      * Displays a chart of recent service notifications
   * Top 10 Service Notifications with a severity of Critical
      * Displays a chart of recent service notifications

Alerts Dashboard
----------------------
   * Featuring an auto-populating drop-down list of device names to easily display relevant alert history
      * Note: the drop-down list is auto-populated by a hidden search that extracts the src_host field from the nagios log that contains nagiosevent="CURRENT HOST STATE" - generated by default by Nagios at midnight every day.

Performance Dashboards
----------------------
Note: these graphs have been optimized for a 24 hour time span. If you require a longer time window, please update the span value accordingly.

Host specific dashboards:
   * Featuring an auto-populating drop-down list of device names to easily display relevant alerts, notifications and performance graphs:
   * Note: the drop-down list is auto-populated by a hidden search that extracts the src_host field from the nagios log that contains nagiosevent="CURRENT HOST STATE" - generated by default for all devices in Nagios at midnight every day.
      * Nagios AIX Performance Graphs
      * Nagios Linux Performance Graphs
      * Nagios *nix Filesystem Usage Graphs
      * Nagios Windows Performance Graphs

NAS specific dashboards:
   * Featuring a search box to enter the relevant hostname of your NAS device to easily display relevant alerts, notifications and performance graphs:
      * Nagios Isilon Performance Graphs
      * Nagios Celerra Performance Graphs

Disclaimer
----------
   * This app has been created for the specifics of our Nagios environment (Nagios Core version 3.2.1) and it may or may not suit your specific purposes.

License
-------
   * GNU GENERAL PUBLIC LICENSE Version 3

v1.1.1
------
 - added 2 NAS Dashboards with Graphs of Storage Usage, Quota Usage, SAVVOL Usage, Connections by Protocol, etc (EMC Isilon and Celerra)

v1.1
----
 - added 4 all new Powerful Views with Graphs of metal level metrics sourced from Nagios Plugin Performance Data
 - added Nagios Alerts Form Search with an auto-populating drop-down list of all device names to easily display relevant alert history
 - added 5 all new field extractions for CIM compliance: http://www.splunk.com/base/Documentation/latest/Knowledge/UnderstandandusetheCommonInformationModel

v1.0
----
 - initial release

