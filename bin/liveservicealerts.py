# Script to list all remote hosts' service state (not ok) in Nagios by accessing MK Livestatus
# Required fields to be passed to this script from Splunk: host (mk-livestatus/nagios server) & src_host
import socket,string,sys,splunk.Intersplunk,mklivestatus

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "host" in r:
                try:
		    PORT = mklivestatus.PORT
		    content = [ "GET services\nFilter: state > 0\nColumns: host_name description plugin_output state\n" ]
    		    query = "".join(map(str,content))
		    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		    s.connect(((r["host"]), PORT))
		    s.send(query)
		    s.shutdown(socket.SHUT_WR)
		    data = s.recv(100000000)
		    table2 = data.strip()
		    table = table2.split('\n')
		    s.close()
    		    r["liveservicealerts_results"] = table
                except:
                    r["liveservicealerts_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

