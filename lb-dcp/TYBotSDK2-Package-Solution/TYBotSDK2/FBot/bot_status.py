#======================================================
#功能机器人节点状态汇报-状态信息数据结构实现类
#封装需要向状态监控节点汇报信息的数据结构
#
#Pxk    2017-06-24
#======================================================
import time
import os
import socket
import psutil
import json

class SockInfo:
    '''
    Sock连接信息类，实现记录Sock连接相关信息
    '''
    def __init__(self,name,operateId=0,sockType="Connect",status="Down",totalSend=0,totalRecv=0,lastSendTime=0,lastRecvTime=0):
        #Sock连接名称
        self.Name=name
        #Sock操作ID
        self.OperateID=operateId
        #Sock连接类型，Connect-连接其他服务端类型，Listen-来自监听的客户端连接类型
        self.Type=sockType
        #Sock连接状态: Up-正在运行 Down-已经停止
        self.Status=status
        #发送的数据包总数
        self.TotalSend=totalSend
        #接收到的数据包总数
        self.TotalRecv=totalRecv
        #最后一次发送包的时间
        self.LastSendTime=lastSendTime
        #最后一次接收包的时间
        self.LastRecvTime=lastRecvTime

    def dump_obj(self):
        '''
        将当前Sock连接信息对象转换成字典格式
        :return: 字典格式的Sock连接对象
        '''
        obj={}
        obj['Name']=self.Name
        obj['OperateID'] = self.OperateID
        obj['Type'] = self.Type
        obj['Status'] = self.Status
        obj['TotalSend'] = self.TotalSend
        obj['TotalRecv'] = self.TotalRecv
        obj['LastSendTime'] = self.LastSendTime
        obj['LastRecvTime'] = self.LastRecvTime

        return obj

class NodeStatus:
    '''
    节点状态信息类，实现对节点状态信息的封装
    '''
    def __init__(self,name,nodeType="FBot",comment=""):
        #FBot节点名称
        self.NodeName=name
        #FBot节点类型：FBot-功能机器人类型,Server-中转节点类型
        self.NodeType="FBot"
        #FBot节点功能说明或者描述
        self.NodeComment=comment
        #FBot节点启动运行时间
        self.StartupTime=NodeStatus.get_now_timestamp()
        #FBot当前状态汇报时间
        self.StatusTime=0
        #当前节点的Sock连接信息
        self.SocksInfo={}
        #当前节点所有的Sock连接信息
        self.SocksInfo['Socks']={}
        #当前节点所有发送的包数目
        self.SocksInfo["TotalSend"]=0
        #当前节点所有收到的包数目
        self.SocksInfo["TotalRecv"]=0
        #当前节点的主机名
        self.NodeHostName=socket.gethostname()
        #当前节点所有可用IP列表，不包括127.0.0.1
        self.NodeIPAddress=NodeStatus.get_all_avaliable_ip_address()
        #当前节点主机相关信息，包括内存、CPU利用率等
        self.NodeMachineInfo=NodeStatus.get_machine_info()

    def dumps_json(self):
        '''
        将当前节点状态信息转换成json格式字符串
        :return: json格式状态信息
        '''
        jsonObj={}
        jsonObj['NodeName'] = self.NodeName
        jsonObj['NodeType'] = self.NodeType
        jsonObj['NodeComment']=self.NodeComment
        jsonObj['StartupTime'] = self.StartupTime
        jsonObj['StatusTime'] = self.StatusTime
        jsonObj['SocksInfo'] = self.SocksInfo
        jsonObj['NodeHostName'] = self.NodeHostName
        jsonObj['NodeIPAddress'] = self.NodeIPAddress
        jsonObj['NodeMachineInfo'] = self.NodeMachineInfo

        return json.dumps(jsonObj,ensure_ascii=False)


    @staticmethod
    def get_now_timestamp():
        '''
        获取当前时间戳
        :return: 当前时间戳
        '''
        return time.time()

    @staticmethod
    def get_all_avaliable_ip_address():
        '''
        获取当前主机节点所有有效IP地址（不包含127.0.0.1）
        :return: 当前主机节点所有可用有效IP地址集合
        '''
        allIPs=[]
        ifs=psutil.net_if_addrs()
        for key in ifs.keys():
            adds=ifs[key]
            for add in adds:
                address=add.address
                if ":" in address or address == "127.0.0.1":
                    continue
                allIPs.append(address)

        return allIPs

    @staticmethod
    def get_machine_info():
        '''
        获取节点主机相关信息，包括内存，CPU等信息
        :return: 包含主机信息的字典对象
        '''
        machineInfo={}
        cpuInfo={}
        memoryInfo={}
        #当前进程信息
        p=psutil.Process(os.getpid())
        #节点主机内存信息
        virtualMemory=psutil.virtual_memory()
        #总内存大小,bytes
        memoryInfo['Total']=virtualMemory.total
        #可用内存大小,bytes
        memoryInfo['Available'] = virtualMemory.available
        #内存使用率，0-100%
        memoryInfo['Percent'] = virtualMemory.percent
        #已经使用的大小，bytes
        memoryInfo['Used'] = virtualMemory.used
        #空闲内存的大小，bytes
        memoryInfo['Free'] = virtualMemory.free

        #节点主机CPU信息
        #CPU总利用率，0-100%
        cpuInfo['TotalCpuPercent']=psutil.cpu_percent(1)
        #当前FBot进程使用的CPU使用率，0-100%
        cpuInfo['ProcessCpuPercent'] = p.cpu_percent(1)

        #主机总信息
        #主机CPU信息
        machineInfo['CPUInfo']=cpuInfo
        #主机内存信息
        machineInfo['MemoryInfo']=memoryInfo


        return machineInfo



if __name__=="__main__":
    key=b"a"
    print(isinstance(key,bytes))
    s={key.decode():10}
    ss=json.dumps(s)
    print(ss)