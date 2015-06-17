# Script to list Host Group members in Nagios by accessing MK Livestatus
# Required field to be passed to this script from Splunk: n/a
import socket,string,sys,re,splunk.Intersplunk,mklivestatus

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        try:
            HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
    	    for h in HOST:
	        content = [ "GET hostgroups\nColumns: name members_with_state\n" ]
    	        query = "".join(map(str,content))
    	        try:
        	    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        	    s.connect((h, PORT))
    		except socket.error, (value,message): 
        	    if s: 
		    	s.close() 
		    	#Error: Could not open socket: connection refused (MK Livestatus not setup in xinetd?)
		    	break
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

