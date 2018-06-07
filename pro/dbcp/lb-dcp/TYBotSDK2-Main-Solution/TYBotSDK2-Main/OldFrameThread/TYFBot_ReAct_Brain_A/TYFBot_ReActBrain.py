# -*- coding:UTF-8 -*- 放到第一行标记
# TYFBot_ReActBrain.py 操作 行动大脑 功能机器人
#
# start by sk. 170412

from datetime import datetime
from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
from TYBotSDK2.BotBase.Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_MainConn
import time
import os
from Operate_Store_Real import CTYOp_ReActBrain_Store
from Sk_LB_db_FBot_ReactBrain_Real import CSkLBDB_ea_brain_chatcontent, CSkLBDB_ea_brain_envirument, CSkLBDB_ea_brain_usermang,\
    CSkLBDB_ea_brain_exec_task
from Track_Chat_Analys import CTYReActBrainBot_Track_Checker
import json

# ################################################################################################
#   下面是节点系统单元实现
# ################################################################################################

# 单位时间的回调功能，如果有内容执行，则返回True，空闲，则返回False
# start by sk. 170222
def TimerCheck_PrepareSendContent():
    bRetValue = False  # 返回值。

    return bRetValue

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = u'TianYuan Function Bot - Real Action Brain'
g_mainOperate_RealActionDB = CSkLBDB_MainConn()    # 链接行动内容 数据库

g_str_TY2FuncBot_MiscCollect_DBName = u'ty2_funcbot_misc_collect'

# 下面复制定义微信机器人操作相关管套。
g_strOPWeiXinSrvName = u'TYFBot_OP_WeiXin'
g_i_ListenSock_TYFBot_OP_WeiXin_Operate = 7  # 监听管套，操作微信机器人

g_i_OpWeiXin_SubCmd_GetLoginCode = 701  # 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Reply_GetLoginCode = 702  # 回复 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Get_ChatContent = 703  # 获得聊天的内容
g_i_OpWeiXin_SubCmd_Reply_Get_ChatText = 704  # 回复 获得聊天的内容
g_i_OpWeiXin_SubCmd_Send_ChatContent = 705  # 发送要和别人说的内容
g_i_OpWeiXin_SubCmd_Reply_SendChatContent = 706  # 回复 发送要和别人说的内容
g_str_ContentSplit = u'(;1-@;)'   # 内容的分隔符


# 下面定义本机器人的任务执行管套
g_i_ListenSock_TYFBot_ReAction_Brain_Operate = 9   # 监听管套，操作行动机器人的任务

g_i_OpAction_SubCmd_RequestExec = 901   # 申请可以执行的子任务
g_i_OpAction_SubCmd_Reply_RequestExec = 902  # 回复 申请子任务
g_i_OpAction_SubCmd_ReplyExecResult = 903   # 执行子任务后，返回执行结果
g_i_OpAction_SubCmd_Reply_ReplyExecResult = 904   # 回复 返回执行结果

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting")
    g_bSysRunning = False

####################################################################################
#  下面实现参数-数据库功能，和结果数据库功能的测试。
####################################################################################

# 获得要发送给参数管理的数据
# start by sk. 170412
def HandleSend_OpWeiXin_Srv():
    retSendUnitArray = []

    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpWeiXin_SubCmd_Get_ChatContent)
    retSendUnitArray.append(sendCTUnit)

    # 有需要发送的内容吗？提交进行发送
    while(True):
        strExecMsgContent, strExecToUser, iExecUserType, iExecContentType, strToGroupName = CTYOp_ReActBrain_Store.PopNextNeedSendWeiXinMsg(g_mainOperate_RealActionDB.s_DbConn)
        if( strExecMsgContent):
            sendCTUnit = CTYBot_CTUnit_CommonData()
            sendCTUnit.SetIntData(g_i_OpWeiXin_SubCmd_Send_ChatContent)
            # 输入: strValue = 要发送的内容，iValue = 705，strParam1 = 要发送对象的ID或者群名，strParam2 = 内容类型 - 文字 - 图片 < 分割 > 是个人，还是群
            sendCTUnit.SetStrData(strExecMsgContent)
            strParam2Array = [str(iExecContentType), str(iExecUserType), strToGroupName]
            sendCTUnit.SetParam( strExecToUser, g_str_ContentSplit.join(strParam2Array))
            retSendUnitArray.append(sendCTUnit)
        else:
            break
    return retSendUnitArray

# 获得 获得 聊天内容
# 	返回: strValue=别人和我说话的文字内容。iValue=704，strParam1=说话者的ID，strParam2=说话的时间<分割>内容类型-文字-图片<分割>是个人
#           还是群<分割>如果是群，群名是什么
# start by sk. 170412
def Handle_Recv_SubCmd_Reply_GetChat(ustrChatContent, ustrUserName, ustrTimeTypeInfo):
    # 获得用户的环境记录。是不是和我说话，如果不是，那么，忽略。如果和我说话，那么，又要处理
    strTimeTypeInfoArray = ustrTimeTypeInfo.split( g_str_ContentSplit)
    if( len(strTimeTypeInfoArray) >= 4):
        strContentTime = strTimeTypeInfoArray[0]
        contentTime = datetime.strptime( strContentTime, u'%Y-%m-%d %H:%M:%S')
        iContentType = int(strTimeTypeInfoArray[1])
        iUserGroupType = int(strTimeTypeInfoArray[2])
        strFromGroupName = strTimeTypeInfoArray[3]

        #CTYLB_Log.ShowLog(0, 'Recv-chat-content', "recv [%s]: Group:[%d][%s] Type:[%d] [%s] [%s]" % (strUserName, iUserGroupType, strFromGroupName,
        #                                                                                             iContentType, strTimeTypeInfo, strChatContent))

        iUserEnvirumentID = CTYOp_ReActBrain_Store.GetUserChatEnvirumentID( g_mainOperate_RealActionDB.s_DbConn, ustrUserName, iUserGroupType, strFromGroupName)
        if( iUserEnvirumentID > 0):
            iChatRecID = CSkLBDB_ea_brain_chatcontent.AddNewdRec(g_mainOperate_RealActionDB.s_DbConn, iUserEnvirumentID,
                                                                 ustrChatContent, iContentType, CTYOp_ReActBrain_Store.s_g_iDirection_From_User_To_Brain, contentTime)

    pass

# 获得要发送给参数管理的数据
# start by sk. 170412
def HandleRecv_OPWeiXin_CTUnit( recvCTUnit):
    if (recvCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_GetLoginCode):
            pass
        elif (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_Get_ChatText):
            Handle_Recv_SubCmd_Reply_GetChat( recvCTUnit.s_bstrValue.decode(), recvCTUnit.s_bstrParam1.decode(),
                                              recvCTUnit.s_bstrParam2.decode())
            pass
        elif (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_SendChatContent):
            # CTYLB_Log.ShowLog(0, 'recv-wx', 'recv sendtext-reply:[%s] param: [%s] : [%s]'
            #                  % (recvCTUnit.s_bstrValue, recvCTUnit.s_bstrParam1, recvCTUnit.s_bstrParam2))
            pass
    pass


# ################################################################################################
#   下面是主命令通信接口 实现
#  g_i_OpAction_SubCmd_RequestExec = 901   # 申请可以执行的子任务
#  g_i_OpAction_SubCmd_ReplyExecResult = 903   # 执行子任务后，返回执行结果
# ################################################################################################


g_str_runParam_AlarmCount = u'AlarmCount'
g_str_runParam_LastAlarmTime = u'LastAlarm'

g_str_Alarm_origParam_Time = u'NotifyTime'
g_str_Alarm_origParam_AlarmContent = u'Content'

g_str_TotalParam_OrigParam = u'OrigParam'
g_str_TotalParam_RunTimeParam = u'RunTimeParam'

# 执行结果返回的定义
g_i_Code_Finish_Stop_Task = 0      # 0 –完成，可以停止本次任务；
g_i_Code_Finish_Need_Run_Update_RunParam = 1    # 1-本次完成，下次还要继续运行，需要更新运行时参数
g_i_Code_Finish_Need_Run = 2      # 2-本次完成，还要继续运行，不修改参数内容

g_str_Alarm_Reply_V_ResultCode = u'code'
g_str_Alarm_Reply_V_RunResult = u'RunResult'
g_str_Alarm_Reply_V_NeedUpdateRunParam = u'NeedUpdateRunParam'
g_str_Alarm_Reply_V_SendUserContent = u'SendUserContent'

g_str_Alarm_Reply_P1_RunTypeID = u'RunTypeID'
g_str_Alarm_Reply_P1_TaskRecID = u'TaskRecID'


# 处理 操作 大脑的行动任务执行子命令：请求执行任务
#  	输入: iValue=901。strParam1=执行类型ID
#  	返回: iValue=902。strValue=json:传入参数|运行时参数内容，strParam1=执行类型ID，strParam2=任务ID记录值
#  	执行类型=’1’，表示显示任务。
# start by sk. 170413
def SubHandle_OPActionBrain_RequestExec(strPeerName, strRequestTaskType):
    retCTUnitArray = []
    # 搜索记录表中，某个类型的任务
    iExecTaskTypeID = int(strRequestTaskType)
    iExecRecIDArray = CSkLBDB_ea_brain_exec_task.GetRecList_By_TaskTypeID_ExecStatus( g_mainOperate_RealActionDB.s_DbConn,
                                                                                      iExecTaskTypeID, CTYOp_ReActBrain_Store.s_g_iStatus_Free)
    for iEachExecRecID in iExecRecIDArray:
        iExecBelongEnviruID, iExecTaskTypeID, strExecContent, strExecParam, strExecWhoRequestName, execCreateTime,\
            execRequestExecTime, iExecRequestExecStatus, iExecTaskRunAlways, execLastCheckTime, strExecTaskRunParam =\
            CSkLBDB_ea_brain_exec_task.ReadByRecID( g_mainOperate_RealActionDB.s_DbConn, iEachExecRecID)
        valueCollect = { g_str_TotalParam_OrigParam : strExecParam,
                         g_str_TotalParam_RunTimeParam : strExecTaskRunParam}
        strRunValue = json.dumps(valueCollect)

        # 构建单元数据包
        sendCTUnit = CTYBot_CTUnit_CommonData()
        sendCTUnit.SetIntData(g_i_OpAction_SubCmd_Reply_RequestExec)
        sendCTUnit.SetStrData( strRunValue)
        sendCTUnit.SetParam(strRequestTaskType, str(iEachExecRecID))
        retCTUnitArray.append(sendCTUnit)

        # 搜索到，分配，设置正在执行的状态
        CSkLBDB_ea_brain_exec_task.Update_ExStatus( g_mainOperate_RealActionDB.s_DbConn, iEachExecRecID, CTYOp_ReActBrain_Store.s_g_iStatus_Running)
        CSkLBDB_ea_brain_exec_task.Update_RequestName(g_mainOperate_RealActionDB.s_DbConn, iEachExecRecID, strPeerName)
        CSkLBDB_ea_brain_exec_task.Update_LastCheckTime(g_mainOperate_RealActionDB.s_DbConn, iEachExecRecID)
    return retCTUnitArray

# 处理 操作 大脑的行动任务执行子命令：回复任务的执行结果
#  	输入: iValue=903，strValue=json:结果code|执行的结果内容|需要更新的运行时参数|需要发送给用户的内容。strParam1=执行类型ID|任务ID，strParam2=结果附加参数
#  	返回: iValue=904。无
#  	结果code: 0 –完成，可以停止本次任务；1-本次完成，下次还要继续运行，需要更新运行时参数；2-本次完成，还要继续运行，不修改参数内容
#  	返回: iValue=904。无
# start by sk. 170413
def SubHandle_OPActionBrain_ReplyExecResult(strPeerName, strTaskValue, strTaskTypeIDRecID, strTaskResultParam):
    strPeerName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPeerName)
    strTaskValue = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTaskValue)
    strTaskTypeIDRecID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTaskTypeIDRecID)
    strTaskResultParam = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTaskResultParam)
    # 提取参数结果内容
    paramCollect = json.loads(strTaskValue)
    iExecResultCode = paramCollect[g_str_Alarm_Reply_V_ResultCode]
    strRunResult = paramCollect[g_str_Alarm_Reply_V_RunResult]
    strNeedUpdateRunParam = paramCollect[g_str_Alarm_Reply_V_NeedUpdateRunParam]
    strNeedSendUserContent = paramCollect[g_str_Alarm_Reply_V_SendUserContent]

    paramCollect = json.loads(strTaskTypeIDRecID)
    iRunTaskTypeID = paramCollect[g_str_Alarm_Reply_P1_RunTypeID]
    iTaskRecID = paramCollect[g_str_Alarm_Reply_P1_TaskRecID]

    iExecBelongEnviruID, iExecTaskTypeID, strExecContent, strExecParam, strExecWhoRequestName, execCreateTime, \
    execRequestExecTime, iExecRequestExecStatus, iExecTaskRunAlways, execLastCheckTime, strExecTaskRunParam = \
        CSkLBDB_ea_brain_exec_task.ReadByRecID(g_mainOperate_RealActionDB.s_DbConn, iTaskRecID)

    iDestSetStatus = CTYOp_ReActBrain_Store.s_g_iStatus_Finish
    if( iExecResultCode == g_i_Code_Finish_Stop_Task):
        # 0 –完成，可以停止本次任务；
        pass
    elif( iExecResultCode == g_i_Code_Finish_Need_Run_Update_RunParam):
        # 1-本次完成，下次还要继续运行，需要更新运行时参数
        iDestSetStatus = CTYOp_ReActBrain_Store.s_g_iStatus_Free
        CSkLBDB_ea_brain_exec_task.Update_RunParam( g_mainOperate_RealActionDB.s_DbConn, iTaskRecID, strNeedUpdateRunParam)
        pass
    elif( iExecResultCode == g_i_Code_Finish_Need_Run):
        # 2-本次完成，还要继续运行，不修改参数内容
        iDestSetStatus = CTYOp_ReActBrain_Store.s_g_iStatus_Free
        pass

    # 发送内容用户，提交到微信输出表
    if( strNeedSendUserContent):
        CTYReActBrainBot_Track_Checker.AddReplyTextInfoToUser( g_mainOperate_RealActionDB.s_DbConn, iExecBelongEnviruID, strNeedSendUserContent)

    # 更新任务状态
    CSkLBDB_ea_brain_exec_task.Update_ExStatus(g_mainOperate_RealActionDB.s_DbConn, iTaskRecID, iDestSetStatus)
    CSkLBDB_ea_brain_exec_task.Update_LastCheckTime(g_mainOperate_RealActionDB.s_DbConn, iTaskRecID)

    # 构建返回数据包
    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpAction_SubCmd_Reply_ReplyExecResult)
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray


# 接收到 操作 大脑的行动任务执行 管套数据单元的处理
# start by sk. 170412
def HandleRecvCTUnit_OPActionBrain(hlSockMang, iEachAcceptSock, ctUnitArray):
    strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iEachAcceptSock)
    retDataArray = []
    for eachCTUnit in ctUnitArray:
        eachRetCommCTUnit = None
        eachRetCommCTUnitArray = []
        if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if( eachCTUnit.s_iValue == g_i_OpAction_SubCmd_RequestExec):
                eachRetCommCTUnitArray = SubHandle_OPActionBrain_RequestExec(strPeerName, eachCTUnit.s_strParam1)
            elif( eachCTUnit.s_iValue == g_i_OpAction_SubCmd_ReplyExecResult):
                eachRetCommCTUnitArray = SubHandle_OPActionBrain_ReplyExecResult(strPeerName, eachCTUnit.s_strValue,
                                                                                 eachCTUnit.s_strParam1, eachCTUnit.s_strParam2)

        if( eachRetCommCTUnit):
            retDataArray.append(eachRetCommCTUnit)
        if( eachRetCommCTUnitArray):
            retDataArray.extend( eachRetCommCTUnitArray)
    # 如果没有内容，那么，放一个空单元
    if( not retDataArray):
        sendCTUnit = CTYBot_CTUnit_CommonData()
        retDataArray.append(sendCTUnit)
    hlSockMang.PassiveSend_To_AcceptSock(iEachAcceptSock, retDataArray)
    pass


# ################################################################################################
#   主程序入口 实现
# ################################################################################################
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

    # 链接主数据库
    g_mainOperate_RealActionDB.ReConnect(u"127.0.0.1", 3306, u"lessnet", u",,,,,...../////", g_str_TY2FuncBot_MiscCollect_DBName)

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()
    g_strSelfID = g_LessTYLB_Bot_FrameThread.GetMyName()

    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang

    # 连接 weixin-op 机器人
    # 获得管套管理对象, 操作结果，操作参数块
    connect_weixin_op_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_strOPWeiXinSrvName, g_i_ListenSock_TYFBot_OP_WeiXin_Operate,5,300)
    CTYLB_Log.ShowLog(0, u'exec', u'start HLSock connect remote [%s:%d] op-weixin Func' % (g_strOPWeiXinSrvName, g_i_ListenSock_TYFBot_OP_WeiXin_Operate))

    # 创建行动监听管套
    iOP_ActionBrain_ListenSock = hlSockMang.CreateListenSock( g_i_ListenSock_TYFBot_ReAction_Brain_Operate)
    iAccept_OP_ActionBrain_Sock_Array = []

    reactBotTrackChecker = CTYReActBrainBot_Track_Checker()

    while(g_bSysRunning):
        bTaskBusy = False

        # 下面执行 对微信新内容的通信检查
        if( connect_weixin_op_Sock.ExecNextCheck()):
            bTaskBusy = True

        if( connect_weixin_op_Sock.CanExecSendData()):
            execSendCTArray = HandleSend_OpWeiXin_Srv()
            connect_weixin_op_Sock.ExecSendData( execSendCTArray)
            bTaskBusy = True

        recvCTArray = connect_weixin_op_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connect_weixin_op_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                # CTYLB_Log.ShowLog(0, 'recv-WeiXin-reply', 'from [%s:%d] recv len:[%d]' % ( strPeerName, iPeerPort, len(eachUnit.s_strValue)))
                HandleRecv_OPWeiXin_CTUnit( eachUnit)

        # 下面执行 对 执行行动大脑 监听服务的 通信检查
        # 检查新接收的连接
        iNewAcceptSockIndex = hlSockMang.ExAcceptNewListenArriveSock( iOP_ActionBrain_ListenSock)
        if( iNewAcceptSockIndex):
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSockIndex)
            CTYLB_Log.ShowLog(0, u'op-Action-Brain', u'from [%s:%d] new HLConnect %d accept.' % (strPeerName, iPeerPort, iNewAcceptSockIndex))
            bTaskBusy = True
            iAccept_OP_ActionBrain_Sock_Array.append( iNewAcceptSockIndex)
            pass
        for iEachAcceptSock in iAccept_OP_ActionBrain_Sock_Array:
            # 检查有否新数据包到达
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachAcceptSock)
            if( not bSockExist):
                # 检查是否管套已经关闭
                CTYLB_Log.ShowLog(0, u'op-Action-Brain', u'sock %d closed' % (iEachAcceptSock))
                iAccept_OP_ActionBrain_Sock_Array.remove( iEachAcceptSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    HandleRecvCTUnit_OPActionBrain( hlSockMang, iEachAcceptSock, ctUnitArray)

        if(CTYReActBrainBot_Track_Checker.TimerCheck_ChatContent(g_mainOperate_RealActionDB.s_DbConn)):
            bTaskBusy = True
        if(reactBotTrackChecker.TimerCheck_ScheduleAlwaysTask(g_mainOperate_RealActionDB.s_DbConn)):
            bTaskBusy = True
        if(reactBotTrackChecker.TimerCheck_UserMoodCheckTime(g_mainOperate_RealActionDB.s_DbConn)):
            bTaskBusy = True

        if( not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    connect_weixin_op_Sock.Close()
    g_LessTYLB_Bot_FrameThread.SafeStop()

    CTYLB_Log.ShowLog(0, u'Main', u'bye bye')

