# Script to list unacknowledged service problems by accessing MK Livestatus
import socket
import sys,splunk.Intersplunk
import string

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                if "name" in r:
                    try:
		        HOST = 'nagios1'    # The remote nagios server
		        PORT = 6557              # The remote port on the nagios server
		        content = [ "GET services\nFilter: acknowledged = 0\nFilter: state != 0\nAnd: 2\nColumns: host_name service_description acknowledged\n" ]
    		        query = "".join(content)
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
			liveservicelistunack2 = data.strip()
			liveservicelistunack = liveservicelistunack2.split(";")
			s.close()
                        r["src_host"] = liveservicelistunack[0]
                        r["name"] = liveservicelistunack[1]
                        r["liveservicelistunack"] = liveservicelistunack[2]
                    except:
                        r["src_host"] = "None"
                        r["name"] = "None"
                        r["liveservicelistunack"] = "None"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

