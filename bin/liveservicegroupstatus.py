# Script to list Service Group members in Nagios by accessing MK Livestatus
# Required field to be passed to this script from Splunk: host (mk-livestatus/nagios server)
import socket,string,sys,re,splunk.Intersplunk,mklivestatus

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "host" in r:
                try:
                    PORT = mklivestatus.PORT
		    content = [ "GET servicegroups\nColumns: name members_with_state\n" ]
    		    query = "".join(map(str,content))
		    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		    s.connect(((r["host"]), PORT))
		    s.send(query)
		    s.shutdown(socket.SHUT_WR)
		    data = s.recv(100000000)
		    table = data.split('\n')
		    liveservicegroupstatus_results = table
		    s.close()
		    servicesgs_results = []
		    for sg in liveservicegroupstatus_results:
			for sgmembers in re.finditer(r'([^;]*);(.*)', sg):
			    servicegroupname = "|%s," % sgmembers.group(1)
			    servicegroupmembers = sgmembers.group(2)
			    servicesg = (re.sub( r'(,|$)' , servicegroupname, servicegroupmembers))
			    servicesg2 = (re.findall(r'([^,$]+)', servicesg))
			    servicesgs_results = servicesgs_results + servicesg2
		    r["liveservicestatus_results"] = servicesgs_results
                except:
                    r["liveservicestatus_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

