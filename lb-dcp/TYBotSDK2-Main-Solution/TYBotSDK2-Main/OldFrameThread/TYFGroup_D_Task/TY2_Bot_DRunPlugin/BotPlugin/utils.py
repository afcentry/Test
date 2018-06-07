#=-*-coding:utf-8 -*-
import platform
import socket
import struct
import re

def isWindwosOS():
    '''
        判断当前操作系统是否为Windows操作系统
        :return: 是：True，否：False
    '''
    if "windows" in platform.platform().lower():
        return True
    return False

def isUnixOS():
    '''
        判断当前操作系统是否为Unix或者Linux操作系统
        :return: 是：True，否：False
    '''
    return isWindwosOS()==False

def ip2Long(ip):
    '''
        将字符串IP转换成整型IP值
        :param ip: 字符串IP值
        :return: 整型IP值
    '''
    packIP=socket.inet_aton(ip)
    return struct.unpack("!L",packIP)[0]

def long2IP(ip):
    '''
       将整型IP转换成字符串型IP
       :param ip: 整型IP值
       :return: 字符串IP值
    '''
    return socket.inet_ntoa(struct.pack("!L",ip))

def valid_ip(address):
    '''
    验证字符串IP是否合法
    :param address: 需要验证的字符串IP
    :return: 是合法IP-True，否则-False
    '''
    try:
        socket.inet_aton(address)
        return True
    except:
        return False

def valid_domain(domain):
    '''
    验证域名是否合法
    :param domain: 需要验证的域名
    :return: 是合法域名-True，否则-False
    '''
    pattern=r"(?i)^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$"
    if re.match(pattern,domain):
        return True
    else:
        return False


def split_and_remove_empty(souceStr,sep,maxsplit=-1):
    '''
    拆分字符串，并移除空的（含空格、换行、制表符）字符串
    :param souceStr: 需要拆分的字符串
    :param sep: 分割符
    :param maxsplit: 最大分割次数
    :return: 拆分后的字符串集合，List类型
    '''
    if isinstance(souceStr,basestring):
        datas=souceStr.split(sep,maxsplit)
        ret=[]
        for d in datas:
            if d=='' or d.strip()=='':
                continue
            d=d.strip()
            ret.append(d)
        return ret
    else:
        return souceStr
