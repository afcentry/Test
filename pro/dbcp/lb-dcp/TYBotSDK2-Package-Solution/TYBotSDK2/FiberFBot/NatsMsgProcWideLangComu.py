# NatsMsgProcWideLangComu.py
# 采用Nats消息队列，进行进程间通信，实现跨语言之间的通信。
# start by sk. 180404

import asyncio
import json
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrNoServers
import threading, time, queue
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CTYLB_MainSys_MiscFunc


class CAsyncNats_MultiLang_Proc_Comu:
    # 初始化类
    def __init__(self, strNATSServerAddr, strSelfRecvName):
        self.s_strNatsServerAddr = strNATSServerAddr
        self.s_strSelfRecvName = strSelfRecvName
        self.s_globalQueue = queue.Queue()
        self.s_natsExecThread = CNatsExec_Thread(self.s_globalQueue, self.s_strNatsServerAddr, self.s_strSelfRecvName)
        pass

    def StartComu(self):
        self.s_globalQueue.put(0)
        self.s_natsExecThread.setDaemon(True)
        self.s_natsExecThread.start()
        pass

    def AddContentToSend(self, strDestSendToName, iMsgType, strContent):
        self.s_natsExecThread.Safe_AddSendUnit(strDestSendToName, iMsgType, strContent)
        pass

    def CheckRecvMsg(self):
        recvMsgArray = []
        while (True):
            recvUnit = CNatsExec_Thread.Safe_PopRecvUnit()
            if (recvUnit):
                recvMsgArray.append(recvUnit)
            else:
                break
        return recvMsgArray


# 多语言平台线程通信的发送接收单元
class CMPL_ProcComu_SendRecvUnit:
    def __init__(self, strPeerMsgName, iMsgType, strMsgContent):
        self.s_strPeerMsgName = strPeerMsgName
        self.s_iMsgType = iMsgType
        self.s_strMsgContent = strMsgContent


g_listRecvMsg = []  # 接收到的全局消息 CMPL_ProcComu_SendRecvUnit
g_recvMsgExecMutex = threading.Lock()  # 线程执行同步锁


# 主机执行线程管理
# start by sk. 170213
class CNatsExec_Thread(threading.Thread):
    s_g_iFree = 0
    s_g_iPrepareRun = 1
    s_g_iRunning = 2

    # s_ExecMutex = None  # 线程执行同步锁

    def __init__(self, paramQueue, strNatsServerAddr, strPeerComuName):
        threading.Thread.__init__(self)
        self.s_strNatsServerAddr = strNatsServerAddr
        self.s_strPeerComuName = strPeerComuName
        self.s_MyQueue = paramQueue

        self.s_needSendUnitArray = []  # 需要发送的消息单元 CMPL_ProcComu_SendRecvUnit
        self.s_recvProcComuUnitArray = []  # 需要接收的消息单元 CMPL_ProcComu_SendRecvUnit

        self.s_bThreadRunning = True

        self.s_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_iCurStatus = 0  # 空闲

        self.s_NatsEventRoot = asyncio.get_event_loop()

        if (self.s_ExecMutex.acquire()):
            self.s_ExecMutex.release()

    def __del__(self):
        self.s_bThreadRunning = False
        pass

    s_g_key_Msg = 'Msg'
    s_g_key_Type = 'Type'
    s_g_key_FromSender = 'FromSender'

    # 异步运行发送和接收
    @staticmethod
    async def AsyncSendRecvRun(loopEventIO, natsExecThread, strNatsServerAddr, strSelfRecvName):
        nats = NATS()
        await nats.connect(io_loop=loopEventIO, servers=[strNatsServerAddr])

        sid = await nats.subscribe_async(strSelfRecvName, cb=CNatsExec_Thread.AsyncRecvMsg_Handler)

        while (natsExecThread.s_bThreadRunning):
            bMsgBusy = False

            needSendMsg = natsExecThread.Safe_PopNeedSendUnit()
            if (needSendMsg):
                bReExecConnect = False
                # 获得需要发送的单元消息
                msg = {}

                # strBase64 = CTYLB_MainSys_MiscFunc.SafeConvertStrToBase64(needSendMsg.s_strMsgContent)
                msg[CNatsExec_Thread.s_g_key_Msg] = needSendMsg.s_strMsgContent
                msg[CNatsExec_Thread.s_g_key_Type] = needSendMsg.s_iMsgType
                msg[CNatsExec_Thread.s_g_key_FromSender] = strSelfRecvName

                strExContent = json.dumps(msg, ensure_ascii=False)
                bytesExContent = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strExContent)

                while(True):

                    try:
                        await nats.publish(needSendMsg.s_strPeerMsgName, bytesExContent)
                        break
                    except:
                        if(nats.is_closed):
                            bReExecConnect=True

                    if(bReExecConnect):
                        CTYLB_Log.ShowLog(0, "Reconnect", "Nats Connect lost. reconnecting...")
                        bReExecConnect=False
                        await nats.connect(io_loop=loopEventIO, servers=[strNatsServerAddr])

                bMsgBusy = True

            if (not bMsgBusy):
                await asyncio.sleep(0.001)

        await asyncio.sleep(1, loop=loopEventIO)
        await nats.close()

    # 线程接收的函数
    @staticmethod
    async def AsyncRecvMsg_Handler(natsMsg):
        strFromPeerName = natsMsg.subject
        strJsonData = natsMsg.data.decode()

        dictRecvData = json.loads(strJsonData)
        try:
            iMsgType = int(dictRecvData[CNatsExec_Thread.s_g_key_Type])
            strOrigBaseData = dictRecvData[CNatsExec_Thread.s_g_key_Msg]
            strPeerSenderName = dictRecvData[CNatsExec_Thread.s_g_key_FromSender]
            #strOrigData = CTYLB_MainSys_MiscFunc.SafeRestoreFromBase64(strOrigBaseData)

            CNatsExec_Thread.Safe_AddRecvUnit(strPeerSenderName, iMsgType, strOrigBaseData)
        except Exception as e:
            CTYLB_Log.ShowLog(1, "接收异步nats消息解释错误", str(e))

    # 运行
    def run(self):
        self.s_MyQueue.get()

        loopEventIO = asyncio.new_event_loop()
        asyncio.set_event_loop(loopEventIO)

        loopEventIO = asyncio.get_event_loop()
        loopEventIO.run_until_complete(CNatsExec_Thread.AsyncSendRecvRun(loopEventIO, self, self.s_strNatsServerAddr,
                                                                         self.s_strPeerComuName))

        self.s_MyQueue.task_done()  # finish queue unit
        pass

    # 安全停止
    def Safe_Stop(self):
        if (self.s_ExecMutex.acquire()):
            self.s_bThreadRunning = False
            self.s_ExecMutex.release()

    # 安全 获取状态
    def Safe_GetStatus(self):
        iRetValue = 0
        if (self.s_ExecMutex.acquire()):
            iRetValue = self.s_iCurStatus
            self.s_ExecMutex.release()
        return iRetValue

    # 安全 获取需要发送的单元
    def Safe_PopNeedSendUnit(self):
        retUnit = None
        if (self.s_ExecMutex.acquire()):
            if (len(self.s_needSendUnitArray) > 0):
                retUnit = self.s_needSendUnitArray.pop(0)
            self.s_ExecMutex.release()
        return retUnit

    # 安全 增加单元进行发送
    def Safe_AddSendUnit(self, strDestPeerName, iMsgType, strMsgContent):
        # 此处进行base64的编码
        strExBase64Content = CTYLB_MainSys_MiscFunc.SafeConvertStrToBase64(strMsgContent)

        newUnit = CMPL_ProcComu_SendRecvUnit(strDestPeerName, iMsgType, strExBase64Content)
        if (self.s_ExecMutex.acquire()):
            self.s_needSendUnitArray.append(newUnit)
            self.s_ExecMutex.release()

    # 安全 获取需要发送的单元
    @staticmethod
    def Safe_PopRecvUnit():
        retUnit = None
        if (g_recvMsgExecMutex.acquire()):
              if (len(g_listRecvMsg) > 0):
                retUnit = g_listRecvMsg.pop(0)
              g_recvMsgExecMutex.release()
        return retUnit

    # 安全 增加单元进行发送
    @staticmethod
    def Safe_AddRecvUnit(strFromPeerName, iMsgType, strMsgBase64Content):
        # 此处进行base64的恢复
        strRestoreOrigContent = CTYLB_MainSys_MiscFunc.SafeRestoreFromBase64(strMsgBase64Content)

        newUnit = CMPL_ProcComu_SendRecvUnit(strFromPeerName, iMsgType, strRestoreOrigContent)
        if (g_recvMsgExecMutex.acquire()):
            g_listRecvMsg.append(newUnit)
            g_recvMsgExecMutex.release()

    @staticmethod
    def ShowLog(iWarnLevel, strMsg):
        CTYLB_Log.ShowLog(iWarnLevel, 'Connect Thread', strMsg)
