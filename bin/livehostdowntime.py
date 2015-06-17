# Script to set downtime for a host by accessing MK Livestatus
# Required fields to be passed to this script from Splunk: host_name, starttime, endtime, comment (double quotes should be used for arguments that contain spaces)
import socket,string,sys,re,datetime,mklivestatus
import splunk.Intersplunk

results = []

if len(sys.argv) != 5:
    print "Usage: %s [host_name] [starttime] [endtime] [comment]" % sys.argv[0]
    sys.exit(1)

host_name2 = sys.argv[1]
host_name = host_name2.lower()
starttime = sys.argv[2]
endtime = sys.argv[3]
comment = sys.argv[4]

try:
    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()
    for r in results:
        try:
	    HOST = mklivestatus.HOST
            PORT = mklivestatus.PORT
	    nowepoch2 = datetime.datetime.now()
	    nowepoch = nowepoch2.strftime("%s")
	    timeformat = "%Y-%m-%d %H:%M:%S"
	    st2 = datetime.datetime.strptime(starttime, timeformat)
	    st = int(st2.strftime("%s"))
	    et2 = datetime.datetime.strptime(endtime, timeformat)
	    et = int(et2.strftime("%s"))
	    duration = et - st
    	    for h in HOST:
		content = [ "COMMAND [", nowepoch, "] SCHEDULE_HOST_DOWNTIME;", host_name, ";", st, ";", et, ";1;0;", duration, ";nagiosadmin;", comment, "\n" ]
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
		    livehostdowntime = data.split()
		    s.close()
                r["livehostdowntime"] = "Downtime Scheduled"
        except:
            r["livehostdowntime"] = "UNKNOWN"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

