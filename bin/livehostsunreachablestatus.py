# Script to request all hosts with UP status by accessing MK Livestatus
import socket
import sys,splunk.Intersplunk
import string

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                    try:
		        HOST = '10.20.14.114'    # The remote nagios server
		        PORT = 6557              # The remote port on the nagios server
		        content = [ "GET hosts\nFilter: scheduled_downtime_depth > 0\nFilter: host_scheduled_downtime_depth > 0\nOr: 2\nNegate:\nStats: last_hard_state = 2\n" ]
    		        query = "".join(content)
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
		        livehostsunreachablestatus = string.split(data)
		        s.close()
                        r["livehostsunreachablestatus"] = livehostsunreachablestatus[0]
                    except:
                        r["livehostsunreachablestatus"] = "0"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

