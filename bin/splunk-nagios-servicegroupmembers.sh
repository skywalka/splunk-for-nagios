#!/bin/bash
#### THIS FILE MANAGED BY PUPPET ####
echo "host_name,name,state,num,servicegroup"
/usr/bin/nc nagios-dev.noc.harvard.edu 6557 < nagios-servicegroupmembers |sed 's/,/\n/g'|sed 's/|/,/g'|while read line
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
