# Script to list service problems in downtime by accessing MK Livestatus
# Required argument to be passed to this script from Splunk: host_name
import socket,string,sys,re,mklivestatus
import splunk.Intersplunk

results = []

if len(sys.argv) != 2:
    print "Usage: %s [host_name]" % sys.argv[0]
    sys.exit(1)

host_name2 = sys.argv[1]
host_name = host_name2.lower()

try:
    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()
    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
    	    for h in HOST:
		content = [ "GET services\nFilter: host_name = ", host_name, "\nColumns: host_name service_description state scheduled_downtime_depth host_scheduled_downtime_depth\nSeparators: 10 44 44 124\n" ]
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
		    liveservicelistdowntime2 = data.strip()
		    liveservicelistdowntime = liveservicelistdowntime2.split("\n")
		    s.close()
                r["liveservicelistdowntime"] = liveservicelistdowntime
        except:
            r["liveservicelistdowntime"] = "UNKNOWN"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

