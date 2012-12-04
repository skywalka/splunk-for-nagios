# Script to request a hosts' SLA by accessing MK Livestatus
import socket
import sys,splunk.Intersplunk
import string
from datetime import datetime, timedelta

results = []

try:

    results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

    for r in results:
        if "_raw" in r:
            if "src_host" in r:
                    try:
		        HOST = 'nagios1'    # The remote nagios server
		        PORT = 6557              # The remote port on the nagios server
			N = int(r["daysago"])
			nowepoch = datetime.now()
			nowepoch2 = nowepoch.strftime("%s")
			date_N_days_ago = datetime.now() - timedelta(days=N)
			date_N_days_ago2 = date_N_days_ago.strftime("%s")
		        content = [ "GET statehist\nFilter: host_name = ", (r["src_host"]), "\nFilter: service_description = ", "\nFilter: time >= ", date_N_days_ago2, "\nFilter: time < ", nowepoch2, "\nStats: sum duration_part_ok", "\n" ]
    		        query = "".join(content)
		        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		        s.connect((HOST, PORT))
		        s.send(query)
		        s.shutdown(socket.SHUT_WR)
		        data = s.recv(100000000)
		        livehostsla = string.split(data)
		        s.close()
                        r["livehostsla"] = livehostsla[0]
                    except:
                        r["livehostsla"] = "0"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

