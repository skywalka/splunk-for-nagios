# Script to request hosts with DOWN status and total hosts by accessing MK Livestatus
# Required field to be passed to this script from Splunk: n/a
import socket,string,sys,re,splunk.Intersplunk,mklivestatus

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        try:
	    HOST = mklivestatus.HOST
	    PORT = mklivestatus.PORT
            s = None 
            livehostsdown = 0
	    livehoststotal = 0
    	    for h in HOST:
	        content = [ "GET hosts\nStats: state = 1\nStats: state != 9999\n" ]
	        query = "".join(content)
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
		    livehosts = livehosts2.split(";")
		    s.close()
		    livehostsdownind = int(livehosts[0])
		    livehoststotalind = int(livehosts[1])
		    livehostsdown = livehostsdown + livehostsdownind
		    livehoststotal = livehoststotal + livehoststotalind
                r["livehostsdownstatus"] = livehostsdown
                r["livehoststotalstatus"] = livehoststotal
        except:
            r["livehostsdownstatus"] = "0"
            r["livehoststotalstatus"] = "0"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

