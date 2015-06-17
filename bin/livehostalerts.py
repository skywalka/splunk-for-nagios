# Script to list remote hosts (not ok) in Nagios by accessing MK Livestatus
# Required field to be passed to this script from Splunk: n/a
import socket,string,sys,re,mklivestatus
import splunk.Intersplunk

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
    	    for h in HOST:
	        content = [ "GET hosts\nFilter: state > 0\nColumns: name address alias state\n" ]
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
		    livehosts2 = data.strip()
	            table2 = data.strip()
	            table = table2.split("\n")
	            s.close()
    	    	r["livehostalerts_results"] = table
        except:
            r["livehostalerts_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

