# Script to list acknowledged service problems by accessing MK Livestatus
import socket,string,mklivestatus
import sys,splunk.Intersplunk

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                try:
		    PORT = mklivestatus.PORT
		    content = [ "GET services\nFilter: acknowledged = ", (r["acktype"]), "\nFilter: state != 0\nAnd: 2\nColumns: host_name service_description acknowledged\n" ]
    		    query = "".join(content)
		    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		    s.connect(((r["host"]), PORT))
		    s.send(query)
		    s.shutdown(socket.SHUT_WR)
		    data = s.recv(100000000)
		    liveservicelistack2 = data.strip()
		    liveservicelistack = liveservicelistack2.split("\n")
		    s.close()
                    r["liveservicelistack"] = liveservicelistack
                except:
                    r["liveservicelistack"] = "UNKNOWN"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

