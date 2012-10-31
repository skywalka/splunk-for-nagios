#!/bin/bash
echo "host_name,state,num,hostgroup"
/usr/bin/nc 127.0.0.1 6557 < nagios-hostgroupmembers |sed 's/,/\n/g'|sed 's/|/,/g'|while read line
do
COUNT=`echo $line|grep -c ","`

if [ $COUNT -eq 0 ]
 then
     HG=$line
 else
     echo $line","$HG
fi

done

