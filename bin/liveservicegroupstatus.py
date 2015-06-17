# Script to list Service Group members in Nagios by accessing MK Livestatus
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
		content = [ "GET servicegroups\nColumns: name members_with_state\n" ]
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
	        liveservicegroupstatus_results = table
	        s.close()
	        hostsgs_results = []
	        for sg in liveservicegroupstatus_results:
		    for sgmembers in re.finditer(r'([^;]*);(.*)', sg):
		        servicegroupname = "|%s," % sgmembers.group(1)
		        servicegroupmembers = sgmembers.group(2)
		        hostsg = (re.sub( r'(,|$)' , servicegroupname, servicegroupmembers))
		        hostsg2 = (re.findall(r'([^,$]+)', hostsg))
		        hostsgs_results = hostsgs_results + hostsg2
	    r["liveservicestatus_results"] = hostsgs_results
        except:
            r["liveservicestatus_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

