#!/usr/bin/python
import sys,string,socket,re,mklivestatus
HOST = mklivestatus.HOST
PORT = mklivestatus.PORT
s = None
livehoststatus_results = []
for h in HOST:
    content = [ "GET hosts\nColumns: name address alias state\n" ]
    query = "".join(map(str,content))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((h, PORT))
    except socket.error, (value,message):
        if s: 
	    s.close() 
	    print "Error connecting to %s on port %d: " % (h, PORT) + message 
	    break
    s.send(query)
    s.shutdown(socket.SHUT_WR)
    data = s.recv(100000000)
    data2 = (re.findall(r'(No UNIX socket)', data))
    if data2:
	print "Error connecting to %s on port %d: " % (h, PORT) + data
	s.close()
    else:
    	table = data.strip('\n')
    	s.close()
	print table
