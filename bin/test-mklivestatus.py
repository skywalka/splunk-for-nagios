#!/usr/bin/python
import sys,string,socket,mklivestatus
HOST = mklivestatus.HOST
PORT = mklivestatus.PORT
livehoststatus_results = []
for h in HOST:
    content = [ "GET hosts\nColumns: name address alias state\n" ]
    query = "".join(map(str,content))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((h, PORT))
    s.send(query)
    s.shutdown(socket.SHUT_WR)
    data = s.recv(100000000)
    table = data.split()
    s.close()
    print table
