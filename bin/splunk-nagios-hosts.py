# Display all devices in nagios
import os
os.system("/usr/bin/nc 127.0.0.1 6557 < nagios-hosts")
