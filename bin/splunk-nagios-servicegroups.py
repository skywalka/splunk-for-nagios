# Display all service groups in nagios
import os
os.system("/usr/bin/nc 10.20.14.114 6557 < nagios-servicegroups")
