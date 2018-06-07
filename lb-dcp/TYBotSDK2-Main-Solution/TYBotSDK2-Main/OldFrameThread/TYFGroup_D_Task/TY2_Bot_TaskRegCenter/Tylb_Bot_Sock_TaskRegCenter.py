# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Sock_TaskRegCenter.py 任务注册中心。执行单元向它汇报空闲状况，需要执行的向它提请执行要求
#
# start by sk. 170212
# fix bug, main FBot Loop inc effiency. sk. 170601.
# 增加接收到PluginClient的结果CTUnit后，每个单元需要搜索对应的ReqHostUnit的缓冲存储。by sk. 170614

from TYBotSDK2.FBot.fbotV2 import FBot
from TYBotSDK2.FBot.global_define import *

import time
import os
from datetime import datetime
from TYBotSDK2.BotBase.Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_TaskRegCenter_ReportMangStatus,\
    CTYBot_CTUnit_CommonData, CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignTaskParam,\
    CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignWebNameBlock, CTYBot_CTUnit_CreateNew_ReportMyStatus,\
    CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_V2_ReportResult, CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_ReportResult
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread

# 任务中心，远端执行插件任务的主机单元
# start by sk. 170215
class CTYLB_TaskCenter_ExecHostUnit:
    s_g_statusTimeToCurrentOnLine = 1800  # 30分钟之内？
    s_g_iMaxAcceptRunParam = 15  # 最多同时接收15个任务
    s_g_iResultQueryTimeDiff = 1  # 每秒检查是否可以查询结果
    s_g_iMaxWaitResultForceTimeDiff = 600  # 每10分钟强制重新发送申请结果回传

    def __init__(self, bstrHostName, iAcceptSockIndex):
        bstrHostName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrHostName)

        self.s_lastSendCmdTime = datetime( 2017, 1,1)
        self.s_lastClientStatusData = None
        self.s_bstrHostIDName = bstrHostName
        self.s_lastRecvStatusTime = datetime.now()
        self.s_bstrTaskParamSignArray = []  # 任务参数队列

        self.s_iSock_AcceptFromRemotePlugin = iAcceptSockIndex  # 连接远端插件的管套ID
        self.s_toBeSendCTUnitArray = []   # 等待发送单元队列

    # 上次状态数据是否超时？
    # start by sk. 170222
    def IsStatusDataTimeOut(self):
        bTimeOut = False

        '''
        if( self.s_lastClientStatusData):
            nowTime = datetime.now()
            timeDiff = nowTime - self.s_lastClientStatusData.GetUnitRelativeTime()
            if (timeDiff.seconds >= CTYLB_TaskCenter_ExecHostUnit.s_g_statusTimeToCurrentOnLine):
                bTimeOut = True
        '''
        return bTimeOut

    # 获得插件ID可以运行的参数块个数
    # start by sk. 170226
    def GetPluginIDCanRunParamBlockCount(self, iPluginID):
        iRetFreeParamBlockCount = 0
        if( self.s_lastClientStatusData):
            if( iPluginID in self.s_lastClientStatusData.s_iSupportPluginIDArray):
                iRetFreeParamBlockCount = self.s_lastClientStatusData.s_iCanRecvTaskCount
        return iRetFreeParamBlockCount

    # 更新上次接收的时间?
    # start by sk. 170224
    def UpdateLastActiveTime(self):
        self.s_lastRecvStatusTime = datetime.now()

    # 本主机是否可以接收新的运行单元了?
    # start by sk. 170222
    def CanAcceptNewTask(self):
        bRetValue = False
        if( len(self.s_bstrTaskParamSignArray) >= CTYLB_TaskCenter_ExecHostUnit.s_g_iMaxAcceptRunParam):
            pass
        else:
            bRetValue = True
        return bRetValue

    # 设置任务标识已经完成
    # start by sk. 170222
    def SetTaskSignFinish(self, bstrParamSign):
        bstrParamSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamSign)
        if( bstrParamSign in self.s_bstrTaskParamSignArray):
            self.s_bstrTaskParamSignArray.remove( bstrParamSign)

    # 主机单元是否超时？
    # start by sk. 170222
    def IsHostTimeOut(self):
        bTimeOut = False

        if( self.s_lastClientStatusData):
            if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_lastRecvStatusTime, CTYLB_TaskCenter_HostMang.s_g_iMaxClientOffLineIdleTime)):
                bTimeOut = True
        return bTimeOut

# 任务中心，请求执行的主机，和请求过来的参数队列
# start by sk. 170220
class CTYLB_TaskCenter_RequestHostUnit:
    def __init__(self, bstrHostName, iAcceptSock):
        bstrHostName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrHostName)

        self.s_bstrHostIDName = bstrHostName    # 主机名字
        self.s_requestParamUnitArray = []     # 请求执行的参数单元队列  CTYLB_P2P_ContentUnit_Base
        self.s_waitExecParamArray = []        #  等待执行的参数队列  CTYLB_P2P_ContentUnit_Base
        self.s_waitBroadCastParamArray = []   # 等待广播执行的参数队列  CTYLB_P2P_ContentUnit_Base
        self.s_bstrRunningParamSignArray = []         # 正在运行的参数标记队列bytes
        self.s_runningBCastParamArray = []         # 正在运行的参数队列  CTYLB_P2P_ContentUnit_Base
        self.s_lastScheduleTime = datetime(2017,1,1)   # 上次调度时间
        self.s_clientResultCTUnitArray = []   # 客户端结果发送的单元队列

        self.s_iAcceptSock = iAcceptSock    # 接收到请求端的管套ID
        self.s_toBeSendReplyCTUnitArray = []   # 等待发送的回复单元队列
        pass

    # 是否有单个执行的自由未执行的参数
    def HaveFree_SingleRequest_Param(self):
        bRetValue = False
        if( self.s_waitExecParamArray):
            bRetValue = True
        return bRetValue

    # 获得下一个单个执行的自由参数
    def Query_NextFreeParam_SingleRequest(self):
        bRetValue = False
        if( self.s_waitExecParamArray):
            bRetValue = True
        return bRetValue

    # 在等待队列中，去除指定的单元
    def PopFrom_WaitArray_StoreSign_To_ExecParamArray(self):
        retParamUnit = None
        if( self.s_waitExecParamArray):
            retParamUnit = self.s_waitExecParamArray.pop(0)
            self.s_bstrRunningParamSignArray.append(retParamUnit.s_bstrUniqueSign)
            self.s_lastScheduleTime = datetime.now()
        return retParamUnit

    # 获得等待运行的参数块个数
    # start by sk. 170310
    def GetNeedRunParamBlockCount(self, iPluginID):
        iRetCount = 0
        for eachParam in self.s_waitExecParamArray:
            iParamPluginID = CTYLB_TaskCenter_HostMang.GetParamUnit_PluginID( eachParam)
            if( iParamPluginID == iPluginID):
                iRetCount += 1
        return iRetCount

    # 根据名字搜索请求任务的客户端主机单元
    # start by sk. 170221
    def Search_OrigTaskSign_By_UniqueSign(self, bstrParamUniqueSign):
        bstrParamUniqueSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamUniqueSign)
        bRetExist = False
        if( bstrParamUniqueSign in self.s_bstrRunningParamSignArray):
            bRetExist = True
        return bRetExist

    # 设置任务完成
    # start by sk. 170221
    def SetTaskFinish(self, bstrParamUnitUniqueSign):
        bstrParamUnitUniqueSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamUnitUniqueSign)
        if( bstrParamUnitUniqueSign in self.s_bstrRunningParamSignArray):
            self.s_bstrRunningParamSignArray.remove( bstrParamUnitUniqueSign)
        pass

# 任务中心，执行主机管理
#  刷新客户端的数据，广播任务，请求执行任务，查找空闲的单元，生成显示数据
# start by sk. 170215
class CTYLB_TaskCenter_HostMang:
    s_g_iMaxCheckClientSecond = 1  # 每秒检查一次
    s_g_iMaxSendTotalCTUnitCount = 2500  # 每次发送2500个单元数据包
    s_g_iMaxClientOffLineIdleTime = 1200  # 20分钟没有状态消息，则下线

    def __init__(self):
        self.s_execHostUnitArray = []  # 主机单元队列 CTYLB_TaskCenter_ExecHostUnit
        self.s_requestHostUnitArray = []   # 请求执行的主机单元队列  CTYLB_TaskCenter_RequestHostUnit
        self.s_lastCheckClientTime = datetime.now()
        self.s_waitTransBackResultArray = []                # 等待传输回去的结果数据 CTYBot_CTUnit_TaskRegCenter_ReportResult
        self.s_waitReportMangStatusBackToUserArray = []     # 已经请求了，等待回复管理状态的用户队列

    # 根据名字搜索执行任务的主机单元
    # start by sk. 170221
    def Search_execHostUnit_By_UniqueSign(self, bstrParamUniqueSign):
        bstrParamUniqueSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamUniqueSign)
        retHostUnit = None
        for eachUnit in self.s_execHostUnitArray:
            if( bstrParamUniqueSign in eachUnit.s_bstrTaskParamSignArray):
                retHostUnit = eachUnit
                break
        return retHostUnit

    # 根据名字搜索请求任务的客户端主机单元
    # start by sk. 170221
    def Search_OrigTaskSign_ReqHostUnit_By_UniqueSign(self, bstrParamUniqueSign, lastOrigReqHostUnit):
        bstrParamUniqueSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamUniqueSign)
        retHostUnit = None
        bOrigRunParamExist = False
        bNeedTotalSearch = True

        # 这里快速判断是否上次单元
        if( lastOrigReqHostUnit):
            bCurExist = lastOrigReqHostUnit.Search_OrigTaskSign_By_UniqueSign( bstrParamUniqueSign)
            if( bCurExist):
                bOrigRunParamExist = True
                retHostUnit = lastOrigReqHostUnit
                bNeedTotalSearch = False

        # 需要进行全面搜索
        if( bNeedTotalSearch):
            for eachUnit in self.s_requestHostUnitArray:
                bCurExist = eachUnit.Search_OrigTaskSign_By_UniqueSign( bstrParamUniqueSign)
                if( bCurExist):
                    bOrigRunParamExist = True
                    retHostUnit = eachUnit
                    break

        return bOrigRunParamExist, retHostUnit

    # 根据名字搜索请求任务的客户端主机单元
    def Search_Add_Request_HostUnit_By_IDName(self, bstrHostIDName, iNewSock, bAddNew=True):
        bstrHostIDName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrHostIDName)
        retHostUnit = None
        for eachUnit in self.s_requestHostUnitArray:
            if (eachUnit.s_bstrHostIDName == bstrHostIDName):
                eachUnit.s_iAcceptSock = iNewSock
                retHostUnit = eachUnit
                break
        if( not retHostUnit):
            # 新主机，加入请求主机单元队列
            hostUnit = CTYLB_TaskCenter_RequestHostUnit( bstrHostIDName, iNewSock)
            self.s_requestHostUnitArray.append(hostUnit)
            retHostUnit = hostUnit
        return retHostUnit

    # 根据名字搜索执行的客户端主机单元
    def SearchExecHostUnitByIDName(self, bstrHostIDName):
        bstrHostIDName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrHostIDName)
        retHostUnit = None
        for eachUnit in self.s_execHostUnitArray:
            if (eachUnit.s_bstrHostIDName == bstrHostIDName):
                retHostUnit = eachUnit
                break
        return retHostUnit

    # 查询可以运行的插件个数
    # start by sk. 170226
    def Query_PluginID_CanRunCount(self, iPluginID):
        iRetRunCount = 0
        # 查找最大可接收数量的
        for eachHost in self.s_execHostUnitArray:
            iRetRunCount += eachHost.GetPluginIDCanRunParamBlockCount(iPluginID)

        # 如果等待队列有参数需要执行，那么，将个数进行删除
        for eachReqHost in self.s_requestHostUnitArray:
            iNeedAssignParamCount = eachReqHost.GetNeedRunParamBlockCount( iPluginID)
            iRetRunCount -= iNeedAssignParamCount

        if( iRetRunCount < 0):
            iRetRunCount = 0
        return iRetRunCount

    # 处理 提交请求的 管套关闭
    # start by sk. 170308
    def Handle_PromptorRequester_SockClose(self, iPromptSock):
        # 找到以前的对象，删除
        reqHostUnit = self.SearchHostUnitBySockIndex( iPromptSock, True)
        if( reqHostUnit):
            self.s_requestHostUnitArray.remove( reqHostUnit)
        pass
    pass

    # 处理 主机插件执行的 管套关闭
    # start by sk. 170308
    def Handle_ExecPlugin_SockClose(self, iPromptSock):
        # 找到以前的对象，删除
        reqHostUnit = self.SearchHostUnitBySockIndex( iPromptSock, False)
        if( reqHostUnit):
            self.s_execHostUnitArray.remove( reqHostUnit)
        pass
    pass

    # 根据管套，搜索 请求主机，或者 执行主机对象。　
    # start by sk. 170308
    def SearchHostUnitBySockIndex(self, iSockIndex, bPrompterOrExecPlugin):
        retHostUnit = None
        # 找到以前的对象，删除
        if( bPrompterOrExecPlugin):
            for eachPromptor in self.s_requestHostUnitArray:
                if( eachPromptor.s_iAcceptSock == iSockIndex):
                    retHostUnit = eachPromptor
                    break
        else:
            for eachExecHost in self.s_execHostUnitArray:
                if (eachExecHost.s_iSock_AcceptFromRemotePlugin == iSockIndex):
                    retHostUnit = eachExecHost
                    break
        return retHostUnit

    # 处理 提交请求主机 接收到新管套。　
    # start by sk. 170308
    def Handle_PromptorRequester_NewAcceptSock( self, bstrPeerName, iNewAcceptSock_Prompter):
        bstrPeerName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrPeerName)
        retNewRequestHost = self.Search_Add_Request_HostUnit_By_IDName( bstrPeerName, iNewAcceptSock_Prompter)
        if( retNewRequestHost):
            retNewRequestHost.s_iAcceptSock = iNewAcceptSock_Prompter

    # 处理 执行主机 接收到新管套。　
    # start by sk. 170308
    def Handle_ExecPluginHost_NewAcceptSock( self, bstrPeerName, iNewAcceptSock_ExecPlugin):
        bstrPeerName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrPeerName)
        clientUnit = self.SearchExecHostUnitByIDName(bstrPeerName)
        if (clientUnit == None):
            clientUnit = CTYLB_TaskCenter_ExecHostUnit(bstrPeerName, None)
            self.s_execHostUnitArray.append( clientUnit)
            clientUnit.s_iSock_AcceptFromRemotePlugin = iNewAcceptSock_ExecPlugin
    pass

    # 处理 提交请求主机 管套信息。　
    # start by sk. 170308
    def Handle_PromptorRequester_RecvSockCTUnit(self, hlSockMang, iPromptorSock, ctUnitArray):
        requestorHost = self.SearchHostUnitBySockIndex(iPromptorSock, True)
        if (requestorHost):
            for eachCTUnit in ctUnitArray:
                bUnitHandled = False
                if( not bUnitHandled):
                    # 单个参数块分配
                    if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                        if( (eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_AssignTask) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_AssignTask_Param) ):
                            bUnitHandled = True
                            requestorHost.s_waitExecParamArray.append( eachCTUnit)
                            pass
                if( not bUnitHandled):
                    # 广播参数块分配
                    if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                        if( (eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_AssignTask) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_AssignTask_BroadCast_Param) ):
                            bUnitHandled = True
                            requestorHost.s_waitBroadCastParamArray.append( eachCTUnit)
                            pass
                if( not bUnitHandled):
                    # 域名参数块分配
                    if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                        if( (eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock) ):
                            bUnitHandled = True
                            requestorHost.s_waitExecParamArray.append( eachCTUnit)
                            pass
                if( not bUnitHandled):
                    if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
                        if( (eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_CommonTask_SingleData) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_CommonTask_SingleData) ):
                            bUnitHandled = True
                            self.__Handle_PromptRequestor_Recv_CommCTUnit( requestorHost, eachCTUnit)
            # 调度数据包发送回去。
            totalNeedSend = []
            # 把最多某个个长度的数组存入
            # 发送 回复单元
            iCanSendCount = CTYLB_TaskCenter_HostMang.s_g_iMaxSendTotalCTUnitCount
            iArrayLen = len(requestorHost.s_toBeSendReplyCTUnitArray)
            if( iArrayLen > 0):
                iHaveSendCount = iArrayLen if( iCanSendCount > iArrayLen) else iCanSendCount
                totalNeedSend.extend( requestorHost.s_toBeSendReplyCTUnitArray[:iHaveSendCount])
                stillSaveArray = requestorHost.s_toBeSendReplyCTUnitArray[iHaveSendCount:]
                requestorHost.s_toBeSendReplyCTUnitArray = stillSaveArray

            # 发送结果单元
            iArrayLen = len(requestorHost.s_clientResultCTUnitArray)
            iCanSendCount = CTYLB_TaskCenter_HostMang.s_g_iMaxSendTotalCTUnitCount - len(totalNeedSend)
            if( iArrayLen > 0 and iCanSendCount > 0):
                iHaveSendCount = iArrayLen if( iCanSendCount > iArrayLen) else iCanSendCount
                totalNeedSend.extend( requestorHost.s_clientResultCTUnitArray[:iHaveSendCount])
                stillSaveArray = requestorHost.s_clientResultCTUnitArray[iHaveSendCount:]
                requestorHost.s_clientResultCTUnitArray = stillSaveArray

            if( not totalNeedSend):
                # 如果为空的队列，增加临时单元，保证队列不为空
                replyCommUnit = CTYBot_CTUnit_CommonData()
                totalNeedSend.append( replyCommUnit)

            hlSockMang.PassiveSend_To_AcceptSock( iPromptorSock, totalNeedSend)
        else:
            CTYLB_Log.ShowLog(1, 'TRC_host_mang', "Invalid Promptor HL_Socket %d not exist" % (iPromptorSock))
            pass

    # 处理 插件执行主机 管套信息。　
    # start by sk. 170308
    def Handle_ExecPlugin_RecvSockCTUnit(self, hlSockMang, iExecPluginSock, ctUnitArray):
        execPluginHost = self.SearchHostUnitBySockIndex(iExecPluginSock, False)
        if (execPluginHost):
            execPluginHost.UpdateLastActiveTime()
            lastOrigReqHostUnit = None  # 上次查询的主机单元值
            for eachCTUnit in ctUnitArray:
                bUnitHandled = False
                if (not bUnitHandled):
                    # 向任务中心报告当前状态
                    if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                        if ((eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportMyStatus) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportMyStatus_None)):
                            bUnitHandled = True
                            execPluginHost.s_lastClientStatusData = eachCTUnit
                            pass
                if (not bUnitHandled):
                    # 结果报告的命令
                    if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                        if ((eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl)):
                            bUnitHandled = True
                            taskUnitReportResult = eachCTUnit
                            bOrigParamExist, origReqHostUnit = self.Search_OrigTaskSign_ReqHostUnit_By_UniqueSign( taskUnitReportResult.s_bstrOrigTaskUniqueSign, lastOrigReqHostUnit)
                            if (bOrigParamExist and origReqHostUnit):
                                origReqHostUnit.s_clientResultCTUnitArray.append(taskUnitReportResult)
                                lastOrigReqHostUnit = origReqHostUnit
                            pass
                if (not bUnitHandled):
                    # 结果报告单元V2
                    if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                        if ((eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult_V2) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_V2_PingTraceWebCrawl)):
                            bUnitHandled = True
                            taskUnitReportV2Result = eachCTUnit
                            bOrigParamExist, origReqHostUnit = self.Search_OrigTaskSign_ReqHostUnit_By_UniqueSign( taskUnitReportV2Result.s_bstrOrigTaskUniqueSign, lastOrigReqHostUnit)
                            if (bOrigParamExist and origReqHostUnit):
                                origReqHostUnit.s_clientResultCTUnitArray.append(taskUnitReportV2Result)
                                lastOrigReqHostUnit = origReqHostUnit
                            pass
                if (not bUnitHandled):
                    # 结果通用单元
                    if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
                        if ((eachCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_CommonTask_SingleData) and
                                (eachCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_CommonTask_SingleData)):
                            bUnitHandled = True
                            lastOrigReqHostUnit = self.__Handle_ExecPluginHost_Recv_CommCTUnit( execPluginHost, eachCTUnit, lastOrigReqHostUnit)
            # 把主机空闲的参数块，分配到该主机。
            self.__AssignFreeParamToExecPluginHost( execPluginHost)
            # 发送数据包。发送后，清除
            if( len(execPluginHost.s_toBeSendCTUnitArray) > 0):
                toBeSendArray = execPluginHost.s_toBeSendCTUnitArray
            else:
                tmpCommCTUnit = CTYBot_CTUnit_CommonData()
                tmpCommCTUnit.SetIntData( 0)
                toBeSendArray = [tmpCommCTUnit]
            hlSockMang.PassiveSend_To_AcceptSock(iExecPluginSock, toBeSendArray)
            execPluginHost.s_toBeSendCTUnitArray = []
        else:
            CTYLB_Log.ShowLog(1, 'TRC_host_mang', "Invalid ExecPluginSocket HL_Socket %d not exist" % (iExecPluginSock))
            pass

    # 提交请求主机，收到 通用单元的处理流程　
    # start by sk. 170308
    def __Handle_PromptRequestor_Recv_CommCTUnit(self, requestorHost, commDataCTUnit):
        if (commDataCTUnit.s_iType == CTYBot_CTUnit_CommonData.s_g_iType_int):
            if (commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Request_TaskCenter_Send_Promptor_Result_Count):
                # 请求报告管理端状态
                pass
            elif (commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Query_PluginID_Run_ParamBlock_Count):
                # 请求 插件可运行个数
                iQueryPluginID = int(commDataCTUnit.s_bstrParam1)
                iCanRunCount = self.Query_PluginID_CanRunCount(iQueryPluginID)
                replyCommCTUnit = CTYBot_CTUnit_CommonData()
                replyCommCTUnit.SetIntData(CTYBot_CTUnit_CommonData.s_g_iIntValue_Reply_PluginID_Run_ParamBlock_Count)
                replyCommCTUnit.SetParam(str(iQueryPluginID), str(iCanRunCount))
                requestorHost.s_toBeSendReplyCTUnitArray.append(replyCommCTUnit)

    # 执行插件单元，收到 通用单元的处理流程　
    # start by sk. 170308
    # 增加 上次请求主机单元对象输入和返回，加快处理速度。 by sk. 170614
    def __Handle_ExecPluginHost_Recv_CommCTUnit( self, execPluginHost, commDataCTUnit, lastOrigReqHostUnit):
        # 查找本记录对应的源主机
        if (commDataCTUnit.s_iType == CTYBot_CTUnit_CommonData.s_g_iType_int):
            if (commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish or
                        commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_BCast_Fail_No_Host or
                        commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Start_Run or
                        commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish_Fail):
                bOrigParamExist, origReqHostUnit = self.Search_OrigTaskSign_ReqHostUnit_By_UniqueSign(
                    commDataCTUnit.s_bstrParam1, lastOrigReqHostUnit)
                if( commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Start_Run ):
                    pass
                else:
                    # 搜索运行的主机，释放该标识
                    origExecHost = self.Search_execHostUnit_By_UniqueSign(commDataCTUnit.s_bstrParam1)
                    if (origExecHost):
                        origExecHost.SetTaskSignFinish(commDataCTUnit.s_bstrParam1)
                    # 搜索请求执行的主机单元。释放该单元
                    if (bOrigParamExist and origReqHostUnit):
                        origReqHostUnit.SetTaskFinish(commDataCTUnit.s_bstrParam1)
                # 搜索请求执行的主机单元。释放该单元
                if (bOrigParamExist and origReqHostUnit):
                    origReqHostUnit.s_clientResultCTUnitArray.append(commDataCTUnit)
                    lastOrigReqHostUnit = origReqHostUnit

            if (commDataCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Reply_DExecHost_Contain_Result):
                # [执行插件主机->任务中心] 回复我现有的结果单元个数, strParam1=还剩下的结果个数, strParam2=请求包的标识
                iNotHandleCount = int(commDataCTUnit.s_bstrParam1)
                execPluginHost.HandleRemoteRecvReplyResultQuery(iNotHandleCount, commDataCTUnit.s_bstrParam2)
        return lastOrigReqHostUnit

    # 分配自由参数，到执行主机。　
    # start by sk. 170308
    def __AssignFreeParamToExecPluginHost(self, execPluginHost):
        if (execPluginHost.s_lastClientStatusData and  execPluginHost.s_lastClientStatusData.s_iCanRecvTaskCount > 0):
            # 找有空闲请求，而且等待时间最长的任务
            freeRequestHost = self.__Query_RequestCanRunParam_MostWaitTime()
            if (freeRequestHost):
                freeParam = freeRequestHost.PopFrom_WaitArray_StoreSign_To_ExecParamArray()
                if (freeParam):
                    # 分配，发送
                    iExecPluginID = CTYLB_TaskCenter_HostMang.GetParamUnit_PluginID(freeParam)
                    if (iExecPluginID):
                        # 完成发送，执行删除参数，放到运行队列.
                        # 发送到远程执行主机
                        CTYLB_Log.ShowLog(0, 'TRC_host_mang', "send param [%s] to [%s]" % (
                            freeParam.s_bstrUniqueSign, execPluginHost.s_bstrHostIDName))
                        execPluginHost.s_toBeSendCTUnitArray.append( freeParam)
                        # 加入到主机的执行队列
                        execPluginHost.s_bstrTaskParamSignArray.append(freeParam.s_bstrUniqueSign)
                        # 分配一个，减少一个值
                        if( execPluginHost.s_lastClientStatusData):
                            execPluginHost.s_lastClientStatusData.s_iCanRecvTaskCount -= 1
                    else:
                        # 回复失败，设置任务完成。
                        freeRequestHost.SetTaskFinish(freeParam.s_bstrUniqueSign)
                        # set task finish & failure.
                        replyCommUnit = CTYBot_CTUnit_CommonData()
                        replyCommUnit.SetIntData(CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_BCast_Fail_No_Host)
                        replyCommUnit.SetParam(freeParam.s_bstrUniqueSign, '')
                        freeRequestHost.s_clientResultCTUnitArray.append(replyCommUnit)  # 加入到结果队列
                    pass
        pass

    # 获得 本管理中心 状态数据。　
    # start by sk. 170308
    def __GetSelf_ReportMangStatus_Unit(self):
        iTotalFreeCount = 0
        iOnLineHostCount = len(self.s_execHostUnitArray)
        iTotalWaitCount = 0

        for eachHost in self.s_execHostUnitArray:
            iTotalFreeCount += eachHost.s_lastClientStatusData.s_iCanRecvTaskCount
            iTotalWaitCount += eachHost.s_lastClientStatusData.s_iCurWaitCount
        iTotalWaitCount += len(self.s_waitTransBackResultArray)

        mangStatusResult = CTYBot_CTUnit_TaskRegCenter_ReportMangStatus()
        mangStatusResult.s_iTotalFreeCount = iTotalFreeCount
        mangStatusResult.s_iOnLineTotalHostCount = iOnLineHostCount
        mangStatusResult.s_iTotalWaitCount = iTotalWaitCount

        return mangStatusResult
    pass

    # 获得参数单元的 插件ID
    # start by sk. 170221
    @staticmethod
    def GetParamUnit_PluginID(paramCTUnit):
        iRetPluginID = 0
        if (paramCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
            if (paramCTUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock):
                if (paramCTUnit.s_iBotCmd_Sub == CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock):
                    iRetPluginID = paramCTUnit.s_iRunPluginID
        return iRetPluginID

    # 查找空闲可执行的客户单元
    # start by sk. 170215
    def __SearchMostFreeExecTaskClient(self, iPluginIDType):
        iMostCanRecvCount = 0
        retMostFreeHostUnit = None

        # 查找最大可接收数量的
        for eachHost in self.s_execHostUnitArray:
            if( eachHost.IsStatusDataTimeOut()):  # 接收到的是以前的状态数据，忽略
                pass
            else:
                if( iPluginIDType in  eachHost.s_lastClientStatusData.s_iSupportPluginIDArray):
                    # 每个主机最多同时运行20个任务，如果已经发送过去了，那么，等待
                    if( eachHost.CanAcceptNewTask()):
                        # 当前主机空闲数， ＝ 状态空闲值 － 当前分配的个数
                        iHostFreeCount = eachHost.s_lastClientStatusData.s_iCanRecvTaskCount
                        if (iMostCanRecvCount < iHostFreeCount):
                            iMostCanRecvCount = iHostFreeCount
                            retMostFreeHostUnit = eachHost
        return retMostFreeHostUnit

    # 找有空闲请求，而且等待时间最长的任务
    # start by sk. 170221
    def __Query_RequestCanRunParam_MostWaitTime(self):
        iLastWaitTimeDiff = 0
        nowDate = datetime.now()

        # 找有内容，而且等待最久的主机
        freeRequestParamHost = None
        for eachRequestHost in self.s_requestHostUnitArray:
            if(eachRequestHost.HaveFree_SingleRequest_Param()):
                curTimeDiff = nowDate - eachRequestHost.s_lastScheduleTime
                if( curTimeDiff.seconds >= iLastWaitTimeDiff):
                    # 当前主机等待时间比现在大?
                    iLastWaitTimeDiff = curTimeDiff.seconds
                    freeRequestParamHost = eachRequestHost

        return freeRequestParamHost

    # 找有空闲的广播任务请求
    # start by sk. 170221
    def __Pop_RequestBCastParam(self):
        retBCastParam, requestParamHost = None, None

        for eachRequestHost in self.s_requestHostUnitArray:
            if( len(eachRequestHost.s_waitBroadCastParamArray) > 0):
                retBCastParam = eachRequestHost.s_waitBroadCastParamArray.pop(0)
                requestParamHost = eachRequestHost
                break

        return retBCastParam, requestParamHost

# ################################################################################################
#   本地变量
# ################################################################################################
g_strProgName = u"TY_LB_Bot Sock D_Task Center"
g_taskSockCenterHostMang = CTYLB_TaskCenter_HostMang()  # 主机管理单元


# 全局系统运行标识
g_bSysRunning = True

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting")
    g_bSysRunning = False

# ################################################################################################
#   下面是主程序入口
# ################################################################################################
if __name__ == '__main__':
    s_g_iTaskMang_Listen_Port_PromptTask = 3  # 任务管理中心，对任务提交者的监听端口
    s_g_iTaskMang_Listen_Port_PluginStatusResult = 4  # 任务管理中心，插件报告状态，和传回结果。收到后，发送参数块过去

    # bot = FBot(name='TaskRegCenter', listen_mode=True, listen_operate_id=)


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


    # 创建机器人框架
    g_LessTYLB_Bot_TRC_Srv_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_TRC_Srv_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 注册用到的数据单元，当HLSession单元收到后，里面用到的单元数据
    g_LessTYLB_Bot_TRC_Srv_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                            CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_AssignTask,
                                                            CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_AssignTask_Param,
                                                            CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignTaskParam)
    g_LessTYLB_Bot_TRC_Srv_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                            CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_AssignTask,
                                                            CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_AssignTask_BroadCast_Param,
                                                            CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignTaskParam)
    g_LessTYLB_Bot_TRC_Srv_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                            CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock,
                                                            CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock,
                                                            CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignWebNameBlock)
    # 客户端
    g_LessTYLB_Bot_TRC_Srv_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                            CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportMyStatus,
                                                            CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportMyStatus_None,
                                                            CTYBot_CTUnit_CreateNew_ReportMyStatus)
    g_LessTYLB_Bot_TRC_Srv_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                            CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult,
                                                            CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl,
                                                            CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_ReportResult)
    g_LessTYLB_Bot_TRC_Srv_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                            CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult_V2,
                                                            CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_V2_PingTraceWebCrawl,
                                                            CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_V2_ReportResult)
    # 准备运行
    g_LessTYLB_Bot_TRC_Srv_FrameThread.Prepare_Start()

    # 获得管套管理对象
    hlSockMang = g_LessTYLB_Bot_TRC_Srv_FrameThread.s_HLSockMang
    iListenSock_Request_Prompter = hlSockMang.CreateListenSock( s_g_iTaskMang_Listen_Port_PromptTask)
    iListenSock_ExecPlugin_Host = hlSockMang.CreateListenSock( s_g_iTaskMang_Listen_Port_PluginStatusResult)
    iAcceptSock_Prompter_Array = []
    iAcceptSock_ExecPlugin_Array = []

    iLoopFreeCount = 0
    while(g_bSysRunning):
        bTaskBusy = False

        # 处理 提交，申请任务的 管套功能
        iNewAcceptSock_Prompter = hlSockMang.ExAcceptNewListenArriveSock( iListenSock_Request_Prompter)
        if( iNewAcceptSock_Prompter):
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSock_Prompter)
            CTYLB_Log.ShowLog(0, u'TRC_Prompter_Exec', u'from [%s:%d] new Promptor Requestor %d accept.' % (strPeerName, iPeerPort, iNewAcceptSock_Prompter))
            bTaskBusy = True
            g_taskSockCenterHostMang.Handle_PromptorRequester_NewAcceptSock(strPeerName, iNewAcceptSock_Prompter)
            iAcceptSock_Prompter_Array.append( iNewAcceptSock_Prompter)
            pass
        for iEachPromptorSock in iAcceptSock_Prompter_Array:
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachPromptorSock)
            if( not bSockExist):
                CTYLB_Log.ShowLog(0, u'TRC_Prompter_Exec', u'prompter request sock %d closed' % (iEachPromptorSock))
                iAcceptSock_Prompter_Array.remove( iEachPromptorSock)
                g_taskSockCenterHostMang.Handle_PromptorRequester_SockClose(iEachPromptorSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    g_taskSockCenterHostMang.Handle_PromptorRequester_RecvSockCTUnit( hlSockMang, iEachPromptorSock, ctUnitArray)

        # 处理 插件执行 管套功能
        iNewAcceptSock_ExecPlugin = hlSockMang.ExAcceptNewListenArriveSock( iListenSock_ExecPlugin_Host)
        if( iNewAcceptSock_ExecPlugin):
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSock_ExecPlugin)
            CTYLB_Log.ShowLog(0, u'TRC_Plugin_Exec', u'from [%s:%d] new plugin %d accept.' % (strPeerName, iPeerPort, iNewAcceptSock_ExecPlugin))
            bTaskBusy = True
            g_taskSockCenterHostMang.Handle_ExecPluginHost_NewAcceptSock(strPeerName, iNewAcceptSock_ExecPlugin)
            iAcceptSock_ExecPlugin_Array.append( iNewAcceptSock_ExecPlugin)
            pass
        for iEachExecPluginSock in iAcceptSock_ExecPlugin_Array:
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachExecPluginSock)
            if( not bSockExist):
                CTYLB_Log.ShowLog(0, u'TRC_Plugin_Exec', u'plugin sock %d closed' % (iEachExecPluginSock))
                iAcceptSock_ExecPlugin_Array.remove( iEachExecPluginSock)
                g_taskSockCenterHostMang.Handle_ExecPlugin_SockClose(iEachExecPluginSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    g_taskSockCenterHostMang.Handle_ExecPlugin_RecvSockCTUnit( hlSockMang, iEachExecPluginSock, ctUnitArray)
        if( not bTaskBusy):
            iLoopFreeCount += 1
            if( iLoopFreeCount > 100):
                time.sleep(0.01)
        else:
            iLoopFreeCount = 0

    # 退出线程
    g_LessTYLB_Bot_TRC_Srv_FrameThread.SafeStop()
    CTYLB_Log.ShowLog(0, u'Main', u'[%s] bye bye' % g_strProgName)

