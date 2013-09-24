# Display all devices in nagios
import os
os.system("/usr/bin/nc nagios1 6557 < nagios-hosts")
