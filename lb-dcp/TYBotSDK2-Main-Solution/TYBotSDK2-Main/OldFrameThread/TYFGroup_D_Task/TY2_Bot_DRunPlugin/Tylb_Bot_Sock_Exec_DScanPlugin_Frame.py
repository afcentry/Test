# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Sock_Exec_DScanPlugin_Frame.py 主机实现模块，实现连接任务中心，接受调度，提交结果等
#
# start by sk. 170212.
# restart by sk. 170309
# update by sk. 170403. into OpSession_ConnectSock

import signal
from datetime import datetime
import os

from TYBotSDK2.BotBase.Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock,\
    CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignWebNameBlock, CTYBot_CTUnit_CommonData, CTYLB_TaskReg_Cmd_BaseDef,\
    CTYBot_CTUnit_TaskRegCenter_ReportResult_V2, CTYBot_CTUnit_TaskRegCenter_ReportMyStatus
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.P2PClient.Tylb_p2p_ExCall_SubClient import CTYLB_P2P_ContentUnit_Base_bytes
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from LessTYBot_2D_PluginScan import CTYBot_ExecPlugin_Each_CallBack_RunParam, CTYBot_ExecPlugin_GetSupportIDArray
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
import threading
import time
import queue

g_execTYLB_Bot_DExec_HostReal_Frame = None   # 执行 分布插件的 主机机器人实现
g_hostExecPluginBot = None
g_bSysRunning = True
g_strProgName = u'TYBot_DRun_Plugin'

# 线程运行参数单元
# start by sk. 170213
class CThreadRunParamUnit:
    # s_assignTaskParam = None  # CTYBot_CTUnit_TaskRegCenter_AssignTaskParam

    def __init__(self, bstrFromName, assignTaskUnit):
        bstrFromName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrFromName)
        self.s_bstrFromName = bstrFromName
        self.s_assignTaskParam = assignTaskUnit

# 线程运行结果单元
# start by sk. 170213
class CThreadRunResultUnit:
    s_bstrFromName = b''
    s_runResultUnit = None  # CTYBot_CTUnit_TaskRegCenter_ReportResult

    def __init__(self, bstrFromSenderName, resultUnit):
        bstrFromSenderName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrFromSenderName)
        self.s_bstrFromName = bstrFromSenderName
        self.s_runResultUnit = resultUnit

# 主机执行线程管理
# start by sk. 170213
class CTYLB_HostExec_V2_Thread(threading.Thread):
    # s_MyQueue = None
    # s_iMyIndex = 0
    # s_bThreadRunning = True
    # s_runParamUnit = ''  # 运行参数 CThreadRunParamUnit
    # s_runResult = None  # 运行结果 CThreadRunResultUnit
    # s_iCurStatus = 0  # 状态：空闲，运行，等待取结果
    # threadPluginExecEachCallBackFunc = None  # 任务回调函数：trResult = CTYBot_ExecPlugin_CallBack_RunParam( threadRunParamUnit)
    # s_p2pClientExec = ''  # p2p执行单元

    s_g_iFree = 0
    s_g_iPrepareRun = 1
    s_g_iRunning = 2

    # s_ExecMutex = None  # 线程执行同步锁

    def __init__(self, bstrSelfIDName, ustrThreadName, paramQueue, iIndex, threadPluginExecEachCallBackFunc):
        bstrSelfIDName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrSelfIDName)
        ustrThreadName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrThreadName)

        threading.Thread.__init__(self, name=ustrThreadName)
        self.s_MyQueue = paramQueue
        self.s_iMyIndex = iIndex

        self.g_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_bThreadRunning = True

        self.s_runParamUnit = None  # 运行参数
        self.s_runResult = None  # 运行结果
        self.s_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_iCurStatus = 0  # 空闲
        self.s_pluginExecWebCallBackFunc = threadPluginExecEachCallBackFunc
        self.s_bstrSelfIDName = bstrSelfIDName
        self.s_resultMiddleUnitArray = []   # 结果单元队列 CThreadRunResultUnit

        if (self.s_ExecMutex.acquire()):
            self.s_ExecMutex.release()

    def __del__(self):
        self.s_bThreadRunning = False
        pass

    # 运行
    def run(self):
        self.s_MyQueue.get()

        lastSendResultTime = datetime.now()  # 上次发送时间
        iSendWaitDiffTime = 30  # 每30秒发送一次
        while (self.s_bThreadRunning):
            iCurStatus = self.Safe_GetStatus()
            if (iCurStatus == CTYLB_HostExec_V2_Thread.s_g_iPrepareRun):
                # 调度参数进行运行
                self.Safe_SetStatus(CTYLB_HostExec_V2_Thread.s_g_iRunning)

                # 发送开始运行的消息
                bstrOrigParamUniqSign = self.s_runParamUnit.s_assignTaskParam.s_bstrUniqueSign
                replyCommUnit = CTYBot_CTUnit_CommonData()
                replyCommUnit.SetIntData(CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Start_Run)
                replyCommUnit.SetParam(bstrOrigParamUniqSign, self.s_bstrSelfIDName)
                self.Safe_AddMiddleResultData( self.s_runParamUnit.s_bstrFromName, replyCommUnit)

                # 设置参数标识
                reportResultV2 = CTYBot_CTUnit_TaskRegCenter_ReportResult_V2()
                reportResultV2.s_bstrOrigTaskUniqueSign = bstrOrigParamUniqSign
                # 发送每个运行结果
                paramCTUnit = self.s_runParamUnit.s_assignTaskParam
                if (paramCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                    if (paramCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock):
                        if (paramCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock):
                            iRunPluginID = paramCTUnit.s_iRunPluginID
                            bstrRunHostNameArray = paramCTUnit.s_bstrDomainNameArray

                            for bstrEachHost in bstrRunHostNameArray:
                                ustrEachHost = CTYLB_MainSys_MiscFunc.SafeGetUnicode(bstrEachHost)
                                iReplyPluginID, bstrRunContent = 0, b''
                                if (self.s_pluginExecWebCallBackFunc):
                                    try:
                                        iReplyPluginID, ustrRunContent = self.s_pluginExecWebCallBackFunc( iRunPluginID, ustrEachHost)
                                        bstrRunContent = CTYLB_MainSys_MiscFunc.SafeGetUTF8(ustrRunContent)
                                    except Exception as e:
                                        ustrMsg =  u'Run Plugin [%s] Error.[%s]' % (ustrEachHost, str(e))
                                        CTYLB_Log.ShowLog(1, u'Running Plugin %d'%(iRunPluginID), ustrMsg)
                                        pass

                                # 加入到队列，进行输出
                                bstrFixRunContent = CTYLB_P2P_ContentUnit_Base_bytes.SafeConvertStrToUTF8_Base64(bstrRunContent)
                                reportResultV2.AddSubResultUnit( iReplyPluginID, bstrEachHost, bstrFixRunContent)
                                curTime = datetime.now()
                                timeDiff = curTime - lastSendResultTime
                                if( timeDiff.seconds >= iSendWaitDiffTime):
                                    lastSendResultTime = curTime
                                    self.Safe_AddMiddleResultData(self.s_runParamUnit.s_bstrFromName, reportResultV2)
                                    # 输出后，重新申请一个新的单元
                                    reportResultV2 = CTYBot_CTUnit_TaskRegCenter_ReportResult_V2()
                                    reportResultV2.s_bstrOrigTaskUniqueSign = bstrOrigParamUniqSign
                                time.sleep(0.1)
                                pass
                # 有有效内容？输出
                if( len(reportResultV2.s_subResultUnitArray) > 0):
                    self.Safe_AddMiddleResultData(self.s_runParamUnit.s_bstrFromName, reportResultV2)

                # 发送运行完成的消息
                replyCommUnit = CTYBot_CTUnit_CommonData()
                replyCommUnit.SetIntData(CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish)
                replyCommUnit.SetParam(self.s_runParamUnit.s_assignTaskParam.s_bstrUniqueSign, b'')
                self.Safe_AddMiddleResultData( self.s_runParamUnit.s_bstrFromName, replyCommUnit)
                # 任务自由，可以重新接收参数运行
                self.Safe_SetStatus(CTYLB_HostExec_V2_Thread.s_g_iFree)
                pass
            bTaskBusy = False
            if (not bTaskBusy):
                time.sleep(0.1)

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

    # 安全 设置状态
    def Safe_SetStatus(self, newStatus):
        if (self.s_ExecMutex.acquire()):
            self.s_iCurStatus = newStatus
            self.s_ExecMutex.release()

    # 安全 设置参数
    def Safe_StartRunParam(self, runParam):
        if (self.s_ExecMutex.acquire()):
            self.s_runParamUnit = runParam
            self.s_iCurStatus = CTYLB_HostExec_V2_Thread.s_g_iPrepareRun
            self.s_ExecMutex.release()

    # 安全 增加输出结果值
    # start by sk. 170221
    def Safe_AddMiddleResultData(self, bstrFrom, resultUnit):
        bstrFrom = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrFrom)
        if (self.s_ExecMutex.acquire()):
            self.s_resultMiddleUnitArray.append( CThreadRunResultUnit(bstrFrom, resultUnit))
            self.s_ExecMutex.release()

    # 安全 获得结果个数
    # start by sk. 170227
    def Safe_GetResultDataCount(self):
        iRetValue = 0
        if (self.s_ExecMutex.acquire()):
            iRetValue = len(self.s_resultMiddleUnitArray)
            self.s_ExecMutex.release()
        return iRetValue

    # 安全 设置结果值
    # start by sk. 170221
    def Safe_SetStatusFinish(self):
        if (self.s_ExecMutex.acquire()):
            self.s_iCurStatus = CTYLB_HostExec_V2_Thread.s_g_iFree
            self.s_ExecMutex.release()

    # 安全 设置结果值
    # start by sk. 170221
    def Safe_Pop_Retrive_MiddleResult_Unit(self):
        bstrRetName, retResultParamUnit = b'', None
        if (self.s_ExecMutex.acquire()):
            if( len(self.s_resultMiddleUnitArray) > 0):
                resultUnit = self.s_resultMiddleUnitArray.pop(0)
                bstrRetName = resultUnit.s_bstrFromName
                retResultParamUnit = resultUnit.s_runResultUnit
            self.s_ExecMutex.release()
        return bstrRetName, retResultParamUnit

    @staticmethod
    def ShowLog(iWarnLevel, strMsg):
        CTYLB_Log.ShowLog(iWarnLevel, u'Connect Thread', strMsg)

# 主机运行插件机器人实现
# start by sk. 170212
class CTYLB_Host_V2_ExecPlugin_Bot:
    s_g_iMaxSendResultSizeOnce = 1024000    # 最多每次发送1M大小个结果单元

    def __init__(self, bstrSelfIDName, threadPluginExecEachCallBack, iThreadCount=10):
        bstrSelfIDName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrSelfIDName)

        self.s_runThreadMang = []  # 运行线程管理  CTYLB_HostExec_Thread
        self.s_globalQueue = queue.Queue()  # 线程同步
        self.s_waitRunParamUnit = []  # 等待运行的单元参数队列 CThreadRunParamUnit
        self.s_threadPluginExecEachCallBackFunc = threadPluginExecEachCallBack
        self.s_lastSendStatusContentTime = datetime(2017, 1, 1)
        self.s_bstrSelfIDName = bstrSelfIDName
        self.s_iSimuRunThreadCount = iThreadCount   # 线程个数
        pass

    # 启动运行线程池
    # start by sk. 170212
    def StartRunThreads(self):
        for iIndex in range(self.s_iSimuRunThreadCount):
            self.s_globalQueue.put(iIndex)
            newThread = CTYLB_HostExec_V2_Thread( self.s_bstrSelfIDName, u'host-exec', self.s_globalQueue, iIndex, self.s_threadPluginExecEachCallBackFunc)
            newThread.setDaemon(True)
            self.s_runThreadMang.append(newThread)
            newThread.start()

    # 将任务分配到空闲线程
    # start by sk. 170212
    def Check_AssignTaskToFreeThread(self):
        bRetValue = False
        if (len(self.s_waitRunParamUnit) > 0):
            # 查找空闲单元
            for eachThread in self.s_runThreadMang:
                iStatus = eachThread.Safe_GetStatus()
                if ( iStatus == CTYLB_HostExec_V2_Thread.s_g_iFree):
                    curRunParamUnit = self.s_waitRunParamUnit.pop(0)
                    eachThread.Safe_StartRunParam(curRunParamUnit)
                    bRetValue = True
                    break
            pass
        return bRetValue

    # 将结果发送给远程管理端
    # start by sk. 170212
    def PopSizeResultCTUnitArray(self, iTotalExSize=1024000):
        iCurSendCount = 0
        bLooping = True
        retResultCTUnitArray = []
        iCurExSize = 0
        # 查找任务完成等待取结果的单元
        while( bLooping):
            bAllEmpty = True  # 是否全部为空
            for eachThread in self.s_runThreadMang:
                if( iCurExSize >= iTotalExSize):
                    bLooping = False
                    break
                bstrFromName, resultRunUnit = eachThread.Safe_Pop_Retrive_MiddleResult_Unit()
                if( bstrFromName and resultRunUnit):
                    iCurSendCount += 1    # 发送个数 + 1
                    bAllEmpty = False     # 至少一个有内容，不为空
                    strMsg = u'send type:%d cmd:%d-%d sign:%s' % (resultRunUnit.s_iMyDataType, resultRunUnit.s_iBotCmd_Main,
                                                                  resultRunUnit.s_iBotCmd_Sub, resultRunUnit.s_bstrUniqueSign)
                    CTYLB_Log.ShowLog(0, u'bot', strMsg)
                    retResultCTUnitArray.append( resultRunUnit)
                    iCurExSize += resultRunUnit.GetTotalSize()
                pass
            if( bAllEmpty):  # 如果全部为空，那么，跳出循环
                break
        return retResultCTUnitArray

    # 将任务分配到空闲线程
    # start by sk. 170212
    def GetTotalResultCount(self):
        iRetValue = 0
        # 查找任务完成等待取结果的单元
        for eachThread in self.s_runThreadMang:
            iEachCount = eachThread.Safe_GetResultDataCount()
            iRetValue += iEachCount
        return iRetValue

    # 将自身状态发送给远程端
    # start by sk. 170212
    def Create_New_Get_StatusReportUnit(self):
        newReportUnit = CTYBot_CTUnit_TaskRegCenter_ReportMyStatus()

        pluginIDArray = CTYBot_ExecPlugin_GetSupportIDArray()
        newReportUnit.s_iSupportPluginIDArray.extend(pluginIDArray)  # 当前支持的插件ID

        # 获得当前运行的个数
        iFreeCount = 0
        iTotalThreadCount = len(self.s_runThreadMang)
        for eachThreadUnit in self.s_runThreadMang:
            iStatus = eachThreadUnit.Safe_GetStatus()
            if (iStatus == CTYLB_HostExec_V2_Thread.s_g_iFree):
                # add by sk 170315. 强制设置结果全部输出，才能接收下一步的参数内容
                if( eachThreadUnit.Safe_GetResultDataCount() == 0):
                    iFreeCount += 1
        newReportUnit.s_iCanRecvTaskCount = iFreeCount  # 可以接收的任务数
        newReportUnit.s_iCurRunCount = iTotalThreadCount - iFreeCount  # 当前正在运算的数量
        newReportUnit.s_iCurWaitCount = len(self.s_waitRunParamUnit)  # 当前等待的个数

        return newReportUnit

    # 发送数据到远程任务注册管理中心，包括自身状态，和结果数据
    # start by sk. 170309
    def RetriveSendStatusResultDataOut( self):
        sendCTUnitArray = []
        # 结果数据
        resultCTUnitArray = self.PopSizeResultCTUnitArray( CTYLB_Host_V2_ExecPlugin_Bot.s_g_iMaxSendResultSizeOnce)
        sendCTUnitArray.extend( resultCTUnitArray)
        # 状态数据
        newReportUnit = self.Create_New_Get_StatusReportUnit()
        sendCTUnitArray.append( newReportUnit)
        # 执行发送
        return sendCTUnitArray

    # 发送数据到远程任务注册管理中心，包括自身状态，和结果数据
    # start by sk. 170309
    def HandleRecvSockCTUnit( self, cTUnit):
        if( cTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1 and
            cTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock and
            cTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock):
            CTYLB_Log.ShowLog(0, u'Recv-CallBack', u' Recv WebParamBlock cmd [%s]' % (cTUnit.s_bstrUniqueSign))
            newRunParamUnit = CThreadRunParamUnit( u'n/a', cTUnit)
            self.s_waitRunParamUnit.append(newRunParamUnit)
            pass
        # 结果通用单元
        elif ( cTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask and
                       cTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_CommonTask_SingleData):
            if (cTUnit.s_iBotCmd_Sub == CTYLB_TaskReg_Cmd_BaseDef.s_g_iSubCmd_Sample):
                pass
            elif (cTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_CommonTask_SingleData):
                if ( cTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Query_DExecHost_Send_Result_Count):
                    # [任务中心->执行插件主机] 查询完成的结果单元个数。strParam1=最大可发送个数。
                    # 在单位时间发送内容中，实现发送数据的功能
                    pass
        pass

    # 安全退出全部线程
    # start by sk. 170212
    def Safe_QuitAllThread(self):
        # 退出线程
        for eachThread in self.s_runThreadMang:
            eachThread.Safe_Stop()
        self.s_globalQueue.join()

    pass

# ################################################################################################
#   下面是节点系统单元实现
# ################################################################################################

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting")
    g_bSysRunning = False

# 主程序入口
if __name__ == '__main__':
    #获取配置文件路径及文件名，文件夹不存在则创建
    config_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"config")
    config_file= os.path.join(config_dir,u"config.ini")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.isfile(config_file):
        CTYLB_Log.ShowLog(0, u'Main', u'[%s] config file missing...Quit!' % g_strProgName)
        #配置文件不存在，直接退出
        os._exit(-1)

    db_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"db")
    db_file= os.path.join(db_dir,u"data.db")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    s_g_iTaskMang_Listen_Port_PluginStatusResult = 4  # 任务管理中心，插件报告状态，和传回结果。收到后，发送参数块过去
    # 创建机器人框架
    g_LessTYLB_Bot_ExecPlugin_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_ExecPlugin_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 注册用到的数据单元，当HLSession单元收到后，里面用到的单元数据
    g_LessTYLB_Bot_ExecPlugin_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                             CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock,
                                                             CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock,
                                                             CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignWebNameBlock)
    # 准备运行
    g_LessTYLB_Bot_ExecPlugin_FrameThread.Prepare_Start()
    # 读取服务器配置
    ustrTaskRegCenterName = g_LessTYLB_Bot_ExecPlugin_FrameThread.s_execTYLB_Bot_Sample.ReadIniSectionValue( config_file, u'client', u'taskcenter_id',
                                                                    CTYLB_Bot_BaseDef.s_g_strBotName_TaskRegCenter_sk_v1)
    bstrTaskRegCenterName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(ustrTaskRegCenterName)
    # 创建运行任务线程管理单元
    bstrSelfIDName = CTYLB_MainSys_MiscFunc.SafeGetUTF8( g_LessTYLB_Bot_ExecPlugin_FrameThread.GetMyName())
    g_hostExecPluginBot = CTYLB_Host_V2_ExecPlugin_Bot( bstrSelfIDName, CTYBot_ExecPlugin_Each_CallBack_RunParam)
    g_hostExecPluginBot.StartRunThreads()

    hlSockMang = g_LessTYLB_Bot_ExecPlugin_FrameThread.s_HLSockMang
    connectEchoSock = CTYFBot_OpSession_ConnectSock( hlSockMang, bstrTaskRegCenterName, s_g_iTaskMang_Listen_Port_PluginStatusResult)
    CTYLB_Log.ShowLog(0, u'RunPlugin', u'start HLSock connect remote TRC_Center.[%s:%d]' % ( bstrTaskRegCenterName, s_g_iTaskMang_Listen_Port_PluginStatusResult))

    while(g_bSysRunning):
        bTaskBusy = False
        if( connectEchoSock.ExecNextCheck()):
            bTaskBusy = True

        # 检查发送数据.如果有结果数据未发送，那么，立即返回结果数据，不等待
        iNextExecCheckCount = g_hostExecPluginBot.GetTotalResultCount()
        if( iNextExecCheckCount > 0):
            connectEchoSock.SetNextTempSendWaitTick(1)

        if( connectEchoSock.CanExecSendData()):
            execSendCTArray = g_hostExecPluginBot.RetriveSendStatusResultDataOut()
            connectEchoSock.ExecSendData( execSendCTArray)
            bTaskBusy = True
        # 检查接收的数据
        recvCTArray = connectEchoSock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            bstrPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connectEchoSock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                g_hostExecPluginBot.HandleRecvSockCTUnit(eachUnit)
            # 如果还有结果数据为发送，那么，立即调度下一步进行发送
            if( g_hostExecPluginBot.GetTotalResultCount() > 0):
                connectEchoSock.SetNextTempSendWaitTick(1)

        # 检查管理中心
        if (g_hostExecPluginBot.Check_AssignTaskToFreeThread()):
            bTaskBusy = True

        if( not bTaskBusy):
            time.sleep(0.1)
        bTaskBusy = False

    # 退出
    connectEchoSock.Close()
    g_LessTYLB_Bot_ExecPlugin_FrameThread.SafeStop()
    g_hostExecPluginBot.Safe_QuitAllThread()

    CTYLB_Log.ShowLog(0, u'Main', u'bye bye')

