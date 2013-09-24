# Script to list Host Group members in Nagios by accessing MK Livestatus
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
		    livehostgroupstatus_results = table
		    s.close()
		    hosthgs_results = []
		    for hg in livehostgroupstatus_results:
			for hgmembers in re.finditer(r'([^;]*);(.*)', hg):
			    hostgroupname = "|%s," % hgmembers.group(1)
			    hostgroupmembers = hgmembers.group(2)
			    hosthg = (re.sub( r'(,|$)' , hostgroupname, hostgroupmembers))
			    hosthg2 = (re.findall(r'([^,$]+)', hosthg))
			    hosthgs_results = hosthgs_results + hosthg2
		    r["livehoststatus_results"] = hosthgs_results
                except:
                    r["livehoststatus_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

