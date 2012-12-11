# Script to set downtime for a host by accessing MK Livestatus
# Required fields to be passed to this script from Splunk: src_host, starttime, endtime, comment
import socket
import sys,splunk.Intersplunk
import string
import datetime

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                    try:
		        HOST = 'nagios1'    # The remote nagios server
		        PORT = 6557         # The remote port on the nagios server
			nowepoch = datetime.datetime.now()
			nowepoch2 = nowepoch.strftime("%s")
			start = (r["starttime"])
			end = (r["endtime"])
			timeformat = "%Y-%m-%d %H:%M:%S"
			st = datetime.datetime.strptime(start, timeformat)
			st2 = int(st.strftime("%s"))
			et = datetime.datetime.strptime(end, timeformat)
			et2 = int(et.strftime("%s"))
			duration = et2 - st2
		        content = [ "COMMAND [", nowepoch2, "] SCHEDULE_HOST_DOWNTIME;", (r["src_host"]), ";", st2, ";", et2, ";1;0;", duration, ";nagiosadmin;", (r["comment"]), "\n" ]
    		        query = "".join(map(str,content))
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
		        livehostdowntime = string.split(data)
		        s.close()
                        r["livehostdowntime"] = "Downtime Scheduled"
                    except:
                        r["livehostdowntime"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

