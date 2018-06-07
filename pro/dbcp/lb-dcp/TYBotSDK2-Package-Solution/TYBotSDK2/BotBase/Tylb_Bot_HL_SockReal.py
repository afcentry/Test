# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_HL_SockReal.py 天元机器人－高接口级别－管套功能实现
#  实现管套创建，监听，连接的管理
# start by sk. 170304
# update by sk. 增加输出发送数据包队列时，直接赋值
# start by sk. 180315. 升级到V3，采用json方式处理

from TYBotSDK2.P2PClient.Tylb_p2p_ExCall_SubClient import CTYLB_P2P_ContentUnit_Base
from .Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from datetime import datetime
import threading
import random, json

# 通信检查会话，流程：发送信息查询包 -> 等待查询包返回，如果时间太久，就重发 -> 收到回应包后，等待小时间，再发送，循环步骤
# start by sk. 170227
class CTylb_SockSync_Checker:
    # 会话检查通信包的参数，int值，参数1，2, 每次检查时间，和 强制检查时间
    def __init__(self, iEachCheckTickDiff, iLongForceCheckTickDiff):
        self.s_strDestUserID = ''    # 目标用户ID
        self.s_iCheckComuIntValue = 0   # 通信包检查的int值
        self.s_iEachCheckTickDiff = iEachCheckTickDiff  # 每次检查的时间间隔
        self.s_lastEachCheckTime = datetime(2017,1,1)   # 上次检查的时间
        self.s_iLongForceCheckTickDiff = iLongForceCheckTickDiff    # 强制检查的超时时间
        self.s_lastExecSendTime = datetime(2017,1,1)    # 上次执行检查的时间
        self.s_strLastExecQueryUnqiueSign = ''             # 上次执行查询的标识
        pass

    # 是否繁忙，还是空闲
    # start by sk. 170304
    def IsBusy(self):
        bRetValue = False
        if( len(self.s_strLastExecQueryUnqiueSign)>0):
            bRetValue = True
        return bRetValue

    # 接收到会话完成的命令
    def RecvReplyResetSession(self):
        self.s_strLastExecQueryUnqiueSign = ''
        pass

    # 提交发送单元队列，并且进行同步
    # start by sk. 170304
    def ScheduleSendCTUnitArray(self, p2pBotExecFrame, sendCTUnitArray, sockBaseUnit):
        # 提交，整合数据包，发送
        ackCTUnit = CTYBot_CTUnit_HLSockSession()
        ackCTUnit.SetTypeCTUnitArray( sendCTUnitArray, sockBaseUnit)
        sockBaseUnit.Exec_SendCTUnit_AdjustContent( ackCTUnit)
        self.s_strLastExecQueryUnqiueSign = ackCTUnit.s_strUniqueSign
        pass

# ################################################################################################
#   重写 内容单元类，高层管套数据传输
#    通用的数据格式,  主命令，s_g_iMainCmd_HLSockSession
#           s_g_iSubCmd_HLSockSession # 子命令。
#   命令包含：端口，数据类型，数据内容
# start by sk. 170304
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_HLSockSession(CTYLB_P2P_ContentUnit_Base):
    # s_iRunPluginID = 0  # 要运行的插件ID, 在 code_bot_exec／Sk_LB_Cfg_RemoteClient.py 的 CSkLB_Config_RemoteClient_BaseDef 中定义
    s_g_strCTUnitSplit = '$#FF@1@j'
    s_g_iType_SYN = 0  # 握手，开始连接
    s_g_iType_ACK = 1  # 连接回应，成功连接
    s_g_iType_SYNACK = 2  # 连接回应，成功连接
    s_g_iType_DATA_COMMON = 3  # 普通数据
    s_g_iType_CLOSE = 4  # 管套关闭
    s_g_iType_DATA_CTUnitArray = 5  # 包含多个单元
    s_g_iType_NOP = 6  # 无实际内容

    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_HLSockSession)
        self.self_SetCmd(CTYLB_Bot_BaseDef.s_g_iMainCmd_HLSockSession, CTYLB_Bot_BaseDef.s_g_iSubCmd_HLSockSession)
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_COMMON  # 数据类型
        self.s_strData = ''
        self.s_iSelfPort = 0  # 自己端口
        self.s_iPeerPort = 0  # 对方端口
        self.s_iMySeq = 0  # 顺序值
        self.s_iPeerSeq = 0   # 对方的顺序值。
        self.s_strCTUnitRecvBuff = ''  # 接收到临时存储的缓冲。通过回调函数进行解码
        self.s_subCTUnitArray = []  # 包含更多子单元
        self.s_strPeerSign = ''  # 数据包传输回应对方的伙伴标识
        pass


    # 空数据包
    # start by sk. 180318
    def SetTypeNop(self, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_NOP  # 数据类型
        self.s_strData = ''
        # 设置端口，和顺序值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)

    def SetTypeData(self, strData, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_COMMON  # 数据类型
        self.s_strData = strData
        # 设置端口，和顺序值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)

    def SetTypeConnect(self, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_SYN  # 数据类型
        self.s_strData = ''
        # 设置端口，和随机值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)
        pass

    def SetTypeClosed(self, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_CLOSE  # 数据类型
        self.s_strData = ''
        # 设置端口，和顺序值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)
        pass

    def SetTypeConnectAck(self, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_ACK  # 数据类型
        self.s_strData = ''
        # 设置端口，和顺序值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)
        pass

    def SetTypeConnectSYNAck(self, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_SYNACK  # 数据类型
        self.s_strData = ''
        # 设置端口，和顺序值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)
        pass

    def SetTypeCTUnitArray(self, ctUnitArray, sockBaseUnit):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_CTUnitArray  # 数据类型
        self.s_subCTUnitArray.extend(ctUnitArray)
        # 设置端口，和顺序值。
        self.__SetPort( sockBaseUnit.s_iLocalPort, sockBaseUnit.s_iRemotePort)
        self.__SetSeqValue( sockBaseUnit.s_iSelfSequence, sockBaseUnit.s_iPeerSequence)
        pass

    # 设置端口值
    def __SetPort(self, iLocalPort, iPeerPort):
        self.s_iSelfPort = iLocalPort  # 自己端口
        self.s_iPeerPort = iPeerPort  # 对方端口

    # 从数据包中，设置直接关闭. 处理以前应用未处理的数据包
    def Ex_SetCloseFromCTUnit(self, hlSockCTUnit, iPeerSeqAdjust):
        self.s_iPacketType = CTYBot_CTUnit_HLSockSession.s_g_iType_CLOSE  # 数据类型
        self.s_iSelfPort = hlSockCTUnit.s_iPeerPort    # 自己端口
        self.s_iPeerPort = hlSockCTUnit.s_iSelfPort    # 对方端口
        self.s_iMySeq = hlSockCTUnit.s_iPeerSeq
        self.s_iPeerSeq = hlSockCTUnit.s_iMySeq + iPeerSeqAdjust   # 每次收发，对应顺序号＋1.对方发了一个数据包，那么，＋1
        pass

    # 设置顺序号数值
    def __SetSeqValue(self, iSelfSeq, iPeerSeq):
        self.s_iMySeq = iSelfSeq
        self.s_iPeerSeq = iPeerSeq

    # 获得单元队列缓冲
    def __GetCTUnitArrayBuff(self):
        strUnitConvertArray = []
        for eachCTUnit in self.s_subCTUnitArray:
            strUnitBuff = eachCTUnit.EX_CombPacket()
            strUnitConvertArray.append(strUnitBuff)
            pass

        strTotalBuff = CTYBot_CTUnit_HLSockSession.s_g_strCTUnitSplit.join(strUnitConvertArray)
        return strTotalBuff

    # 从缓冲字符串中，恢复单元对象. 由于涉及创建新的单元，必须外部回调函数处，传入子单元管理实现
    def RestoreCTUnitArrayFromBuff(self, p2pMainSubUnitReal):
        self.s_subCTUnitArray = []
        strEachArray = self.s_strCTUnitRecvBuff.split(CTYBot_CTUnit_HLSockSession.s_g_strCTUnitSplit)
        for strEach in strEachArray:
            baseUnit = CTYLB_P2P_ContentUnit_Base()
            if (baseUnit.EX_ExactFromPacket(strEach)):
                execCallBackUnit, newExecContentUnit = p2pMainSubUnitReal.ExCall_CreateNewRealCTUnit_FromBaseCTUnit(
                    strEach, baseUnit)
                if (execCallBackUnit and newExecContentUnit):
                    self.s_subCTUnitArray.append(newExecContentUnit)
                pass
        self.s_strCTUnitRecvBuff = ''  # 释放缓冲



    s_g_strUniqueSign = '@@3kss34ka_HLSockSession'

    s_g_Key_s_iPacketType = 's_iPacketType'
    s_g_Key_s_iSelfPort = 's_iSelfPort'
    s_g_Key_s_iPeerPort = 's_iPeerPort'
    s_g_Key_s_strData = 's_strData'
    s_g_Key_strCTUnitBuff = 'strCTUnitBuff'
    s_g_Key_s_strPeerSign = 's_strPeerSign'
    s_g_Key_s_iMySeq = 's_iMySeq'
    s_g_Key_s_iPeerSeq = 's_iPeerSeq'

    s_g_Key_strSign = 'strSign_HLSockSession'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_s_iPacketType] = self.s_iPacketType
        exDict[self.s_g_Key_s_iSelfPort] = self.s_iSelfPort
        exDict[self.s_g_Key_s_iPeerPort] = self.s_iPeerPort
        exDict[self.s_g_Key_s_strData] = self.s_strData
        exDict[self.s_g_Key_strCTUnitBuff] = self.__GetCTUnitArrayBuff()
        exDict[self.s_g_Key_s_strPeerSign] = self.s_strPeerSign
        exDict[self.s_g_Key_s_iMySeq] = self.s_iMySeq
        exDict[self.s_g_Key_s_iPeerSeq] = self.s_iPeerSeq

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iPacketType = int(exDict[self.s_g_Key_s_iPacketType])
                self.s_iSelfPort = int(exDict[self.s_g_Key_s_iSelfPort])
                self.s_iPeerPort = int(exDict[self.s_g_Key_s_iPeerPort])
                self.s_iMySeq = int(exDict[self.s_g_Key_s_iMySeq])
                self.s_iPeerSeq = int(exDict[self.s_g_Key_s_iPeerSeq])

                self.s_strCTUnitRecvBuff = exDict[self.s_g_Key_strCTUnitBuff]
                self.s_strData = exDict[self.s_g_Key_s_strData]
                self.s_strPeerSign = exDict[self.s_g_Key_s_strPeerSign]
        except Exception as e:
            print(str(e))
            pass
        pass

    def ShowInfo(self, strOpType, strDestUser):
        '''
        strPacketType = 'N/A'
        if( self.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_SYN):  # 握手，开始连接
            strPacketType = 'SYN'
        elif (self.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_ACK):   # 连接回应，成功连接
            strPacketType = 'ACK'
        elif (self.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_SYNACK):   # 连接回应，成功连接
            strPacketType = 'SYN-ACK'
        elif ( (self.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_COMMON) or
                   (self.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_CTUnitArray) ):  # 普通数据
            strPacketType = 'DATA'
        elif (self.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_CLOSE):   # 管套关闭
            strPacketType = 'Close'
        strMsg = '[%s]:[%s] [%s] port:[%d-%d] seq:[%d~%d]' % (strOpType, strDestUser, strPacketType, self.s_iSelfPort,
                                                              self.s_iPeerPort, self.s_iMySeq, self.s_iPeerSeq)
        CTYLB_Log.ShowLog(0, 'sock-session', strMsg)
        '''
        pass


# tylb－p2p的 高层管套会话 实际调用，新建会话单元
# start by sk. 170304
def CTYBot_CTUnit_CreateNewUnit_HLSessionSock():
    newContentUnit = CTYBot_CTUnit_HLSockSession()
    return newContentUnit

# tylb－p2p的 管套单元实现
# start by sk. 170304
class CTYBot_SockUnit_Base:
    s_g_iType_None = 0  # 未知类型
    s_g_iType_Listen = 1  # 监听类型
    s_g_iType_Connect = 2  # 连接类型
    s_g_iType_Accept = 3  # 接受连接类型

    s_g_iStatus_None = 0  # 无状态
    s_g_iStatus_Listening = 1  # 状态-正在监听
    s_g_iStatus_StartConnect = 2  # 状态－正在连接
    s_g_iStatus_Connecting = 3  # 状态－正在连接
    s_g_iStatus_Connected = 4  # 状态－无连接
    s_g_iStatus_Closed = 5  # 状态－已关闭

    # 管套初始化
    def __init__(self, parentBotExecFrame, iSockIndex):
        self.s_strRemoteID = ''  # 远程地址
        self.s_iRemotePort = 0  # 远程端口
        self.s_iLocalPort = 0   # 本地端口
        self.s_iType = CTYBot_SockUnit_Base.s_g_iType_None  # 管套类型
        self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Closed  # 状态
        self.s_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_parentBotExecFrame = parentBotExecFrame  # 父执行框架
        self.s_iSockIndex = iSockIndex        # 索引标识值
        # 下面的顺序数，为了避免同端口值的冲突打架
        self.s_iSelfSequence = random.randint( 10000, 100000000)  # 顺序数, 我发的数据包的第一个值。每次＋1
        self.s_iPeerSequence = 0    # 对方的顺序数值。为对方上次顺序数+1. 如果接收到一个数据包，顺序数＝上次＋1，表示正确。否则丢弃此包
        pass

    # 关闭管套
    def Vilu_Close(self):
        self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Closed  # 状态
        pass

    # 调度进行时间检查，判断是否需要关闭，和需要发送的数据包
    def Vilu_Schedule_TimerCheck(self):
        bRetValue = False
        return bRetValue

    # 发送Nop到远端
    # start by sk. 180318
    def Exec_SendNop_To_RemotePeer(self):
        # 回应ACK
        ackCTUnit = CTYBot_CTUnit_HLSockSession()
        ackCTUnit.SetTypeNop( self)
        self.Exec_SendCTUnit_AdjustContent( ackCTUnit, 0)
        pass

    # 发送Close到远端
    def Exec_SendClose_To_RemotePeer(self):
        # 回应ACK
        ackCTUnit = CTYBot_CTUnit_HLSockSession()
        ackCTUnit.SetTypeClosed( self)
        self.Exec_SendCTUnit_AdjustContent( ackCTUnit, 0)
        pass

    # 接收后，调整顺序值.数据长度默认为1
    def Exec_Validate_Update_Recv_PeerSeq(self, iPeerSeq, iDataLen=1):
        bRetValid = False
        if( self.s_iPeerSequence == iPeerSeq):
            bRetValid = True
            self.s_iPeerSequence += iDataLen  # 更新我的peer-seq
        return bRetValid

    # 执行发送数据包的动作。调整内部内容。主要是顺序值
    def Exec_SendCTUnit_AdjustContent(self, sendCTUnit, iDataLen=1):
        sendCTUnit.ShowInfo( 'send', self.s_strRemoteID)
        self.s_iSelfSequence += iDataLen   # 数据长度 = 1. 此时，对方保存的seq还是旧的。所以，对方seq＋数据长度＝数据包seq
        self.s_parentBotExecFrame.SendCTUnitToUser( self.s_strRemoteID, sendCTUnit)
        pass

    # 处理接收到数据包
    def Vilu_RecvDataCTUnit(self, hlSockSessionCTUnit):
        pass
    pass

# tylb－p2p的 管套单元实现。监听管套
# start by sk. 170304
class CTYBot_Listen_SockUnit(CTYBot_SockUnit_Base):
    # 管套初始化
    def __init__(self, parentBotExecFrame, iSockIndex):
        CTYBot_SockUnit_Base.__init__(self, parentBotExecFrame, iSockIndex)
        self.s_iType = CTYBot_SockUnit_Base.s_g_iType_Listen  # 管套类型
        self.s_acceptSockUnitArray = []   # 接收到的管套单元队列
        self.s_iWaitRetriveAcceptPeerPortArray = []   # 等待获取接收到的管套端口值队列
        pass

    # 开始监听
    def Listen(self, iListenPort):
        self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Listening  # 状态
        self.s_strRemoteID = ''
        self.s_iLocalPort = iListenPort
        pass

    # 处理新连接到达的数据
    def HandleNewSockArriveCTUnit(self, strFromName, hlSockSessionCTUnit, iLastSockIndex):
        newAcceptSock = None
        if (self.s_ExecMutex.acquire()):
            # 创建单元
            newAcceptSock = CTYBot_Accept_SockUnit( self.s_parentBotExecFrame, iLastSockIndex)
            newAcceptSock.s_iLocalPort = self.s_iLocalPort
            newAcceptSock.s_iRemotePort = hlSockSessionCTUnit.s_iSelfPort
            newAcceptSock.s_strRemoteID = strFromName
            newAcceptSock.s_iPeerSequence = hlSockSessionCTUnit.s_iMySeq   # 对方接收到后，＋1
            newAcceptSock.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Connected  # 连接成功
            # 加入队列
            self.s_acceptSockUnitArray.append( newAcceptSock)
            self.s_ExecMutex.release()
        return newAcceptSock

    # 弹出新accept管套
    def PopNewAcceptSock(self):
        retNewSock = None
        if (self.s_ExecMutex.acquire()):
            if( len(self.s_acceptSockUnitArray) > 0):
                retNewSock = self.s_acceptSockUnitArray.pop(0)
                self.s_iWaitRetriveAcceptPeerPortArray.append( [retNewSock.s_strRemoteID, retNewSock.s_iRemotePort])
            self.s_ExecMutex.release()
        return retNewSock

    # 弹出新accept管套
    def PopNewArriveAcceptPeerPort(self):
        strRetPeerID, iRetPort = '', 0
        if (self.s_ExecMutex.acquire()):
            if( len(self.s_iWaitRetriveAcceptPeerPortArray) > 0):
                newAcceptInfo = self.s_iWaitRetriveAcceptPeerPortArray.pop(0)
                strRetPeerID = newAcceptInfo[0]
                iRetPort = newAcceptInfo[1]
            self.s_ExecMutex.release()
        return strRetPeerID, iRetPort
    pass

# tylb－p2p的 管套单元实现, accept单元不主动发。等待对方发送，然后回复，采用会话模式
# start by sk. 170304
class CTYBot_Accept_SockUnit(CTYBot_SockUnit_Base):
    # 管套初始化
    def __init__(self, parentBotExecFrame, iSockIndex):
        CTYBot_SockUnit_Base.__init__(self, parentBotExecFrame, iSockIndex)
        self.s_iType = CTYBot_SockUnit_Base.s_g_iType_Accept  # 管套类型
        self.s_origRecvLowLevel_CTUnitArray = []  # 接收到的底层队列数据
        self.s_recvCTUnitArray = []  # 接收缓冲队列
        self.s_needSendCTUnitArray = []  # 发送缓冲队列
        self.s_strLastSendPeerSign = ''  # 上个伙伴发送的标志
        pass

    # 被动发送单元队列。对方会话到了后，才提交进行发送
    def Mg_Acpt_PassiveSend(self, cTUnitArray):
        if (self.s_ExecMutex.acquire()):
            self.s_needSendCTUnitArray.extend(cTUnitArray)
            self.s_ExecMutex.release()
        pass

    # 主动获得接收的内容，然后才被动回复结果。
    def Mg_Acpt_ActiveRecv(self):
        retRecvCTUnitArray = []
        if( self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connected):
            if (self.s_ExecMutex.acquire()):
                if (len(self.s_recvCTUnitArray) > 0):
                    retRecvCTUnitArray = self.s_recvCTUnitArray
                    self.s_recvCTUnitArray = []
                self.s_ExecMutex.release()
        return retRecvCTUnitArray

    # 调度进行时间检查，判断是否需要关闭，和需要发送的数据包
    def Vilu_Schedule_TimerCheck(self):
        bRetValue = CTYBot_SockUnit_Base.Vilu_Schedule_TimerCheck( self)
        # 上次接收到对方的标志？已经接收过数据包，可以回应
        if( self.s_strLastSendPeerSign):
            if (self.s_ExecMutex.acquire()):
                # 有数据包需要发送？
                if (len(self.s_needSendCTUnitArray) > 0):
                    ackCTUnit = CTYBot_CTUnit_HLSockSession()
                    ackCTUnit.SetTypeCTUnitArray(self.s_needSendCTUnitArray, self)
                    ackCTUnit.s_strPeerSign = self.s_strLastSendPeerSign
                    self.Exec_SendCTUnit_AdjustContent(ackCTUnit)
                    bRetValue = True
                    # 发送完后，提交，设置已经发送的状态
                    self.s_strLastSendPeerSign = ''
                    self.s_needSendCTUnitArray = []
                self.s_ExecMutex.release()
        return bRetValue

    # 关闭管套
    def Vilu_Close(self):
        bSendClose = True
        # 如果已经连接，发送关闭数据包
        if (bSendClose):
            # 构造关闭数据包，发送远端
            CTYLB_Log.ShowLog(0, 'HLSockMang', 'send sock close to peer.[%d]' % (self.s_iLocalPort))
            self.Exec_SendClose_To_RemotePeer()
        # 设置状态
        CTYBot_SockUnit_Base.Vilu_Close(self)

    # 发送ack到远端
    def Exec_SendAck_To_RemotePeer(self):
        # 回应ACK,
        ackCTUnit = CTYBot_CTUnit_HLSockSession()
        ackCTUnit.SetTypeConnectAck( self)
        self.Exec_SendCTUnit_AdjustContent( ackCTUnit, 0)
        pass

    # 接收到SYN_ack数据单元, 连接成功
    def HandleSYNACKSockArriveCTUnit(self, strFromName, hlSockSessionCTUnit):
        self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Connected

    # 处理接收到数据包
    def Vilu_RecvDataCTUnit(self, hlSockSessionCTUnit):
        if (self.s_ExecMutex.acquire()):
            self.s_recvCTUnitArray.extend( hlSockSessionCTUnit.s_subCTUnitArray)
            self.s_strLastSendPeerSign = hlSockSessionCTUnit.s_strUniqueSign
            self.s_ExecMutex.release()
        pass
    pass


# tylb－p2p的 管套单元实现, 主动发，维护发送队列。但被动接受。对方发送回复了，我才会接收到数据包
# start by sk. 170304
class CTYBot_Connect_SockUnit(CTYBot_SockUnit_Base):
    s_g_iSyncCheck_EachTimeDiff = 1  # 每秒进行检查同步操作
    s_g_iSyncCheck_MaxForceCheck = 1200  # 最大检查时间，20min

    # 管套初始化
    def __init__(self, parentBotExecFrame, iSockIndex):
        CTYBot_SockUnit_Base.__init__(self, parentBotExecFrame, iSockIndex)
        self.s_iType = CTYBot_SockUnit_Base.s_g_iType_Connect  # 管套类型
        self.s_origRecvLowLevel_CTUnitArray = []  # 接收到的底层队列数据
        self.s_recvCTUnitArray = []  # 接收缓冲队列
        self.s_needSendCTUnitArray = []  # 发送缓冲队列

        self.s_simuSyncComuCheck = CTylb_SockSync_Checker(CTYBot_Connect_SockUnit.s_g_iSyncCheck_EachTimeDiff,
                                                CTYBot_Connect_SockUnit.s_g_iSyncCheck_MaxForceCheck)
        pass

    # 是否已经连接成功
    def IsConnected(self):
        bRetValue = False
        if( self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connected):
            bRetValue = True
        return bRetValue

    # 提交，调度发送,主动提交
    def Mg_Conct_PromptSend(self, cTUnitArray):
        if (self.s_ExecMutex.acquire()):
            self.s_needSendCTUnitArray.extend(cTUnitArray)
            self.s_ExecMutex.release()
        pass

    # 获取接收到的内容队列，只有提交后，才能进行接收
    def Mg_Conct_PassiveRecv(self):
        retRecvCTUnitArray = []
        if( self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connected):
            if (self.s_ExecMutex.acquire()):
                if (len(self.s_recvCTUnitArray) > 0):
                    retRecvCTUnitArray = self.s_recvCTUnitArray
                    self.s_recvCTUnitArray = []
                self.s_ExecMutex.release()
        return retRecvCTUnitArray

    # 开始连接
    def Connect(self, strRemoteID, iRemotePort):
        self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_StartConnect  # 状态
        self.s_strRemoteID = strRemoteID
        self.s_iRemotePort = iRemotePort
        pass

    # 调度进行时间检查，判断是否需要关闭，和需要发送的数据包
    def Vilu_Schedule_TimerCheck(self):
        bRetValue = CTYBot_SockUnit_Base.Vilu_Schedule_TimerCheck( self)

        bCanCheckSend = False

        if (self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_StartConnect):
            # 发送连接的数据包-SYN
            ackCTUnit = CTYBot_CTUnit_HLSockSession()
            ackCTUnit.SetTypeConnect( self)
            self.Exec_SendCTUnit_AdjustContent(ackCTUnit, 0)
            self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Connecting
            pass
        elif (self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connecting):
            # 等待连接回应
            pass
        elif (self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connected):
            bCanCheckSend = True
            pass

        if (bCanCheckSend):
            # 如果有数据，检查可否发送。
            if (self.s_ExecMutex.acquire()):
                if (len(self.s_needSendCTUnitArray) > 0):
                    # 提交数据进行发送,发送后清空
                    if (not self.s_simuSyncComuCheck.IsBusy()):
                        bRetValue = True
                        # 如果单元未同步，则发送同步单元。同时，把数据发送出去 sendCTUnitArray, strRemoteHostID, iLocalPort, iRemotePort):
                        self.s_simuSyncComuCheck.ScheduleSendCTUnitArray(self.s_parentBotExecFrame, self.s_needSendCTUnitArray, self)
                        self.s_needSendCTUnitArray = []
                self.s_ExecMutex.release()
        # 如果无可用单元，则等待
        return bRetValue

    # 关闭管套
    def Vilu_Close(self):
        bSendClose = False
        if (self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connecting):
            bSendClose = True
        elif (self.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connected):
            bSendClose = True
        # 如果已经连接，发送关闭数据包
        if (bSendClose):
            # 构造关闭数据包，发送远端
            CTYLB_Log.ShowLog(0, 'HLSockMang', 'connect sock send closed.[%d]' % (self.s_iLocalPort))
            self.Exec_SendClose_To_RemotePeer()
            pass
        CTYBot_SockUnit_Base.Vilu_Close(self)

    # 接收到ack数据单元
    def HandleACKSockArriveCTUnit(self, strFromName, hlSockSessionCTUnit):
        self.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Connected
        self.s_iPeerSequence = hlSockSessionCTUnit.s_iMySeq
        # 回应SYNACK
        ackCTUnit = CTYBot_CTUnit_HLSockSession()
        ackCTUnit.SetTypeConnectSYNAck( self)
        self.Exec_SendCTUnit_AdjustContent( ackCTUnit, 0)
        pass

    # 处理接收到数据包
    def Vilu_RecvDataCTUnit(self, hlSockSessionCTUnit):
        # 接收到数据包，把自己的标志设成可发送。
        if( hlSockSessionCTUnit.s_strPeerSign == self.s_simuSyncComuCheck.s_strLastExecQueryUnqiueSign):
            self.s_simuSyncComuCheck.RecvReplyResetSession()
            if (self.s_ExecMutex.acquire()):
                self.s_recvCTUnitArray.extend(hlSockSessionCTUnit.s_subCTUnitArray)
                self.s_ExecMutex.release()
            pass
        pass
    pass

# tylb－p2p的 管套的管理
# start by sk. 170304
class CTYBot_HL_Sock_Mang:
    s_g_iLastMaxSockValue = 1000    # 上次最大管套值

    def __init__(self, parentBotExecFrame):
        self.s_sockArray = []   # 管套队列，为 CTYBot_SockUnit 单元
        self.s_parentBotExecFrame = parentBotExecFrame  # 父bot执行框架
        self.s_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_iLastLocalPortValue = CTYBot_HL_Sock_Mang.s_g_iLastMaxSockValue   # 最后的本地管套
        self.s_iLastSockValueIndex = 1  # 管套值索引
        pass

    # 获得可用的索引值
    def __GetValidSockIndex(self):
        iRetIndexValue = self.s_iLastSockValueIndex
        self.s_iLastSockValueIndex += 1
        return iRetIndexValue

    # 创建监听管套
    def CreateListenSock(self, iListenPort):
        # 搜索以前是否存在
        retNewSock = self.__SearchSockByTypeValue( CTYBot_SockUnit_Base.s_g_iType_Listen, '', iListenPort, 0)
        if( not retNewSock):
            retNewSock = CTYBot_Listen_SockUnit( self.s_parentBotExecFrame, self.__GetValidSockIndex())
            retNewSock.Listen( iListenPort)
            if (self.s_ExecMutex.acquire()):
                self.s_sockArray.append( retNewSock)
                self.s_ExecMutex.release()
        return retNewSock.s_iSockIndex

    # 根据索引值，获得管套单元
    # start by sk. 170306
    def __GetSockByIndex(self, iSockIndex):
        retSockUnit = None
        # 加入到队列
        if (self.s_ExecMutex.acquire()):
            for eachUnit in self.s_sockArray:
                if( eachUnit.s_iSockIndex == iSockIndex):
                    retSockUnit = eachUnit
                    break
            self.s_ExecMutex.release()
        return retSockUnit

    # 检查是否有新的管套到达
    def __AcceptListenNewSock(self, listenSock):
        if( listenSock and listenSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Listen):
            retNewSock = listenSock.PopNewAcceptSock()
        else:
            retNewSock = None

        if( retNewSock):
            # 搜索以前相同端口单元，把以前的删除
            while(True):
                existSock = self.__SearchSockByTypeValue( CTYBot_SockUnit_Base.s_g_iType_Accept, retNewSock.s_strRemoteID,
                                                          retNewSock.s_iLocalPort, retNewSock.s_iRemotePort)
                if( existSock):
                    if (self.s_ExecMutex.acquire()):
                        self.s_sockArray.remove( existSock)
                        self.s_ExecMutex.release()
                else:
                    break
            # 加入到队列
            if (self.s_ExecMutex.acquire()):
                self.s_sockArray.append(retNewSock)
                self.s_ExecMutex.release()
            # 发送确认回应
            retNewSock.Exec_SendAck_To_RemotePeer()
        return retNewSock

    def CreateConnectSock(self, strRemoteID, iRemotePort):
        # 搜索以前是否存在
        retNewSock = CTYBot_Connect_SockUnit( self.s_parentBotExecFrame, self.__GetValidSockIndex())
        self.s_iLastLocalPortValue += 1
        retNewSock.s_iLocalPort = self.s_iLastLocalPortValue
        if (self.s_ExecMutex.acquire()):
            self.s_sockArray.append( retNewSock)
            self.s_ExecMutex.release()
        retNewSock.Connect( strRemoteID, iRemotePort)

        return retNewSock.s_iSockIndex

    # 提交数据，进行发送
    # start by sk. 170306
    def PassiveRecv_From_ConnectSock(self, iConnectSockIndex):
        retCTUnitArray = []
        bSockExist = False
        connectSock = self.__GetSockByIndex( iConnectSockIndex)
        if( connectSock):
            bSockExist = True
            retCTUnitArray = connectSock.Mg_Conct_PassiveRecv()
        return bSockExist, retCTUnitArray

    # 提交数据，进行发送
    # start by sk. 170306
    def PromptDataSend_To_ConnectSock(self, iConnectSockIndex, dataCTUnitArray):
        connectSock = self.__GetSockByIndex( iConnectSockIndex)
        if( connectSock):
            connectSock.Mg_Conct_PromptSend( dataCTUnitArray)
        pass

    # 对接收管套，进行主动接收操作
    # start by sk. 170306
    def ActiveRecv_From_AcceptSock(self, iAcceptSockIndex):
        retAcceptCTUnitArray = None
        bSockExist = False
        acceptSock = self.__GetSockByIndex( iAcceptSockIndex)
        if( acceptSock):
            bSockExist = True
            retAcceptCTUnitArray = acceptSock.Mg_Acpt_ActiveRecv()
        return bSockExist, retAcceptCTUnitArray

    # 对接受管套，进行提交后的等待
    # start by sk. 170306
    def PassiveSend_To_AcceptSock(self, iAcceptSockIndex, dataCTUnitArray):
        acceptSock = self.__GetSockByIndex( iAcceptSockIndex)
        if( acceptSock):
            acceptSock.Mg_Acpt_PassiveSend( dataCTUnitArray)
        pass

    def CloseSockByIndex(self, iSockIndex):
        destCloseSock = self.__GetSockByIndex( iSockIndex)
        if( destCloseSock):
            # 搜索单元。
            if (self.s_ExecMutex.acquire()):
                if( destCloseSock in self.s_sockArray):
                    destCloseSock.Vilu_Close()
                    CTYLB_Log.ShowLog(0, 'HLSockMang', 'sock closed.[%d]' % (iSockIndex))
                else:
                    CTYLB_Log.ShowLog(1, 'HLSockMang', 'sock found but not exist.[%d]' % (iSockIndex))
                self.s_ExecMutex.release()
        else:
            CTYLB_Log.ShowLog(1, 'HLSockMang', 'Close not exist sock.[%d]' % (iSockIndex))
        pass

    # 搜索某个类型值的管套单元
    def __SearchSockByTypeValue(self, iSockType, strRemoteID, iLocalPort, iPeerPort, bCheckSeq=False, iMySeq=0, iPeerSeq=0):
        retSockUnit = None
        if (self.s_ExecMutex.acquire()):
            for eachSock in self.s_sockArray:
                if( (eachSock.s_iType == iSockType) and (eachSock.s_iLocalPort == iLocalPort)):
                    if( (eachSock.s_iRemotePort == iPeerPort) and ( eachSock.s_strRemoteID == strRemoteID)):
                        bUnitValid = False
                        if( iSockType == CTYBot_SockUnit_Base.s_g_iType_Listen):
                            bUnitValid = True
                        elif( bCheckSeq == False):
                            bUnitValid = True
                        else:
                            if( (eachSock.s_iSelfSequence == iMySeq) and ( eachSock.s_iPeerSequence == iPeerSeq)):
                                bUnitValid = True
                        # 检查顺序号符合。如果端口值相同，但顺序号不同，也返回false.
                        if( bUnitValid):
                            retSockUnit = eachSock
                        break
            self.s_ExecMutex.release()
        return retSockUnit

    # 获得管套对应的名字
    def GetSockPeerAddr(self, iSockIndex):
        strRetPeerName = ''
        iRetPeerPort = 0
        destSock = self.__GetSockByIndex( iSockIndex)
        if( destSock):
            strRetPeerName = destSock.s_strRemoteID
            iRetPeerPort = destSock.s_iRemotePort
            pass
        return strRetPeerName, iRetPeerPort

    # 获得管套是否链接成功状态
    # start by sk. 170404
    def IsSockConnectSuccess(self, iSockIndex):
        bRetValue = False
        destSock = self.__GetSockByIndex( iSockIndex)
        if( destSock):
            if( destSock.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Connected):   # 状态
                bRetValue = True
        return bRetValue

    # 获得管套是否关闭
    # start by sk. 170404
    def IsSockClosed(self, iSockIndex):
        bRetValue = False
        destSock = self.__GetSockByIndex( iSockIndex)
        if( destSock):
            if( destSock.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Closed):   # 状态
                bRetValue = True
        else:
            bRetValue = True
        return bRetValue


    # 外部获取 新到达的管套
    def ExAcceptNewListenArriveSock(self, iListenSockIndex):
        listenSock = self.__GetSockByIndex( iListenSockIndex)
        iRetNewAcceptSockIndex = 0
        if( listenSock):
            strNewPeerID, iNewPort = listenSock.PopNewArriveAcceptPeerPort()
            if( strNewPeerID and iNewPort):
                newAcceptSock = self.__SearchSockByTypeValue(CTYBot_SockUnit_Base.s_g_iType_Accept, strNewPeerID,
                                                                   listenSock.s_iLocalPort, iNewPort)
                if( newAcceptSock):
                    iRetNewAcceptSockIndex = newAcceptSock.s_iSockIndex
        return iRetNewAcceptSockIndex

    # 根据端口值，和远程地址，搜索已经连接的管套
    def __SearchConnectedSock(self, bstrRemoteID, iLocalPort, iPeerPort, bCheckSeq, iMySeq, iPeerSeq):
        connectOrAcceptSock = self.__SearchSockByTypeValue(CTYBot_SockUnit_Base.s_g_iType_Connect, bstrRemoteID,
                                                           iLocalPort, iPeerPort, bCheckSeq, iMySeq, iPeerSeq)
        if (not connectOrAcceptSock):
            connectOrAcceptSock = self.__SearchSockByTypeValue(CTYBot_SockUnit_Base.s_g_iType_Accept, bstrRemoteID,
                                                               iLocalPort, iPeerPort, bCheckSeq, iMySeq, iPeerSeq)
        return connectOrAcceptSock

    # 调度时间进行检查
    def TimerCheck(self):
        bRetValue = False
        for eachSock in self.s_sockArray:
            if( eachSock.Vilu_Schedule_TimerCheck()):
                bRetValue = True

        if (self.s_ExecMutex.acquire()):
            for eachSock in self.s_sockArray:
                # 是否已经关闭
                if( eachSock.s_iStatus == CTYBot_SockUnit_Base.s_g_iStatus_Closed):
                    self.s_sockArray.remove( eachSock)
                    break
            self.s_ExecMutex.release()
        return bRetValue

    # 自身全部退出
    def SelfMangAllQuit(self):
        if (self.s_ExecMutex.acquire()):
            for eachSock in self.s_sockArray:
                eachSock.Vilu_Close()
            self.s_ExecMutex.release()

    def CheckAcceptNewSock(self, listenSockUnit):
        newAcceptSock = None
        # 是否有新连接到达
        if (listenSockUnit.s_iType == CTYBot_SockUnit_Base.s_g_iType_Listen):
            newAcceptSock = listenSockUnit.PopNewAcceptSock()
            if( newAcceptSock):
                if (self.s_ExecMutex.acquire()):
                    self.s_sockArray.append( newAcceptSock)
                    self.s_ExecMutex.release()
        return newAcceptSock

    # 接收到数据包单元的回调
    # 如果管套单元不在我的队列中，那么，发送关闭消息
    # 接收？
    def HandleRecvHLSessionCTUnit(self, strFromName, hlSockSessionCTUnit):
        bNeedSendPeerReset = False
        iSendResetAdjustPeerAck = 0  # 发送重置包时，调整ack的值

        hlSockSessionCTUnit.ShowInfo( 'recv', strFromName)
        if( hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_SYN):  # 握手，开始连接
            # 监听的管套存在？
            listenSock = self.__SearchSockByTypeValue( CTYBot_SockUnit_Base.s_g_iType_Listen, '', hlSockSessionCTUnit.s_iPeerPort,
                                                       0, False, 0)
            if( listenSock):
                newAcceptSock = listenSock.HandleNewSockArriveCTUnit( strFromName, hlSockSessionCTUnit, self.s_iLastSockValueIndex)
                if( newAcceptSock):
                    self.__AcceptListenNewSock( listenSock)
                    # 增加新的索引值
                    self.__GetValidSockIndex()
            else:
                bNeedSendPeerReset = True
        elif (hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_ACK):   # 连接回应，成功连接
            # 此时，connect单元发syn后，peer的ack＝0，所以，接收到ack包含peer有效ack，此时必须＝0，才能搜索到成功的管套单元
            connectSock = self.__SearchSockByTypeValue( CTYBot_SockUnit_Base.s_g_iType_Connect, strFromName,
                                                        hlSockSessionCTUnit.s_iPeerPort, hlSockSessionCTUnit.s_iSelfPort,
                                                        True, hlSockSessionCTUnit.s_iPeerSeq, 0)
            if( connectSock):
                connectSock.HandleACKSockArriveCTUnit( strFromName, hlSockSessionCTUnit)
            else:
                bNeedSendPeerReset = True
        elif (hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_SYNACK):   # 连接回应，成功连接
            acceptSock = self.__SearchSockByTypeValue( CTYBot_SockUnit_Base.s_g_iType_Accept, strFromName,
                                                       hlSockSessionCTUnit.s_iPeerPort, hlSockSessionCTUnit.s_iSelfPort,
                                                       True, hlSockSessionCTUnit.s_iPeerSeq, hlSockSessionCTUnit.s_iMySeq)
            if( acceptSock and acceptSock.Exec_Validate_Update_Recv_PeerSeq(hlSockSessionCTUnit.s_iMySeq, 0)):
                acceptSock.HandleSYNACKSockArriveCTUnit(strFromName, hlSockSessionCTUnit)
            else:
                bNeedSendPeerReset = True
        elif ( (hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_COMMON) or
                   (hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_DATA_CTUnitArray) ):  # 普通数据
            connectOrAcceptSock = self.__SearchConnectedSock( strFromName, hlSockSessionCTUnit.s_iPeerPort,
                                                              hlSockSessionCTUnit.s_iSelfPort,
                                                              True, hlSockSessionCTUnit.s_iPeerSeq, hlSockSessionCTUnit.s_iMySeq)
            if( connectOrAcceptSock and connectOrAcceptSock.Exec_Validate_Update_Recv_PeerSeq(hlSockSessionCTUnit.s_iMySeq)):
                connectOrAcceptSock.Vilu_RecvDataCTUnit( hlSockSessionCTUnit)
            else:
                iSendResetAdjustPeerAck = 1
                bNeedSendPeerReset = True
            pass
        elif (hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_CLOSE):   # 管套关闭
            closeSock = self.__SearchConnectedSock( strFromName, hlSockSessionCTUnit.s_iPeerPort,
                                                    hlSockSessionCTUnit.s_iSelfPort, True,
                                                    hlSockSessionCTUnit.s_iPeerSeq, hlSockSessionCTUnit.s_iMySeq)
            if( closeSock and closeSock.Exec_Validate_Update_Recv_PeerSeq(hlSockSessionCTUnit.s_iMySeq, 0)):
                closeSock.s_iStatus = CTYBot_SockUnit_Base.s_g_iStatus_Closed  # 直接设置状态为关闭
            pass
        elif (hlSockSessionCTUnit.s_iPacketType == CTYBot_CTUnit_HLSockSession.s_g_iType_NOP):   # 空数据包，忽略
            pass

        # 数据包对应的不存在，发送
        if( bNeedSendPeerReset):
            ackCTUnit = CTYBot_CTUnit_HLSockSession()
            ackCTUnit.Ex_SetCloseFromCTUnit( hlSockSessionCTUnit, iSendResetAdjustPeerAck)
            ackCTUnit.ShowInfo('send', strFromName)
            self.s_parentBotExecFrame.SendCTUnitToUser( strFromName, ackCTUnit)
            pass
        pass


    # 处理系统通知
    # start by sk. 170505
    def Handle_SystemNotify_ClientStatus(self, iSystemNotifyClientStatus, strDestClientName):
        # 在 Tylb_Support_Client.py的 CTYLB_MidBalance_InOutBuffMang 中定义。
        if( iSystemNotifyClientStatus == 0):
            # client restart
            # 搜索所有connect和accept的管套。如果是，则设置关闭标志
            if (self.s_ExecMutex.acquire()):
                for eachSock in self.s_sockArray:
                    if ((eachSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Accept) or
                            (eachSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Connect)):
                        if( eachSock.s_strRemoteID == strDestClientName):
                            eachSock.Vilu_Close()
                            CTYLB_Log.ShowLog(0, u'HLSockMang', u'Client Restart, sock:%d->%s:%d closed' %
                                              (eachSock.s_iLocalPort, strDestClientName, eachSock.s_iRemotePort))
                self.s_ExecMutex.release()
            pass
        elif( iSystemNotifyClientStatus == 1): # client init startup
            # 搜索所有connect和accept的管套。如果是，则设置关闭标志
            if (self.s_ExecMutex.acquire()):
                for eachSock in self.s_sockArray:
                    if ((eachSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Accept) or
                            (eachSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Connect)):
                        if( eachSock.s_strRemoteID == strDestClientName):
                            eachSock.Vilu_Close()
                            CTYLB_Log.ShowLog(0, u'HLSockMang', u'Client Init-StartUP, sock:%d->%s:%d closed' %
                                              (eachSock.s_iLocalPort, strDestClientName, eachSock.s_iPeerPort))
                self.s_ExecMutex.release()
            pass
        pass


    # 处理系统通知，服务器重新启动
    # start by sk. 180318
    def Handle_SystemNotify_PeerServerRestart(self):
        # 获得hlsock列表，提交发送nop的数据包
        # 在 Tylb_Support_Client.py的 CTYLB_MidBalance_InOutBuffMang 中定义。
        # 搜索所有connect和accept的管套。如果是，则设置关闭标志
        if (self.s_ExecMutex.acquire()):
            for eachSock in self.s_sockArray:
                if ((eachSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Accept) or
                        (eachSock.s_iType == CTYBot_SockUnit_Base.s_g_iType_Connect)):
                    eachSock.Exec_SendNop_To_RemotePeer()
            self.s_ExecMutex.release()
        pass
    pass

    pass
