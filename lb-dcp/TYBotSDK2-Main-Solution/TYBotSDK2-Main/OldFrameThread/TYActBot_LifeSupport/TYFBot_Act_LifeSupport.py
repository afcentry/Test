# -*- coding:UTF-8 -*- 放到第一行标记
# TYFBot_Act_LifeSupport.py 行动机器人，生活支持助手实现
#
# start by sk. 170413

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
import time
from datetime import datetime
import random
import os
import json

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = u'TianYuan Action Bot - Life Support'

g_str_RealAction_BrainBot_Name = u'TYFBot_ReAct_Brain_A'
g_i_ListenSock_TYFBot_ReAction_Brain_Operate = 9   # 监听管套，操作行动机器人的任务

g_i_OpAction_SubCmd_RequestExec = 901   # 申请可以执行的子任务
g_i_OpAction_SubCmd_Reply_RequestExec = 902  # 回复 申请子任务
g_i_OpAction_SubCmd_ReplyExecResult = 903   # 执行子任务后，返回执行结果
g_i_OpAction_SubCmd_Reply_ReplyExecResult = 904   # 回复 返回执行结果

g_bstr_ContentSplit = b'(;1-@;)'   # 内容的分隔符
g_ustr_TYLB_TimeFormat = u'%Y-%m-%d %H:%M:%S'   # 时间格式
# 执行类型ID-生活助手-闹钟方式提醒
g_i_ExecTypeID_LifeSupport_AlarmRing = 1000001
g_i_Max_Notify_Count = 5   # 最大闹钟次数
g_i_Min_Notify_TimeDiff = 120  # 每60秒提醒一次

g_ustr_runParam_AlarmCount = u'AlarmCount'
g_ustr_runParam_LastAlarmTime = u'LastAlarm'

g_str_Alarm_origParam_Time = u'NotifyTime'
g_str_Alarm_origParam_AlarmContent = u'Content'

g_str_TotalParam_OrigParam = u'OrigParam'
g_str_TotalParam_RunTimeParam = u'RunTimeParam'


# 执行结果返回的定义
g_i_Code_Finish_Stop_Task = 0      # 0 –完成，可以停止本次任务；
g_i_Code_Finish_Need_Run_Update_RunParam = 1    # 1-本次完成，下次还要继续运行，需要更新运行时参数
g_i_Code_Finish_Need_Run = 2      # 2-本次完成，还要继续运行，不修改参数内容

g_str_Alarm_Reply_V_ResultCode = 'code'
g_str_Alarm_Reply_V_RunResult = 'RunResult'
g_str_Alarm_Reply_V_NeedUpdateRunParam = 'NeedUpdateRunParam'
g_str_Alarm_Reply_V_SendUserContent = 'SendUserContent'

g_str_Alarm_Reply_P1_RunTypeID = 'RunTypeID'
g_str_Alarm_Reply_P1_TaskRecID = 'TaskRecID'

# 系统还有其他等待发送的数据单元
g_wait_ToBeSend_CTUnitArray = []



# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, 'CTRL_C', "Ctrl+C Input, exiting")
    g_bSysRunning = False

# ################################################################################################
#   下面是子命令处理实现
# ################################################################################################

# 处理 返回申请领取可以执行的单任务
# 	返回: iValue=902。strValue=传入参数|运行时参数内容，strParam1=执行类型，strParam2=任务ID记录值
#  回复的内容
#  	输入: iValue=903，strValue=结果code|执行的结果内容|需要更新的运行时参数|需要发送给用户的内容。strParam1=执行类型ID|任务ID，strParam2=结果附加参数
#  	结果code: 0 –完成，可以停止本次任务；1-本次完成，下次还要继续运行，需要更新运行时参数；2-本次完成，还要继续运行，不修改参数内容
# start by sk. 170408
def SubHandle_Act_Reply_RequestExec( strOrigParamRunParam, strRunType, strTaskRecID):
    iExRetCode = g_i_Code_Finish_Need_Run
    strSendUserContent = ''
    strNeedRunUpdateParam = ''
    strRunResult = ''

    try:
        iRunType = int(strRunType)
        iTaskRecID = int(strTaskRecID)
    except:
        iRunType = 0
        iTaskRecID = 0

    if( iRunType == g_i_ExecTypeID_LifeSupport_AlarmRing):
        # 提取json参数内容
        paramCollect = json.loads(strOrigParamRunParam)
        strOrigExecParam = paramCollect[g_str_TotalParam_OrigParam]
        strRunTimeParam = paramCollect[g_str_TotalParam_RunTimeParam]

        # 提取原始参数
        try:
            paramCollect = json.loads( strOrigExecParam)
            strOrigNotifyTime = paramCollect[g_str_Alarm_origParam_Time]
            strOrigAlarmContent = paramCollect[g_str_Alarm_origParam_AlarmContent]
            origNotifyTime = datetime.strptime(strOrigNotifyTime, g_ustr_TYLB_TimeFormat)
        except:
            origNotifyTime = datetime.now()
            strOrigAlarmContent = ''

        # 提取运行参数
        try:
            paramCollect = json.loads( strRunTimeParam)
            iAlarmCount = paramCollect[g_ustr_runParam_AlarmCount]
            strLastAlarmTime = paramCollect[g_ustr_runParam_LastAlarmTime]
            # 修正参数值
            lastAlarmTime = datetime.strptime( strLastAlarmTime, g_ustr_TYLB_TimeFormat)
        except:
            # 开始时，参数为空。初始化参数
            iAlarmCount = 0
            lastAlarmTime = datetime(2017,1,1)

        # 判断当前时间符合
        nowTime = datetime.now()
        if( nowTime > origNotifyTime):
            # 判断有否有效的时间间隔
            timeDiff = nowTime - lastAlarmTime
            if( timeDiff.seconds >= g_i_Min_Notify_TimeDiff):
                # 判断有否超过最大次数
                iAlarmCount += 1
                if( iAlarmCount <= g_i_Max_Notify_Count):
                    iExRetCode = g_i_Code_Finish_Need_Run_Update_RunParam
                    strIsLast = u' [最后一次]' if(iAlarmCount == g_i_Max_Notify_Count) else ''
                    strSendUserContent = u'第%d次事件提醒:[%s]%s' % (iAlarmCount, strOrigAlarmContent, strIsLast)
                    CTYLB_Log.ShowLog(0, 'Exec-Alarm', u'send msg:%s' % strSendUserContent)

                    # 输出更新参数
                    strExLastAlarmTime = nowTime.strftime( g_ustr_TYLB_TimeFormat)
                    outParamCollect = {g_ustr_runParam_AlarmCount : iAlarmCount,
                                       g_ustr_runParam_LastAlarmTime : strExLastAlarmTime}
                    strNeedRunUpdateParam = json.dumps(outParamCollect)
                else:
                    iExRetCode = g_i_Code_Finish_Stop_Task
                    strSendUserContent = ''

        pass

    valueCollect = { g_str_Alarm_Reply_V_ResultCode : iExRetCode,
                     g_str_Alarm_Reply_V_RunResult : strRunResult,
                     g_str_Alarm_Reply_V_NeedUpdateRunParam : strNeedRunUpdateParam,
                     g_str_Alarm_Reply_V_SendUserContent : strSendUserContent }
    strRetValue = json.dumps(valueCollect)

    param1Collect = { g_str_Alarm_Reply_P1_RunTypeID : g_i_ExecTypeID_LifeSupport_AlarmRing,
                      g_str_Alarm_Reply_P1_TaskRecID : iTaskRecID }
    strRetParam1 = json.dumps(param1Collect)

    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpAction_SubCmd_ReplyExecResult)
    retCommCTUnit.SetStrData( strRetValue)
    retCommCTUnit.SetParam( strRetParam1, '')

    global g_wait_ToBeSend_CTUnitArray
    g_wait_ToBeSend_CTUnitArray.append( retCommCTUnit)


# ################################################################################################
#   下面是主命令通信接口 实现
# ################################################################################################

# 获得要发送给 行动大脑的数据
# start by sk. 170413
def HandleSend_OpReActBrain_Srv():
    retSendUnitArray = []

    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpAction_SubCmd_RequestExec)
    sendCTUnit.SetParam(str(g_i_ExecTypeID_LifeSupport_AlarmRing), '')
    retSendUnitArray.append(sendCTUnit)

    global g_wait_ToBeSend_CTUnitArray
    if( g_wait_ToBeSend_CTUnitArray):
        retSendUnitArray.extend(g_wait_ToBeSend_CTUnitArray)
        g_wait_ToBeSend_CTUnitArray = []

    return retSendUnitArray

# 接收到 操作 操作行动大脑-数据包单元 管套数据单元的处理
# start by sk. 170413
def HandleRecv_OpReActBrain_CTUnit(eachCTUnit):
    if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if( eachCTUnit.s_iValue == g_i_OpAction_SubCmd_Reply_RequestExec):
            SubHandle_Act_Reply_RequestExec(eachCTUnit.s_strValue, eachCTUnit.s_strParam1, eachCTUnit.s_strParam2)


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

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()

    # 获得管套管理对象
    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang

    # 获得管套管理对象, 操作结果，操作参数块
    connect_ActionOperate_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_str_RealAction_BrainBot_Name, g_i_ListenSock_TYFBot_ReAction_Brain_Operate)
    CTYLB_Log.ShowLog(0, u'exec', u'start HLSock connect remote [%s:%d] op-Exec-Action-Brain Func' % (g_str_RealAction_BrainBot_Name, g_i_ListenSock_TYFBot_ReAction_Brain_Operate))

    while(g_bSysRunning):
        bTaskBusy = False
        if( connect_ActionOperate_Sock.ExecNextCheck()):
            bTaskBusy = True

        if( connect_ActionOperate_Sock.CanExecSendData()):
            execSendCTArray = HandleSend_OpReActBrain_Srv()
            connect_ActionOperate_Sock.ExecSendData( execSendCTArray)
            bTaskBusy = True

        recvCTArray = connect_ActionOperate_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connect_ActionOperate_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                # CTYLB_Log.ShowLog(0, 'recv-RealAction-Brain-reply', 'from [%s:%d] recv len:[%d]' % ( strPeerName, iPeerPort, len(eachUnit.s_strValue)))
                HandleRecv_OpReActBrain_CTUnit( eachUnit)

        if( not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    g_LessTYLB_Bot_FrameThread.SafeStop()

    CTYLB_Log.ShowLog(0, u'sys-echo', u'bye bye')

