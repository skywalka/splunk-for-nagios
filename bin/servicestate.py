# Script to request a hosts' service state by accessing the nagios livestatus
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
		        HOST = '10.20.14.114'    # The remote nagios server
		        PORT = 6557              # The remote port on the nagios server
		        content = [ "GET services\nColumns: state\nFilter: host_name = ", (r["src_host"]), "\nFilter: description = ", (r["name"]), "\n" ]
    		        query = "".join(content)
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
		        livestate = string.split(data)
		        s.close()
                        r["livestate"] = livestate[0]
                    except:
                        r["livestate"] = "0"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

