# Script to request hosts with UP status and total hosts by accessing MK Livestatus
# Required field to be passed to this script from Splunk: host (mk-livestatus/nagios server)
import socket,string,sys,re,splunk.Intersplunk,mklivestatus

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "host" in r:
                    try:
			HOST = mklivestatus.HOST
		        PORT = mklivestatus.PORT
			s = None 
		        livehostsup = 0
		        livehoststotal = 0
    			for h in HOST:
			    content = [ "GET hosts\nStats: state = 0\nStats: state != 9999\n" ]
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
			        livehostsupind = int(livehosts[0])
			        livehoststotalind = int(livehosts[1])
			        livehostsup = livehostsup + livehostsupind
			        livehoststotal = livehoststotal + livehoststotalind
                        r["livehostsupstatus"] = livehostsup
                        r["livehoststotalstatus"] = livehoststotal
                    except:
                        r["livehostsupstatus"] = "0"
                        r["livehoststotalstatus"] = "0"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

