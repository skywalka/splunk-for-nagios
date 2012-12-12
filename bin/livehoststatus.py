# Script to set downtime for a host by accessing MK Livestatus
# Required fields to be passed to this script from Splunk: src_host, starttime, endtime, comment
import socket
import sys,splunk.Intersplunk
import string
import splunk4nagios

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                    try:
		        HOST = splunk4nagios.server    # The remote nagios server
		        PORT = 6557         # The remote port on the nagios server
		        content = [ "GET hosts\nFilter: host_name = ", (r["src_host"]), "\nColumns: name address alias hard_state\n" ]
    		        query = "".join(map(str,content))
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
			livehoststatus2 = data.strip()
			livehoststatus = livehoststatus2.split(";")
		        s.close()
                        r["src_host"] = livehoststatus[0]
                        r["src_ip"] = livehoststatus[1]
                        r["description"] = livehoststatus[2]
                        r["livehoststatus"] = livehoststatus[3]
                    except:
                        r["src_host"] = "Unknown"
                        r["src_ip"] = "Unknown"
                        r["description"] = "Unknown"
                        r["livehoststatus"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

