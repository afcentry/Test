#coding:utf-8
"""套接字服务端"""
import socket
from datetime import datetime

address = ('localhost',9999)
max_size = 1000
print('Start server at {}'.format(datetime.now()))
print('Waiting for a client now ...')
while True:
    #套接字创建
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    #进行端口地址绑定
    server.bind(address)
    print(server)
    #指定最大连接数【最多允许和多少个客户端连接】
    server.listen(5)

    #调用accept方法，socket进入waiting状态，客户端请求连接时，方法建立并返回服务器
    # accept方法返回一个含有两个元素的 元组(connection,address)。
    # 第一个元素connection是新的socket对象，服务器必须通过它与客户通信；
    # 第二个元素 address是客户的Internet地址
    client,addr = server.accept()

    data = client.recv(max_size)
    '''
    指定最大可以接受消息长度为1000字节
    '''

    print("AT",datetime.now(),client,"Said",data)
    client.sendall(b'wecome talk to me,client')
    client.close()
    server.close()