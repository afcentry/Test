#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
    采用nmap扫描，结果存放为Json字符串格式，因为扫描耗时，因此存储所有扫描信息，便于后期根据需要提取数据.

    created time: 2017-04-30
'''
import time
import nmap
import struct
import socket


class NmapScaner(object):
    @staticmethod
    def getTime():
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    @staticmethod
    def IP2Long(ip):
        packIP = socket.inet_aton(ip)
        return struct.unpack("!L", packIP)[0]

    @staticmethod
    def Long2IP(ip):
        return socket.inet_ntoa(struct.pack("!L", ip))

    @staticmethod
    def changeIp(ip):
        if '.' in ip:
            return ip
        else:
            return NmapScaner.Long2IP(ip)

    # 核心函数
    @staticmethod
    def Scan(ip):
        ip = NmapScaner.changeIp(ip)
        print('[', NmapScaner.getTime(), ']', 'Execute Scaner, IP = %s' % ip)
        # nmap扫描参数，端口服务，操作系统类型都进行判别
        args = '-sV -A -O'
        try:
            nm = nmap.PortScanner()  # 定义扫描器
            tmp = nm.scan(ip, arguments=args)  # 开始扫描
            if 'osmatch' in str(tmp):
                return "%s|*|%s" % (ip, tmp)
            else:
                return 'None'
        except Exception as e:
            print(e)
            print('[!]Scan :%s Error..' % ip)
            return 'None'


if __name__ == '__main__':
    s = NmapScaner()
    print(s.Scan(''))
