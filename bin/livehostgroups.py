# Script to list Host Groups in Nagios by accessing MK Livestatus
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
		content = [ "GET hostgroups\nColumns: name num_hosts num_hosts_down num_hosts_pending num_hosts_unreach num_hosts_up num_services num_services_crit num_services_hard_crit num_services_hard_ok num_services_hard_unknown num_services_hard_warn num_services_ok num_services_pending num_services_unknown num_services_warn worst_host_state worst_service_hard_state worst_service_state\n" ]
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
		    livehg2 = data.strip()
		    livehgs = livehg2.split('\n')
		    s.close()
		r["livehostgroups_results"] = livehgs
        except:
            r["livehostgroups_results"] = "Unknown"

except:
    import traceback
    stack =  traceback.format_exc()
    results = splunk.Intersplunk.generateErrorResults("Error : Traceback: " + str(stack))

splunk.Intersplunk.outputResults( results )

