# Script to acknowledge a hosts' service problem by accessing MK Livestatus
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
		        #content = [ "GET services\nFilter: acknowledged = 0\nFilter: state != 0\nAnd: 2\nStats: acknowledged = 0\n" ]
		        content = [ "GET services\nFilter: acknowledged = 0\nFilter: state != 0\nAnd: 2\nColumns: host_name service_description acknowledged\n" ]
    		        query = "".join(content)
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
			liveservicelistack2 = data.strip()
			liveservicelistack = liveservicelistack2.split(";")
			s.close()
                        r["src_host"] = liveservicelistack[0]
                        r["name"] = liveservicelistack[1]
                        r["liveservicelistack"] = liveservicelistack[2]
                    except:
                        r["liveservicelistack"] = "Unknown Error"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

