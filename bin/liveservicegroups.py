# Script to list Service Groups in Nagios by accessing MK Livestatus
# Required field to be passed to this script from Splunk: host (mk-livestatus/nagios server)
import socket,string,sys,splunk.Intersplunk,mklivestatus

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "host" in r:
                try:
                    PORT = mklivestatus.PORT
		    content = [ "GET servicegroups\nColumns: name num_services num_services_crit num_services_hard_crit num_services_hard_ok num_services_hard_unknown num_services_hard_warn num_services_ok num_services_pending num_services_unknown num_services_warn worst_service_state\n" ]
		    query = "".join(content)
		    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		    s.connect(((r["host"]), PORT))
		    s.send(query)
		    s.shutdown(socket.SHUT_WR)
		    data = s.recv(100000000)
		    livehg2 = data.strip()
		    livehgs = livehg2.split('\n')
		    s.close()
		    r["liveservicegroups_results"] = livehgs
                except:
                    r["liveservicegroups_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

