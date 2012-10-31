#!/bin/bash
#### THIS FILE MANAGED BY PUPPET ####
echo "host_name,state,num,hostgroup"
/usr/bin/nc nagios-dev.noc.harvard.edu 6557 < nagios-hostgroupmembers |sed 's/,/\n/g'|sed 's/|/,/g'|while read line
do
COUNT=`echo $line|grep -c ","`

if [ $COUNT -eq 0 ]
 then
     SG=$line
 else
     echo $line","$SG
fi

done

#### THIS FILE MANAGED BY PUPPET ####
