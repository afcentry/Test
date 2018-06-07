# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Sk_Prompt_D_Task.py 天元机器人－提交分布任务，进行发送，获得分布结果后，显示出来
#
# start by sk. 170223

from TYBotSDK2.BotBase.Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock,\
    CTYBot_CTUnit_CommonData, CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_ReportResult, CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_V2_ReportResult
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.P2PClient.Tylb_p2p_ExCall_SubClient import CTYLB_P2P_ContentUnit_Base_bytes
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
from datetime import datetime

g_bstrTYFBot_OPDB_SrvName = b'TYFBot_OP_DB'     # 天元功能机器人，操作数据库实现

g_i_ListenSock_TYFBot_OP_DB_Operate_ParamBlock = 5  # 监听管套，操作数据库机器人，操作参数块
g_i_ListenSock_TYFBot_OP_DB_Operate_Result = 6      # 监听管套，操作数据库机器人，操作结果

g_i_OpParamBlock_SubCmd_RegiestDbTableField_Param = 501  # 注册数据库表字段参数
g_i_OpParamBlock_SubCmd_Reply_RegiestDbTableField_Param = 502  # 注册数据库表字段参数-返回
g_i_OpParamBlock_SubCmd_GetUnExecRecCount = 503  # 获得未处理的个数
g_i_OpParamBlock_SubCmd_Reply_GetUnExecRecCount = 504  # 获得未处理的个数-返回
g_i_OpParamBlock_SubCmd_GetRunParamBlock = 505  # 获得可运行的参数块
g_i_OpParamBlock_SubCmd_Reply_GetRunParamBlock = 506  # 获得可运行的参数块-返回
g_i_OpParamBlock_SubCmd_Finish_ParamBlock = 507  # finish参数块

g_i_OpResult_SubCmd_AddResult = 601  # 增加结果
g_bstr_ResultContentSplit = b'(;1-@;)'   # 结果内容的分隔符
g_i_OpResult_SubCmd_ReplyAddResult = 602  # 增加结果 返回


# tylb－bot 分布任务分发基本类,具有自动检查的功能。自动调度发送空闲参数块，自动维护队列
# start by sk. 170226
class CTYBot_WebName_DTask2_Base:
    s_g_iParamSendDiffTick = 1  # 每秒发送一次参数请求
    s_g_iParamQueryTimeDiff = 60      # 每1分钟查询一次，可否发送参数请求
    s_g_iMaxWaitParamQueryTime = 600    # 每次参数运行个数查询，最多强制等待10分钟。
    s_g_iMaxWaitParamStillCount = 600   # 最多参数块队列等待个数

    def __init__(self, iRunPluginiD, ustrRunTaskLineFile, iEachParamUnitCount=20):
        self.s_lastQueryParamTime = datetime(2017,1,1)  # 上次查询参数时间
        self.s_iRunPluginID = iRunPluginiD  # 运行的插件ID
        self.s_iCanSendRequestParamCount = 0  # 能发送请求参数的个数

        self.s_bstrPromptWaitFinishParamSignArray = []  # 提交，等待执行完成的参数标识队列
        self.s_lastSendParamTime = datetime(2017,1,1)   # 上次发送参数时间

        self.s_ustrRunTaskFileName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrRunTaskLineFile)   # 要运行的任务文件名
        self.s_bstrRunContentArray = []   # 运行内容队列
        self.s_iLastSendPos = 0  # 上次发送位置
        self.s_iEachParamBlockCount = iEachParamUnitCount   # 每次参数块，单元个数
        pass

    # 时间调度
    def Vilu_ExecTimerCheck(self):
        return False

    # 参数块标识是否我的队列。 返回：bool
    def IsParamBlockSignInMyArray(self, bstrParamSign):
        bstrParamSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamSign)
        bRetValue = False
        if( bstrParamSign in self.s_bstrPromptWaitFinishParamSignArray):
            bRetValue = True
        return bRetValue

    # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无
    def Viul_Internal_ParamBlock_PrePare(self, bstrRegCenterID):
        bstrRegCenterID = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrRegCenterID)
        with open(self.s_ustrRunTaskFileName, 'r') as ff:
            total = ff.read()
            bstrTotal = CTYLB_MainSys_MiscFunc.SafeGetUTF8(total)
            bstrContentArray = bstrTotal.split(b'\r')
            if (len(bstrContentArray) == 1):
                bstrContentArray = bstrTotal.split(b'\n')
            lines = bstrContentArray
            lines = [line.strip(b'\n') for line in lines]
            lines = [line.strip(b'\r') for line in lines]
            self.s_bstrRunContentArray = [x for x in lines if x != b'']
        pass

    # 设置需要跳过的行数。 返回：bool
    def SetNeedSkipDataPos(self, iNeedSkipPos):
        self.s_iLastSendPos = iNeedSkipPos

    # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容
    # update by sk. 170404. set output from stringarray into WebNameBlock_Param
    def Viul_Internal_ParamBlock_ReadEach_CTUnit(self):
        bstrRetParamUnitArray = []

        iTotalLineCount = len(self.s_bstrRunContentArray)
        if( self.s_iLastSendPos >= iTotalLineCount):
            pass
        else:
            iEnd = self.s_iLastSendPos + self.s_iEachParamBlockCount
            if( iEnd > iTotalLineCount):
                iEnd = iTotalLineCount
            bstrRetParamUnitArray = self.s_bstrRunContentArray[self.s_iLastSendPos:iEnd]
            self.s_iLastSendPos = iEnd

        assignWebNameBlock = CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock()
        # 提交到任务模块
        assignWebNameBlock.s_iRunPluginID = self.s_iRunPluginID
        assignWebNameBlock.s_bstrDomainNameArray = bstrRetParamUnitArray

        return assignWebNameBlock

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, bstrParamSign, iReplyPluginID, bstrOrigDomain, bstrResult):
        bstrParamSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamSign)
        bstrOrigDomain = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrOrigDomain)
        bstrResult = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrResult)

        bstrShowResult = bstrResult
        s2 = bstrShowResult.replace(b'\r', b'')
        bstrShowResult = s2.replace(b'\n', b'')
        CTYLB_Log.ShowLog( 0, 'result-arrive', '[%s] - [%s] [%d] [%s]' % (bstrParamSign, bstrOrigDomain, iReplyPluginID, bstrShowResult))
        msgObject={
            "monitor_type":"result",
            "level":"info",
            "target":bstrOrigDomain,
            "plugin_id":self.s_iRunPluginID,
            "block_id":"",
            "block_size":0,
            "free_size":0,
            "wait_size":0,
			"success_size":0,
            "result_code":0,
            "msg":bstrResult
            }
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
        pass

    # [子类可继承实现] - paramblock is finish
    def Viul_FinishParamBlock(self, bstrOrigParamBlockSign, iResultCode):
        pass

    # 系统调用，调度，发送请求参数块
    def Sys_Schedule_RequestParamBlock(self):
        retParamBlockArray = []
        while( self.s_iCanSendRequestParamCount > 0):
            # 检查时间符合？
            assignWebNameBlock = self.Viul_Internal_ParamBlock_ReadEach_CTUnit()
            if( assignWebNameBlock):
                self.s_iCanSendRequestParamCount -= 1   # 执行数－1

                # 提交，发送
                retParamBlockArray.append( assignWebNameBlock)
                # 加入参数到等待完成队列
                self.s_bstrPromptWaitFinishParamSignArray.append(assignWebNameBlock.s_bstrUniqueSign)

                CTYLB_Log.ShowLog(0, 'send-task-center',
                                  'prompt-run-param-block:%d [%s]' % (len(assignWebNameBlock.s_bstrDomainNameArray), assignWebNameBlock.s_bstrUniqueSign))
                msgObject={
                    "monitor_type":"send-task-block",
                    "level":"info",
                    "target":"",
                    "plugin_id":assignWebNameBlock.s_iRunPluginID,
                    "block_id":assignWebNameBlock.s_bstrUniqueSign,
                    "block_size":len(assignWebNameBlock.s_bstrDomainNameArray),
                    "free_size":0,
                    "wait_size":0,
				    "success_size":0,
                    "result_code":0,
                    "msg":""}
                CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
            else:
                break
        return retParamBlockArray

    # 系统调用，系统返回可发送参数数据
    def Sys_Reply_Plugin_RunParam_Count(self, iPluginID, iRemoteTaskCenterFreeCount):
        if( iPluginID == self.s_iRunPluginID):
            self.s_iCanSendRequestParamCount = iRemoteTaskCenterFreeCount
            CTYLB_Log.ShowLog( 0, 'recv-task-center', 'plugin:%d free:%d' % (iPluginID, iRemoteTaskCenterFreeCount))

            msgObject={
                    "monitor_type":"recv-task-block-free",
                    "level":"info",
                    "target":"",
                    "plugin_id":iPluginID,
                    "block_id":"",
                    "block_size":0,
                    "free_size":iRemoteTaskCenterFreeCount,
                    "wait_size":0,
				    "success_size":0,
                    "result_code":0,
                    "msg":""}
            CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)


    # 系统调用，这个参数标识是否我正在运行的参数
    def Sys_IsParamSign_MyRunningParamArray(self, bstrCheckParamSign):
        bstrCheckParamSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrCheckParamSign)

        bRetValue = False
        if( bstrCheckParamSign in self.s_bstrPromptWaitFinishParamSignArray):
            bRetValue = True
        return bRetValue

    # 系统调用，系统返回the paramblock is finish
    def Sys_Reply_ParamBlock_Result(self, bstrOrigParamBlockSign, iResultCode):
        bstrOrigParamBlockSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrOrigParamBlockSign)

        self.Viul_FinishParamBlock( bstrOrigParamBlockSign, iResultCode)
        if( bstrOrigParamBlockSign in self.s_bstrPromptWaitFinishParamSignArray):
            bRemove = False
            if( iResultCode == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish):
                bRemove = True
            elif( iResultCode == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish_Fail):
                bRemove = True
            if( bRemove):
                self.s_bstrPromptWaitFinishParamSignArray.remove( bstrOrigParamBlockSign)
                CTYLB_Log.ShowLog( 0,'param-reply', 'block %s run-finish. %d, still_buff_len:[%d]' % (
                    bstrOrigParamBlockSign, iResultCode, len( self.s_bstrPromptWaitFinishParamSignArray)) )

                msgObject={
                    "monitor_type":"block-finish-reply",
                    "level":"info",
                    "target":"",
                    "plugin_id":self.s_iRunPluginID,
                    "block_id":bstrOrigParamBlockSign,
                    "block_size":0,
                    "free_size":0,
                    "wait_size":len( self.s_bstrPromptWaitFinishParamSignArray),
			        "success_size":0,
                    "result_code":iResultCode,
                    "msg":""}
                CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
                pass
        pass

    # 系统调用，系统返回成功发送的结果个数
    def Sys_Reply_SendResultCount_Finish(self, iResultCount, bstrRequestCTUnitSign):
        CTYLB_Log.ShowLog( 0, 'recv-task-center', 'recv result count:%d' % (iResultCount))
        msgObject={
                    "monitor_type":"send-task-block-reply",
                    "level":"info",
                    "target":"",
                    "plugin_id":self.s_iRunPluginID,
                    "block_id":"",
                    "block_size":0,
                    "free_size":0,
                    "wait_size":0,
			        "success_size":iResultCount,
                    "result_code":0,
                    "msg":""}
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

    def Vilu_CloseQuit(self):
        pass


# tylb－bot 调度，异步通过服务器网络，获得下一步要发送的数据块，和数据
# start by sk. 170404
class CTYFBot_DTask_OPDB_Prompter(CTYBot_WebName_DTask2_Base):
    s_g_iStep_WaitConnect = 0
    s_g_iStep_SendObjRegister = 1
    s_g_iStep_Wait_ObjRegister_Reply = 2
    s_g_iStep_Can_SendParam = 2

    def __init__(self, hlSockMang, bstrResultAppName, bstrResultSubTaskName, bstrObjParamName, bstrParamDBName, bstrParamTableName, bstrParamContentField,
                 bstrParamSignIDField, iDestPluginID, iEachBlockCount=50):
        CTYBot_WebName_DTask2_Base.__init__(self, iDestPluginID, '', iEachBlockCount)
        self.s_bstrResultAppName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrResultAppName)
        self.s_bstrResultSubTaskName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrResultSubTaskName)

        self.s_bstrObjParamName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrObjParamName)
        self.s_bstrParamDBName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamDBName)
        self.s_bstrParamTableName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamTableName)
        self.s_bstrParamContentFieldName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamContentField)
        self.s_bstrIDSignFieldName = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamSignIDField)

        self.s_parentHLSockMang = hlSockMang
        self.s_connectOPDBSrv_Param_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_bstrTYFBot_OPDB_SrvName, g_i_ListenSock_TYFBot_OP_DB_Operate_ParamBlock)
        self.s_connectOPDBSrv_Result_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_bstrTYFBot_OPDB_SrvName, g_i_ListenSock_TYFBot_OP_DB_Operate_Result)

        self.s_iExecStep = CTYFBot_DTask_OPDB_Prompter.s_g_iStep_WaitConnect
        self.s_midRecvCanUseParamBlockArray = []   # 中间存储的参数块队列
        self.s_iCanSend_ReqParamCount = 0          # request param count, need send
        self.s_midStore_NeedSend_ResultData = []   # 中间存储的Result队列
        self.s_midStore_NeedSend_FinishParamBlockArray = []   # 中间存储需要发送的的参数结果队列

        pass

    def Vilu_CloseQuit(self):
        self.s_connectOPDBSrv_Param_Sock.Close()
        self.s_connectOPDBSrv_Result_Sock.Close()

    # 时间调度
    def Vilu_ExecTimerCheck(self):
        bRetValue = False
        if( self.s_connectOPDBSrv_Param_Sock.ExecNextCheck()):
            bRetValue = True
        if( self.s_connectOPDBSrv_Result_Sock.ExecNextCheck()):
            bRetValue = True

        # 接收参数管套的数据
        recvCTArray = self.s_connectOPDBSrv_Param_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            bstrPeerName, iPeerPort = self.s_parentHLSockMang.GetSockPeerAddr(self.s_connectOPDBSrv_Param_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                # CTYLB_Log.ShowLog(0, 'recv-reply', 'from [%s:%d] recv [%s]' % ( bstrPeerName, iPeerPort, eachUnit.s_bstrValue))
                self.__HandleRecvCTUnit( eachUnit)
        # 接收结果管套的数据
        recvCTArray = self.s_connectOPDBSrv_Result_Sock.PopRetriveRecvCTArray()

        if( self.s_connectOPDBSrv_Param_Sock.CanExecSendData()):
            needSendCTArray = []
            if( self.s_iExecStep == CTYFBot_DTask_OPDB_Prompter.s_g_iStep_WaitConnect):
                bstrCombArray = [self.s_bstrObjParamName, self.s_bstrParamDBName, self.s_bstrParamTableName, self.s_bstrParamContentFieldName,
                                self.s_bstrIDSignFieldName, b'0']
                bstrFixValue = b';'.join(bstrCombArray)
                sendCTUnit = CTYBot_CTUnit_CommonData()
                sendCTUnit.SetIntData(g_i_OpParamBlock_SubCmd_RegiestDbTableField_Param)
                sendCTUnit.SetStrData(bstrFixValue)
                needSendCTArray.append(sendCTUnit)

                self.s_iExecStep = CTYFBot_DTask_OPDB_Prompter.s_g_iStep_Wait_ObjRegister_Reply
            elif( self.s_iExecStep == CTYFBot_DTask_OPDB_Prompter.s_g_iStep_Can_SendParam):
                if( self.s_iCanSend_ReqParamCount>0):
                    sendCTUnit = CTYBot_CTUnit_CommonData()
                    sendCTUnit.SetIntData(g_i_OpParamBlock_SubCmd_GetRunParamBlock)
                    sendCTUnit.SetStrData(str(self.s_iCanSend_ReqParamCount))
                    sendCTUnit.SetParam(self.s_bstrObjParamName, str(self.s_iEachParamBlockCount).encode())
                    needSendCTArray.append(sendCTUnit)
                    self.s_iCanSend_ReqParamCount = 0  # after send, reset to 0

                sendCTUnit = CTYBot_CTUnit_CommonData()
                sendCTUnit.SetIntData(g_i_OpParamBlock_SubCmd_GetUnExecRecCount)
                sendCTUnit.SetParam(self.s_bstrObjParamName, b'')
                needSendCTArray.append(sendCTUnit)

                if( self.s_midStore_NeedSend_FinishParamBlockArray):
                    needSendCTArray.extend( self.s_midStore_NeedSend_FinishParamBlockArray)
                    self.s_midStore_NeedSend_FinishParamBlockArray = []

            if( not needSendCTArray):
                # 增加临时单元，方便会话的持续
                sendCTUnit = CTYBot_CTUnit_CommonData()
                needSendCTArray.append(sendCTUnit)
            self.s_connectOPDBSrv_Param_Sock.ExecSendData( needSendCTArray)

        if( self.s_connectOPDBSrv_Result_Sock.CanExecSendData()):
            needSendCTArray = self.s_midStore_NeedSend_ResultData
            if( not needSendCTArray):
                # 增加临时单元，方便会话的持续
                sendCTUnit = CTYBot_CTUnit_CommonData()
                needSendCTArray.append(sendCTUnit)
            else:
                self.s_midStore_NeedSend_ResultData = []
            self.s_connectOPDBSrv_Result_Sock.ExecSendData( needSendCTArray)

        return bRetValue

    # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无
    def Viul_Internal_ParamBlock_PrePare(self, bstrRegCenterID):
        pass

    # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容
    def Viul_Internal_ParamBlock_ReadEach_CTUnit(self):
        # 如果缓冲太满了，减少参数块读取的速度
        iCanRetriveCount = 0
        if( len(self.s_bstrPromptWaitFinishParamSignArray) > CTYBot_WebName_DTask2_Base.s_g_iMaxWaitParamStillCount):
            iCanRetriveCount = 1
        else:
            iCanRetriveCount = 10
        retWebBlockParam = self.__ASync_Retrive_OneParamBlock(iCanRetriveCount)
        return retWebBlockParam

    # 处理接收到数据单元
    def __HandleRecvCTUnit(self, recvCTUnit):
        if( recvCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if( recvCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Reply_RegiestDbTableField_Param):
                if( self.__IsRecvCTUnitObjNameMe(recvCTUnit)):
                    if( self.s_iExecStep == CTYFBot_DTask_OPDB_Prompter.s_g_iStep_Wait_ObjRegister_Reply):
                        self.s_iExecStep = CTYFBot_DTask_OPDB_Prompter.s_g_iStep_Can_SendParam
            elif (recvCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Reply_GetUnExecRecCount):
                if( self.__IsRecvCTUnitObjNameMe(recvCTUnit)):
                    iUnHandleCount = int(recvCTUnit.s_bstrValue)
                    iTotalCount = int(recvCTUnit.s_bstrParam2)
                    self.__HandleRecvParamUnExecCount( iUnHandleCount, iTotalCount)
            elif( recvCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Reply_GetRunParamBlock):
                if( self.__IsRecvCTUnitObjNameMe(recvCTUnit)):
                    self.__HandleRecvParamBlockUnit( recvCTUnit.s_bstrValue, recvCTUnit.s_bstrParam2)

    # 处理接收到未执行参数命令个数的数据包
    def __HandleRecvParamUnExecCount(self, iUnHandleCount, iTotalCount):
        CTYLB_Log.ShowLog(0, 'recv-param-count', '%s total:[%d], not run:[%d]' % (self.s_bstrObjParamName, iTotalCount, iUnHandleCount))

    # 判断接收到的单元，是否我单元对象名字相同
    def __IsRecvCTUnitObjNameMe(self, ctUnit):
        bRetValue = False
        if( CTYLB_MainSys_MiscFunc.SafeCompareAnyStrValue( ctUnit.s_bstrParam1, self.s_bstrObjParamName)):
            bRetValue = True
        return bRetValue

    # 处理接收到的参数块
    def __HandleRecvParamBlockUnit(self, bstrParamContentLine, bstrParamSignID):
        bstrParamContentLine = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamContentLine)
        bstrParamSignID = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamSignID)

        bstrBlockArray = bstrParamContentLine.split(b'\n')
        if( bstrBlockArray):
            assignWebNameBlock = CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock()
            # 提交到任务模块
            assignWebNameBlock.s_iRunPluginID = self.s_iRunPluginID
            assignWebNameBlock.s_bstrDomainNameArray = bstrBlockArray
            assignWebNameBlock.s_bstrUniqueSign = bstrParamSignID
            # 提交，发送
            self.s_midRecvCanUseParamBlockArray.append(assignWebNameBlock)

    # [子类可继承实现] - 异步读取可用参数块. 返回：webNameParamBlock，返回空表示无内容
    def __ASync_Retrive_OneParamBlock(self, iMaxRetriveCount):
        retWebNameParamBlock = None
        if( self.s_midRecvCanUseParamBlockArray):
            retWebNameParamBlock = self.s_midRecvCanUseParamBlockArray.pop(0)
        else:
            # 设置发送请求参数块的值，等待调度发送
            self.s_iCanSend_ReqParamCount = iMaxRetriveCount

        return retWebNameParamBlock

    # [子类可继承实现] - paramblock is finish
    def Viul_FinishParamBlock(self, bstrOrigParamBlockSign, iResultCode):
        bstrOrigParamBlockSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrOrigParamBlockSign)

        sendCTUnit = CTYBot_CTUnit_CommonData()
        sendCTUnit.SetIntData(g_i_OpParamBlock_SubCmd_Finish_ParamBlock)
        sendCTUnit.SetStrData( bstrOrigParamBlockSign)
        sendCTUnit.SetParam(self.s_bstrObjParamName, str(iResultCode))
        self.s_midStore_NeedSend_FinishParamBlockArray.append(sendCTUnit)

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, bstrParamSign, iReplyPluginID, bstrOrigTitleDomain, bstrResult):
        bstrParamSign = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrParamSign)
        bstrOrigTitleDomain = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrOrigTitleDomain)
        bstrResult = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrResult)

        contentArray = [self.s_bstrResultAppName, self.s_bstrResultSubTaskName, bstrParamSign]
        bstrParam2Content = g_bstr_ResultContentSplit.join(contentArray)

        sendCTUnit = CTYBot_CTUnit_CommonData()
        sendCTUnit.SetIntData(g_i_OpResult_SubCmd_AddResult)
        sendCTUnit.SetStrData( bstrResult)
        sendCTUnit.SetParam(bstrOrigTitleDomain, bstrParam2Content)
        self.s_midStore_NeedSend_ResultData.append(sendCTUnit)
        pass
    pass

# ################################################################################################
#   下面是节点系统单元实现
#   每个单元读取100个域名，发送到远端。从文件中每次读取100个，发送给 任务中心。
#      发送结果的模式如下：先发送开始，再每个域名扫描结果逐个返回，再发送完成。
#         开始，和完成的 数据包为 int 类型的 CTYBot_CTUnit_CommonData, param1 为结果的uniqueid，int值＝0，表示开始，int=1表示结束
#      最多发送100个单元，收到结果后，再发送下一个结果块。
# ################################################################################################

# 天元机器人－分布任务提交－框架管理
# start by sk. 170226
class CTYBot_Sock_D_PromptTask:
    # 远程管套定义
    s_g_iTaskMang_Listen_Port_PromptTask = 3   # 任务管理中心，对任务提交者的监听端口

    def __init__(self, ustrCfgFileName, ustrDbFileName):
        ustrCfgFileName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrCfgFileName)
        ustrDbFileName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrDbFileName)

        # 设置运行任务提交
        self.s_RunnDTaskArray = []   # 正在运行的任务队列

        # 创建机器人框架
        self.s_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(ustrCfgFileName, ustrDbFileName)
        # 设置默认环境处理
        # self.s_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
        # 准备运行
        self.s_LessTYLB_Bot_FrameThread.Prepare_Start()
        self.s_strSelfID = self.s_LessTYLB_Bot_FrameThread.GetMyName()
        # 注册 单元到达的通知，HLSession的新数据单元创建
        self.s_LessTYLB_Bot_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                           CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult_V2,
                                                           CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_V2_PingTraceWebCrawl,
                                                           CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_V2_ReportResult)
        self.s_LessTYLB_Bot_FrameThread.RegisterNewCTUnit( CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1,
                                                           CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult,
                                                           CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl,
                                                           CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_ReportResult)

        # 获得管套管理对象
        self.s_hlSockMang = self.s_LessTYLB_Bot_FrameThread.s_HLSockMang
        # 读取配置参数
        ustrTaskRegCenterID = self.s_LessTYLB_Bot_FrameThread.s_execTYLB_Bot_Sample.ReadIniSectionValue( ustrCfgFileName,
                                                            u'client', u'taskcenter_id',
                                                            CTYLB_Bot_BaseDef.s_g_strBotName_TaskRegCenter_sk_v1)
        self.s_bstrTaskRegCenterID = CTYLB_MainSys_MiscFunc.SafeGetUTF8(ustrTaskRegCenterID)
        # 创建连接管套
        self.s_x_TaskRegCenter_Sock = CTYFBot_OpSession_ConnectSock(self.s_hlSockMang, self.s_bstrTaskRegCenterID,
                                                                    self.s_g_iTaskMang_Listen_Port_PromptTask)
        pass

    # 提交分布任务进行运行， 参数1-dRunTask = CTYBot_DTask_Base 单元
    # start by sk. 170226
    def PromptDTask(self, dRunTask):
        self.s_RunnDTaskArray.append( dRunTask)
        pass

    # 运行前的准备 - 子类可继承
    # start by sk. 170226
    def Vilu_Prepare_Run(self):
        # 对每个任务的准备函数进行调用
        for eachDTask in self.s_RunnDTaskArray:
            eachDTask.Viul_Internal_ParamBlock_PrePare(self.s_bstrTaskRegCenterID)
        pass

    # 单位时间调度 - 子类可继承
    # start by sk. 170226
    def Vilu_TimerCheck(self):
        bRetValue = False

        # 对每个扫描任务进行检查调度
        for eachPromptTask in self.s_RunnDTaskArray:
            if( eachPromptTask.Vilu_ExecTimerCheck()):
                bRetValue = True

        if( self.s_x_TaskRegCenter_Sock.ExecNextCheck()):
            bRetValue = True
        if( self.s_x_TaskRegCenter_Sock.CanExecSendData()):
            bRetValue = True
            # 对每个任务的准备函数进行调用
            needPromptParamArray = []
            for eachDTask in self.s_RunnDTaskArray:
                curParamArray = eachDTask.Sys_Schedule_RequestParamBlock()
                needPromptParamArray.extend(curParamArray)
                # 请求插件ID的空余数量
                newCommDataCTUnit = CTYBot_CTUnit_CommonData()
                newCommDataCTUnit.SetIntData(CTYBot_CTUnit_CommonData.s_g_iIntValue_Query_PluginID_Run_ParamBlock_Count)
                newCommDataCTUnit.SetParam(str(eachDTask.s_iRunPluginID).encode(), b'')
                needPromptParamArray.append(newCommDataCTUnit)
            # 提交发送
            if( not needPromptParamArray):
                newCommDataCTUnit = CTYBot_CTUnit_CommonData()
                needPromptParamArray.append( newCommDataCTUnit)
            self.s_x_TaskRegCenter_Sock.ExecSendData( needPromptParamArray)
            pass

        recvCTArray = self.s_x_TaskRegCenter_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bRetValue = True
            bstrPeerName, iPeerPort = self.s_hlSockMang.GetSockPeerAddr(self.s_x_TaskRegCenter_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                # CTYLB_Log.ShowLog(0, 'data-receive', 'from [%s:%d] recv [%d]' % (strPeerName, iPeerPort, eachUnit.s_iMyDataType))
                msgObject = {
                    "monitor_type": "status",
                    "level": "info",
                    "target": "",
                    "plugin_id": -1,
                    "block_id": "",
                    "block_size": 0,
                    "free_size": 0,
                    "wait_size": 0,
                    "success_size": 0,
                    "result_code": 0,
                    "msg": "PLC received <%d> bytes from <%s:%d>" % (eachUnit.s_iMyDataType, bstrPeerName, iPeerPort)
                }
                CTYLB_Log.ShowMonitor(msgType="PLC", msgObject=msgObject)

                if (eachUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
                    self.HandleRecv_CommonData(bstrPeerName, eachUnit)
                elif (eachUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1):
                    if (eachUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult_V2):
                        self.HandleRecv_Result_V2(bstrPeerName, eachUnit)
                        self.s_x_TaskRegCenter_Sock.SetNextTempSendWaitTick(0)   # 有结果到达，可能还有结果数据，这时候不等待，立即再发送获取
                    elif (eachUnit.s_iBotCmd_Main == CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult):
                        self.HandleRecv_Result(bstrPeerName, eachUnit)
                        self.s_x_TaskRegCenter_Sock.SetNextTempSendWaitTick(0)   # 有结果到达，可能还有结果数据，这时候不等待，立即再发送获取
                else:
                    CTYLB_Log.ShowLog(1, 'data-receive', 'Unknown packet:%d-%d-%d' % (eachUnit.s_iMyDataType,
                                                                                      eachUnit.s_iBotCmd_Main,
                                                                                      eachUnit.s_iBotCmd_Sub))
                    msgObject = {
                        "monitor_type": "status",
                        "level": "warning",
                        "target": "",
                        "plugin_id": -1,
                        "block_id": "",
                        "block_size": 0,
                        "free_size": 0,
                        "wait_size": 0,
                        "success_size": 0,
                        "result_code": 0,
                        "msg": "PLC unknown package received <Type:%d,MainCMD:%d,SubCMD:%d>"
                               % (eachUnit.s_iMyDataType, eachUnit.s_iBotCmd_Main, eachUnit.s_iBotCmd_Sub)
                    }
                    CTYLB_Log.ShowMonitor(msgType="PLC", msgObject=msgObject)

                pass

        return bRetValue

    # 处理接收数据的回调 － 通用数据 - CTYBot_CTUnit_CommonData
    # start by sk. 170226
    def HandleRecv_CommonData(self, bstrFromUser, commuCTUnit):
        if (commuCTUnit.s_iType == CTYBot_CTUnit_CommonData.s_g_iType_int):
            bHandleParamResult = False  # 处理参数结果
            bReplyBlockCount = False   # 处理块个数
            bCenterReplyResult = False  # 处理中心回应结果到达

            if (commuCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish):
                bHandleParamResult = True
            elif(commuCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_BCast_Fail_No_Host):
                bHandleParamResult = True
            elif(commuCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Task_Finish_Fail):
                bHandleParamResult = True
            elif ( commuCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Reply_PluginID_Run_ParamBlock_Count):
                bReplyBlockCount = True
            elif ( commuCTUnit.s_iValue == CTYBot_CTUnit_CommonData.s_g_iIntValue_Reply_TaskCenter_Send_Promptor_Result_Finish):
                # [任务中心->提交者] 返回当前提交者的结果个数。strParam1=结果个数, strParam2=请求包标识符
                bCenterReplyResult = True

            # 处理块个数
            if( bReplyBlockCount):
                try:
                    iQueryPluginID = int(commuCTUnit.s_bstrParam1)
                    iCanRunCount = int(commuCTUnit.s_bstrParam2)
                    for eachDTask in self.s_RunnDTaskArray:
                        eachDTask.Sys_Reply_Plugin_RunParam_Count( iQueryPluginID, iCanRunCount)
                except Exception as e:
                    pass

            # 处理参数结果
            if( bHandleParamResult):
                for eachDTask in self.s_RunnDTaskArray:
                    if (eachDTask.Sys_IsParamSign_MyRunningParamArray(commuCTUnit.s_bstrParam1)):
                        eachDTask.Sys_Reply_ParamBlock_Result(commuCTUnit.s_bstrParam1, commuCTUnit.s_iValue)
                        break

            # 处理结果到达完成
            if( bCenterReplyResult):
                iResultCount = int(commuCTUnit.s_bstrParam1)
                bstrOrigSign = commuCTUnit.s_bstrParam2
                for eachDTask in self.s_RunnDTaskArray:
                    eachDTask.Sys_Reply_SendResultCount_Finish(iResultCount, bstrOrigSign)
            pass

    # 处理接收数据的回调 － 结果数据 - CTYBot_CTUnit_TaskRegCenter_ReportResult
    # start by sk. 170226
    def HandleRecv_Result(self, bstrFromName, resultCTUnit):
        for eachDTask in self.s_RunnDTaskArray:
            if( eachDTask.IsParamBlockSignInMyArray(resultCTUnit.s_bstrOrigTaskUniqueSign)):
                bstrFixOrigResult = CTYLB_P2P_ContentUnit_Base_bytes.SafeConvertBase64Str_ToUTF8( resultCTUnit.s_bstrRunResult)
                eachDTask.Viul_Notify_Recv_RunResult( resultCTUnit.s_bstrOrigTaskUniqueSign,
                                                      resultCTUnit.s_iExecPluginID,
                                                      resultCTUnit.s_bstrExecDomainName,
                                                      bstrFixOrigResult)
                break
        pass

    # 处理接收数据的回调 － 结果数据V2 - CTYBot_CTUnit_TaskRegCenter_ReportResult_V2
    # start by sk. 170226
    def HandleRecv_Result_V2(self, bstrFromName, resultV2CTUnit):
        for eachDTask in self.s_RunnDTaskArray:
            if( eachDTask.IsParamBlockSignInMyArray(resultV2CTUnit.s_bstrOrigTaskUniqueSign)):
                for eachSubUnit in resultV2CTUnit.s_subResultUnitArray:
                    bstrFixOrigResult = CTYLB_P2P_ContentUnit_Base_bytes.SafeConvertBase64Str_ToUTF8(
                        eachSubUnit.s_bstrRunResult)
                    eachDTask.Viul_Notify_Recv_RunResult( resultV2CTUnit.s_bstrOrigTaskUniqueSign,
                                                          eachSubUnit.s_iExecPluginID,
                                                          eachSubUnit.s_bstrExecDomainName,
                                                          bstrFixOrigResult)
                break
        pass

    def StopQuit(self):
        self.s_x_TaskRegCenter_Sock.Close()
        self.s_LessTYLB_Bot_FrameThread.SafeStop()
