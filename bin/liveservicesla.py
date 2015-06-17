# Script to request service SLA by accessing MK Livestatus
# Required field to be passed to this script from Splunk: host_name & daysago (must be an integer)
import socket,string,sys,re,mklivestatus
from datetime import datetime, timedelta
import splunk.Intersplunk

results = []

if len(sys.argv) != 3:                                                           
    print "Usage: %s [host_name] [daysago]" % sys.argv[0]                                 
    sys.exit(1)                                                                  

host_name2 = sys.argv[1]
host_name = host_name2.lower()
daysago2 = int(sys.argv[2])

if daysago2 <= 0:
    daysago = 1
else:
    daysago = daysago2

try:
    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()
    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
	    N = int(daysago)
	    nowepoch2 = datetime.now()
	    nowepoch = nowepoch2.strftime("%s")
	    date_N_days_ago2 = datetime.now() - timedelta(days=N)
	    date_N_days_ago = date_N_days_ago2.strftime("%s")
    	    for h in HOST:
		content = [ "GET statehist\nColumns: host_name service_description\nFilter: host_name = ", host_name, "\nFilter: time >= ", date_N_days_ago, "\nFilter: time < ", nowepoch, "\nStats: sum duration_part_ok", "\n" ]
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
		    liveservicesla2 = data.strip()
		    liveservicesla = liveservicesla2.split('\n')
		    s.close()
                r["liveservicesla"] = liveservicesla
        except:
            r["liveservicesla"] = "UNKNOWN"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

