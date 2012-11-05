#### THIS FILE MANAGED BY PUPPET ####
# Display all devices in nagios
import os
import splunk4nagios
os.system("/usr/bin/nc "+splunk4nagios.server+" 6557 < nagios-hosts")
#### THIS FILE MANAGED BY PUPPET ####
