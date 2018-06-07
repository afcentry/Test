# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_FBot_BaseFuncReal.py 天元功能机器人－基本功能实现
#
# start by sk. 170404

from datetime import datetime
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc


# 接口：
# 设置自动连接。
# 当前可以发送数据了吗？
# 设置单下一次不等待调度发送
# 自动调度检查

# 3.1 对HL管套操作的封装 CTYFBot_OpSessionSock
# 建立发送队列。当管套未连接成功，或者管套已经关闭时，暂停发送数据。
# 以会话方式提交发送。
# 设置默认的状态等待，当有数据等待发送时，不等待。当无重要数据发送时，调度获得发送数据。
# start by sk. 170404
class CTYFBot_OpSession_ConnectSock:

    # 初始化：目标地址-端口-默认空闲等待时间-默认重新连接时间
    def __init__(self, hlSockMang, strDestSrvName, iDestPort, iDefaultIdleTick=5, iDefaultReconnectTick=1200):
        self.s_strDestSrvName = strDestSrvName
        self.s_iDestPort = iDestPort                     # 目标短裤
        self.s_iSendDataIdleTime = iDefaultIdleTick        # 发送数据的等待时间
        self.s_iCheckReconnectTime = iDefaultReconnectTick    # 长时间未收到返回，检查重新连接的时间
        self.s_iNextSendWaitCheckTick = self.s_iSendDataIdleTime    # 下一次发送等待的检查时间
        self.s_execHLSockMang = hlSockMang                # 管套管理对象
        self.s_iExecConnectSockIndex = 0                  # 执行连接的管套索引值
        self.s_lastSendTime = datetime(2017,1,1)
        self.s_bWaitReply = False           # 是否已经发送等待回应?
        self.s_lastRecvCTArray = []         # 上次接收的数据包队列
        pass

    def __del__(self):
        self.Close()

    def Close(self):
        if( self.s_iExecConnectSockIndex):
            self.s_execHLSockMang.CloseSockByIndex(self.s_iExecConnectSockIndex)
            self.s_iExecConnectSockIndex = 0
        pass

    # 执行下一步检查
    def ExecNextCheck(self):
        bRetValue = False
        # 如果还没有开始连接，那么，开始连接
        if( not self.s_iExecConnectSockIndex):
            self.s_iExecConnectSockIndex = self.s_execHLSockMang.CreateConnectSock( self.s_strDestSrvName, self.s_iDestPort)
            self.s_lastSendTime = datetime(2017, 1, 1)
            self.s_bWaitReply = False
            bRetValue = True

        # 是否已经连接成功
        if( self.s_execHLSockMang.IsSockConnectSuccess( self.s_iExecConnectSockIndex)):
            # 如果数据发送后，长时间数据未到达，可能对方重启了，本地重启连接
            if( self.s_bWaitReply):
                if (CTYLB_MainSys_MiscFunc.CheckIdleTime(self.s_lastSendTime, self.s_iCheckReconnectTime)):
                    self.s_execHLSockMang.CloseSockByIndex(self.s_iExecConnectSockIndex)
                    self.s_iExecConnectSockIndex = 0
                    pass

        if( self.s_iExecConnectSockIndex):
            bSockExist, recvCTArray = self.s_execHLSockMang.PassiveRecv_From_ConnectSock( self.s_iExecConnectSockIndex)
            if( not bSockExist):
                self.s_iExecConnectSockIndex = 0
            else:
                if( recvCTArray):
                    self.s_lastRecvCTArray.extend(recvCTArray)
                    self.s_bWaitReply = False
                    bRetValue = True

        return bRetValue

    # 执行下一步发送
    def ExecSendData(self, ctDataArray):
        self.s_bWaitReply = True
        self.s_iNextSendWaitCheckTick = self.s_iSendDataIdleTime
        self.s_lastSendTime = datetime.now()
        self.s_execHLSockMang.PromptDataSend_To_ConnectSock(self.s_iExecConnectSockIndex, ctDataArray)

    # 能否执行发送数据？ 当数据取出来后，而且 当连接成功，并且未发送数据时，或者发送后对方已经回应了，并且等待时间超过了，才可以执行发送
    def CanExecSendData(self):
        bRetValue = False
        if( not self.s_lastRecvCTArray):
            if( self.s_execHLSockMang.IsSockConnectSuccess( self.s_iExecConnectSockIndex)):
                if( not self.s_bWaitReply):
                    if (CTYLB_MainSys_MiscFunc.CheckIdleTime(self.s_lastSendTime, self.s_iNextSendWaitCheckTick)):
                        bRetValue = True
        return bRetValue

    # 是否有数据接收到
    def PopRetriveRecvCTArray(self):
        retDataArray = []
        if( self.s_lastRecvCTArray):
            retDataArray.extend( self.s_lastRecvCTArray)
            self.s_lastRecvCTArray = []
        return retDataArray

    # 设置下一次等待发送时间
    def SetNextTempSendWaitTick(self, iNextTmpWaitTick):
        self.s_iNextSendWaitCheckTick = iNextTmpWaitTick
