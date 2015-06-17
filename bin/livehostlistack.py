# Script to acknowledge a host alert by accessing MK Livestatus
# Required field to be passed to this script from Splunk: host_name & comment (must be wrapped in double quotes if comment contains spaces)
import socket,string,sys,re,mklivestatus
import splunk.Intersplunk

results = []

if len(sys.argv) != 2:                                                           
    print "Usage: %s [acktype]" % sys.argv[0]                                 
    sys.exit(1)                                                                  

acktype = int(sys.argv[1])

try:
    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()
    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
    	    for h in HOST:
		content = [ "GET hosts\nFilter: acknowledged = ", acktype, "\nFilter: state != 0\nAnd: 2\nColumns: host_name acknowledged\n" ]
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
    		data2 = (re.findall(r'(No UNIX socket)', data))
		if data2:
		    #Error: MK Livestatus module not loaded?
		    s.close()
		else:
		    livehostlistack2 = data.strip()
		    livehostlistack = livehostlistack2.split("\n")
		    s.close()
                r["livehostlistack"] = livehostlistack
        except:
            r["livehostlistack"] = "UNKNOWN"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

