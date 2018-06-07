#coding:utf-8
"""套接字客户端"""
import socket,time
from datetime import datetime

address = ("localhost",9999)
max_size = 1000
while True:
    print("Start The Client...")

    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    client.connect(address)

    client.sendall(b"Hello,I'm a client")

    data = client.recv(max_size)

    print("AT",datetime.now(),"some replay",data)

    client.close()

    time.sleep(3)