# Script to acknowledge a host alert by accessing MK Livestatus
# Required field to be passed to this script from Splunk: host_name & comment (must be wrapped in double quotes if comment contains spaces)
import socket,string,sys,re,mklivestatus
from datetime import datetime, timedelta
import splunk.Intersplunk

results = []

if len(sys.argv) != 3:                                                           
    print "Usage: %s [host_name] [comment]" % sys.argv[0]                                 
    sys.exit(1)                                                                  

host_name2 = sys.argv[1]
host_name = host_name2.lower()
comment = sys.argv[2]

try:
    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()
    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
	    nowepoch2 = datetime.now()
	    nowepoch = nowepoch2.strftime("%s")
    	    for h in HOST:
		#/bin/printf "[%lu] ACKNOWLEDGE_HOST_PROBLEM;host1;2;1;1;Some One;Some Acknowledgement Comment\n" $now > $commandfile
		content = [ "COMMAND [", nowepoch, "] ACKNOWLEDGE_HOST_PROBLEM;", host_name, ";1;1;0;nagiosadmin;", comment, "\n" ]
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
		    livehostack = string.split(data)
		    s.close()
                r["livehostack"] = "Acknowledged"
        except:
            r["livehostack"] = "UNKNOWN"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

