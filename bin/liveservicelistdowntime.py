# Script to list service problems in downtime by accessing MK Livestatus
# Required fields to be passed to this script from Splunk: src_host, name
import socket
import sys,splunk.Intersplunk
import string

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                if "name" in r:
                    try:
		        HOST = 'nagios1'    # The remote nagios server
		        PORT = 6557              # The remote port on the nagios server
		        content = [ "GET services\nFilter: host_name = ", (r["src_host"]), "\nFilter: service_description = ", (r["name"]), "\nAnd: 2\nColumns: host_name service_description state scheduled_downtime_depth host_scheduled_downtime_depth\n" ]
    		        query = "".join(content)
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
			liveservicelistdowntime2 = data.strip()
			liveservicelistdowntime = liveservicelistdowntime2.split(";")
			s.close()
                        r["src_host"] = liveservicelistdowntime[0]
                        r["name"] = liveservicelistdowntime[1]
                        r["liveservicestate"] = liveservicelistdowntime[2]
                        r["liveserviceindowntime"] = liveservicelistdowntime[3]
                        r["liveserviceinhostdowntime"] = liveservicelistdowntime[4]
                    except:
                        r["src_host"] = "n/a"
                        r["name"] = "n/a"
                        r["liveserviceindt"] = "n/a"
                        r["liveserviceinhdt"] = "n/a"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

