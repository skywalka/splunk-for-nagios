# Script to list Host Groups in Nagios by accessing MK Livestatus
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
		    content = [ "GET hostgroups\nColumns: name members_with_state\n" ]
    		    query = "".join(map(str,content))
		    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		    s.connect(((r["host"]), PORT))
		    s.send(query)
		    s.shutdown(socket.SHUT_WR)
		    data = s.recv(100000000)
		    table = data.split('\n')
		    livehoststatus_results = table
		    s.close()
		    for hg in livehoststatus_results:
		        for mo in re.finditer(r'([^;]*);(.*)', hg):
		            hostgroupname = "|%s," % mo.group(1)
		            hostgroupmembers = mo.group(2)
		            table = re.sub( r'(,|$)' , hostgroupname, hostgroupmembers)
    		            r["livehoststatus_results"] = table
                except:
                    r["livehoststatus_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

