# ======================================================
# TYFBot_Act_MonitorTaskAnalyze.py 行动机器人，显示器任务 态势-资产-展示-助手实现
#
# start by pxk. 170505

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log,CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
import time
from datetime import datetime
import random
import os
import json

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = u'TianYuan Action Bot - Monitor Task Analyze'

g_str_RealAction_BrainBot_Name = u'TYFBot_ReAct_Brain_A'#通信大脑
g_str_RealAction_MonitorCtrlBot_Name=u'TYFBot_OP_MultiMonitorCtrl' #显示器控制调度机器人
g_i_ListenSock_TYFBot_ReAction_Brain_Operate = 9   # 监听管套，操作行动机器人的任务

g_i_OpAction_SubCmd_RequestExec = 901   # 申请可以执行的子任务
g_i_OpAction_SubCmd_Reply_RequestExec = 902  # 回复 申请子任务
g_i_OpAction_SubCmd_ReplyExecResult = 903   # 执行子任务后，返回执行结果
g_i_OpAction_SubCmd_Reply_ReplyExecResult = 904   # 回复 返回执行结果

g_i_ListenSock_TYFBot_OP_Monitor_Operate = 8  # 监听管套，操作显示内容机器人

g_i_OpMonitor_SubCmd_Post_DisplayContent = 801  # 提交显示内容
g_i_OpMonitor_SubCmd_Reply_Post_DisplayContent = 802  # 回复 提交显示内容

g_i_ExecTypeID_Monitor_ShowNetworkSituation=20001 #执行类型ID-态势感知-显示器展示指定地区或者企业网络安全态势
g_i_ExecTypeID_Monitor_ShowNetworkAssets=20002    #执行类型ID-态势感知-展示指定地区或企业的网络资产分布

g_bstr_ContentSplit = b'(;1-@;)'   # 内容的分隔符
g_ustr_TYLB_TimeFormat = u'%Y-%m-%d %H:%M:%S'   # 时间格式



# 执行结果返回的定义
g_i_Code_Finish_Stop_Task = 0      # 0 –完成，可以停止本次任务；
g_i_Code_Finish_Need_Run_Update_RunParam = 1    # 1-本次完成，下次还要继续运行，需要更新运行时参数
g_i_Code_Finish_Need_Run = 2      # 2-本次完成，还要继续运行，不修改参数内容



# 系统还有其他等待发送的数据单元
g_wait_ToBeSend_CTUnitArray = []
g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray = []


# 中断处理函数
# start by pxk. 170505
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
# start by pxk. 170505
def SubHandle_Act_Brain_Reply_RequestExec( strOrigParamRunParam, strRunType, strTaskRecID):
    strOrigParamRunParam=CTYLB_MainSys_MiscFunc.SafeGetUnicode(strOrigParamRunParam)
    strRunType = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRunType)
    strTaskRecID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTaskRecID)
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

    if( iRunType == g_i_ExecTypeID_Monitor_ShowNetworkSituation):  #安全态势任务
        # 提取json参数内容
        paramCollect = json.loads(strOrigParamRunParam)

        # ==================构建回复用户微信的内容=================================
        iExRetCode=g_i_Code_Finish_Stop_Task
        strSendUserContent="任务已经下发到屏幕控制机器人，渲染完成后将通知你哦。。。"
        print("[*]处理安全态势任务到显示屏：{}".format(strOrigParamRunParam))
        valueCollect = {"code": iExRetCode,
                        "RunResult": strRunResult,
                        "NeedUpdateRunParam": strNeedRunUpdateParam,
                        "SendUserContent": strSendUserContent}
        strRetValue = json.dumps(valueCollect)

        param1Collect = {"RunTypeID": g_i_ExecTypeID_Monitor_ShowNetworkSituation,
                         "TaskRecID": iTaskRecID}
        strRetParam1 = json.dumps(param1Collect)

        # ==================构建发送给Monitor控制的内容===========================
        ustrDisplayContent = paramCollect["OrigParam"]  # "{\"area\": \"\u5e7f\u5dde\u5e02\"}"
        ustrMonitorID = strRetParam1  #回复微信时需要
        ustrDataType = "ShowNetworkSituation"

    elif( iRunType == g_i_ExecTypeID_Monitor_ShowNetworkAssets):  #网络资产任务
        # 提取json参数内容
        paramCollect = json.loads(strOrigParamRunParam)

        #==================构建回复用户微信的内容=================================
        iExRetCode=g_i_Code_Finish_Stop_Task
        strSendUserContent="任务已经下发到屏幕控制机器人，渲染完成后将通知你哦。。。"
        print("[*]处理网络资产关联任务到显示屏：{}".format(strOrigParamRunParam))
        valueCollect = { "code" : iExRetCode,
                         "RunResult" : strRunResult,
                         "NeedUpdateRunParam" : strNeedRunUpdateParam,
                         "SendUserContent" : strSendUserContent }
        strRetValue = json.dumps(valueCollect)

        param1Collect = { "RunTypeID" : g_i_ExecTypeID_Monitor_ShowNetworkAssets,
                          "TaskRecID" : iTaskRecID }
        strRetParam1 = json.dumps(param1Collect)

        # ==================构建发送给Monitor控制的内容===========================
        #'{"OrigParam": "{\\"target\\": \\"\\u5357\\u65b9\\u7535\\u7f51\\"}", "RunTimeParam": null}'
        ustrDisplayContent=paramCollect["OrigParam"] #"{\"target\": \"\u5e7f\u5dde\u5e02\"}"
        ustrMonitorID=strRetParam1  #回复微信时需要
        ustrDataType="ShowNetworkAssets"

    retCommCTUnitToBrain = CTYBot_CTUnit_CommonData()
    retCommCTUnitToBrain.SetIntData( g_i_OpAction_SubCmd_ReplyExecResult)
    retCommCTUnitToBrain.SetStrData( strRetValue)
    retCommCTUnitToBrain.SetParam( strRetParam1, '')


    retCommCTUnitToMonitor = CTYBot_CTUnit_CommonData()
    retCommCTUnitToMonitor.SetIntData( g_i_OpMonitor_SubCmd_Post_DisplayContent)
    retCommCTUnitToMonitor.SetStrData( ustrDisplayContent)
    retCommCTUnitToMonitor.SetParam( ustrMonitorID,ustrDataType)

    #TODO:同时构造两个回复包，一个发送给用户提示提交成功，另一个发送到屏幕控制
    global g_wait_ToBeSend_CTUnitArray
    g_wait_ToBeSend_CTUnitArray.append(retCommCTUnitToBrain)

    global g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray
    g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray.append( retCommCTUnitToMonitor)

# 处理 返回申请领取可以执行的单任务
# 	返回: iValue=902。strValue=传入参数|运行时参数内容，strParam1=执行类型，strParam2=任务ID记录值
#  回复的内容
#  	输入: iValue=903，strValue=结果code|执行的结果内容|需要更新的运行时参数|需要发送给用户的内容。strParam1=执行类型ID|任务ID，strParam2=结果附加参数
#  	结果code: 0 –完成，可以停止本次任务；1-本次完成，下次还要继续运行，需要更新运行时参数；2-本次完成，还要继续运行，不修改参数内容
# start by pxk. 170505
def SubHandle_Act_Monitor_Reply_RequestExec( strOrigParamRunParam, strRunType, strTaskRecID):
    strOrigParamRunParam=CTYLB_MainSys_MiscFunc.SafeGetUnicode(strOrigParamRunParam)
    strRunType = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRunType)
    strTaskRecID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTaskRecID)
    iExRetCode = g_i_Code_Finish_Need_Run
    strSendUserContent = ""
    strNeedRunUpdateParam = ''
    strRunResult = ''
    try:
        iRunType = int(strRunType)
        iTaskRecID = int(strTaskRecID)
    except:
        iRunType = 0
        iTaskRecID = 0

    if( iRunType == g_i_ExecTypeID_Monitor_ShowNetworkSituation):  #安全态势任务
        # 提取json参数内容

        iExRetCode = g_i_Code_Finish_Stop_Task
        strSendUserContent = "安全态势任务结果已经展示到显示屏:{}".format(strOrigParamRunParam)
        print("[*]处理安全态势关联任务到显示屏结果通知：{}".format(strOrigParamRunParam))
        valueCollect = {"code": iExRetCode,
                        "RunResult": strRunResult,
                        "NeedUpdateRunParam": strNeedRunUpdateParam,
                        "SendUserContent": strSendUserContent}
        strRetValue = json.dumps(valueCollect)


        param1Collect = {"RunTypeID": g_i_ExecTypeID_Monitor_ShowNetworkSituation,
                         "TaskRecID": iTaskRecID}
        strRetParam1 = json.dumps(param1Collect)


    elif( iRunType == g_i_ExecTypeID_Monitor_ShowNetworkAssets):  #网络资产任务
        # 提取json参数内容

        iExRetCode = g_i_Code_Finish_Stop_Task
        strSendUserContent = "网络资产任务结果已经展示到显示屏:{}".format(strOrigParamRunParam)
        print("[*]处理网络资产关联任务到显示屏结果通知：{}".format(strOrigParamRunParam))
        valueCollect = {"code": iExRetCode,
                        "RunResult": strRunResult,
                        "NeedUpdateRunParam": strNeedRunUpdateParam,
                        "SendUserContent": strSendUserContent}
        strRetValue = json.dumps(valueCollect)

        param1Collect = { "RunTypeID" : g_i_ExecTypeID_Monitor_ShowNetworkAssets,
                          "TaskRecID" : iTaskRecID }
        strRetParam1 = json.dumps(param1Collect)


    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData(g_i_OpAction_SubCmd_ReplyExecResult)
    retCommCTUnit.SetStrData(strRetValue)
    retCommCTUnit.SetParam(strRetParam1, '')
    #通知微信用户查看
    global g_wait_ToBeSend_CTUnitArray
    g_wait_ToBeSend_CTUnitArray.append(retCommCTUnit)

# ################################################################################################
#   下面是主命令通信接口 实现
# ################################################################################################

# 获得要发送给 屏幕控制的数据
# start by pxk. 170505
def HandleSend_OpMonitorCtrl_Srv():
    retSendUnitArray = []

    global g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray
    if( g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray):
        retSendUnitArray.extend(g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray)
        g_wait_ToBeSend_To_MonitorCtrl_CTUnitArray = []

    #保证每次都会发送数据到屏幕控制端，避免等待
    if( not retSendUnitArray):
        sendCTUnit = CTYBot_CTUnit_CommonData()
        retSendUnitArray.append(sendCTUnit)

    return retSendUnitArray


# 获得要发送给 行动大脑的数据
# start by pxk. 170505
def HandleSend_OpReActBrain_Srv():
    retSendUnitArray = []

    #查询申请新的可执行任务 安全态势
    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpAction_SubCmd_RequestExec)
    sendCTUnit.SetParam(str(g_i_ExecTypeID_Monitor_ShowNetworkSituation), '')
    retSendUnitArray.append(sendCTUnit)

    #查询申请新的可执行任务 网络资产
    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpAction_SubCmd_RequestExec)
    sendCTUnit.SetParam(str(g_i_ExecTypeID_Monitor_ShowNetworkAssets), '')
    retSendUnitArray.append(sendCTUnit)


    global g_wait_ToBeSend_CTUnitArray
    if( g_wait_ToBeSend_CTUnitArray):
        retSendUnitArray.extend(g_wait_ToBeSend_CTUnitArray)
        g_wait_ToBeSend_CTUnitArray = []

    return retSendUnitArray
# 接收到 操作 操作行动大脑-数据包单元 管套数据单元的处理
# start by pxk. 170505
def HandleRecv_OpReActBrain_CTUnit(eachCTUnit):
    if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if( eachCTUnit.s_iValue == g_i_OpAction_SubCmd_Reply_RequestExec):
            SubHandle_Act_Brain_Reply_RequestExec(eachCTUnit.s_strValue, eachCTUnit.s_strParam1, eachCTUnit.s_strParam2)

# 接收到 操作 操作显示器-数据包单元 管套数据单元的处理
# start by pxk. 170505
def HandleRecv_OpMonitorCtrl_CTUnit(eachCTUnit):
    if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if (eachCTUnit.s_iValue == g_i_OpMonitor_SubCmd_Reply_Post_DisplayContent):
            #TODO:屏幕展示完毕，可以查看，通知到用户微信
            SubHandle_Act_Monitor_Reply_RequestExec(eachCTUnit.s_strValue, eachCTUnit.s_strParam1,
                                            eachCTUnit.s_strParam2)


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
    connect_MonitorCtrl_Operate_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_str_RealAction_MonitorCtrlBot_Name, g_i_ListenSock_TYFBot_OP_Monitor_Operate)
    CTYLB_Log.ShowLog(0, u'exec', u'start HLSock connect remote [%s:%d] op-Exec-Action-Brain Func' % (g_str_RealAction_BrainBot_Name, g_i_ListenSock_TYFBot_ReAction_Brain_Operate))
    CTYLB_Log.ShowLog(0, u'exec', u'start HLSock connect remote [%s:%d] op-Exec-Monitor-Ctrl Func' % (g_str_RealAction_MonitorCtrlBot_Name, g_i_ListenSock_TYFBot_OP_Monitor_Operate))

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

        #####################################
        #大脑任务发送到屏幕控制端的指令解析
        if( connect_MonitorCtrl_Operate_Sock.ExecNextCheck()):
            bTaskBusy = True

        if( connect_MonitorCtrl_Operate_Sock.CanExecSendData()):
            execSendCTArray = HandleSend_OpMonitorCtrl_Srv()
            connect_MonitorCtrl_Operate_Sock.ExecSendData( execSendCTArray)
            bTaskBusy = True

        recvCTArray = connect_MonitorCtrl_Operate_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connect_MonitorCtrl_Operate_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                # CTYLB_Log.ShowLog(0, 'recv-RealAction-Brain-reply', 'from [%s:%d] recv len:[%d]' % ( strPeerName, iPeerPort, len(eachUnit.s_strValue)))
                HandleRecv_OpMonitorCtrl_CTUnit( eachUnit)

        if( not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    connect_ActionOperate_Sock.Close()
    g_LessTYLB_Bot_FrameThread.SafeStop()

    CTYLB_Log.ShowLog(0, u'sys-echo', u'bye bye')

