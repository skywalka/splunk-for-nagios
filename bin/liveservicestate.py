# Script to list remote services in Nagios by accessing MK Livestatus
# Required field to be passed to this script from Splunk: status (eg. 0, 1, 2, 3, 666, 9999)
# where 666 is any non-zero status, and 9999 is any status
import socket,string,sys,re,mklivestatus
import splunk.Intersplunk

results = []

if len(sys.argv) != 3:                                                           
    print "Usage: %s [status] [host_name]" % sys.argv[0]                                 
    sys.exit(1)                                                                  

status_zero = 0
status2 = int(sys.argv[1])
host_name3 = sys.argv[2]
host_name2 = host_name3.lower()

if status2 == 666:
    mkl_filter = ">"
    status3 = status_zero
elif status2 == 9999:
    mkl_filter = "!="
    status3 = status2
else:
    mkl_filter = "="
    status3 = status2

status = "%s %d" % (mkl_filter, status3)

if host_name2 == "all":
    mkl_filter2 = "!="
    host_name = host_name2
else:
    mkl_filter2 = "=~"
    host_name = host_name2

host_status = "%s %s" % (mkl_filter2, host_name)

try:
    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()
    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
    	    for h in HOST:
	        content = "GET services\nFilter: host_name %s\nFilter: state %s\nAnd: 2\nColumns: host_name description plugin_output state\n" % (host_status, status)
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
		    liveservices2 = data.strip()
	            table2 = data.strip()
	            table = table2.split("\n")
	            s.close()
    	    	r["liveservicestatus_results"] = table
        except:
            r["liveservicestatus_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

