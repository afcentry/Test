# -*- coding:UTF-8 -*- 放到第一行标记
# TYFBot_Real_OP_Monitor.py 天元功能机器人－操作 多显示器的服务端
#
# start by sk. 170408

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log,CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_MainConn
from Sk_LB_db_FBot_MultiMonitorCtrl_Real import CSkLBDB_funcbot_op_display
from monitor_api_handler import MonitorApiHandler
import time
from datetime import datetime
import random
import os
import json

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = u'TianYuan Function Bot - Multi Montiro Display'
#g_mainOperateMonitorDB = CSkLBDB_MainConn()    # 链接微信bot数据库

g_str_MultiMonitorBot_DBName = u'funcbot_op_display'
g_i_ListenSock_TYFBot_OP_Monitor_Operate = 8  # 监听管套，操作显示内容机器人

g_i_OpMonitor_SubCmd_Post_DisplayContent = 801  # 提交显示内容
g_i_OpMonitor_SubCmd_Reply_Post_DisplayContent = 802  # 回复 提交显示内容

g_i_ExecTypeID_Monitor_ShowNetworkSituation=20001 #执行类型ID-态势感知-显示器展示指定地区或者企业网络安全态势
g_i_ExecTypeID_Monitor_ShowNetworkAssets=20002    #执行类型ID-态势感知-展示指定地区或企业的网络资产分布

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting")
    g_bSysRunning = False

# ################################################################################################
#   下面是子命令处理实现
# ################################################################################################

# 处理操作 Monitor 提交显示的内容
# 	输入: iValue=801，strValue=显示文字，或者显示图片的Base64转码。strParam1=显示器的标志ID，strParam2=数据类型0-文字，1-图像
# 	返回: iValue=802。
# start by sk. 170408
def SubHandle_OPMonitor_Post_DisplayContent( ustrDisplayContent, ustrMonitorID, ustrDataType):
    ustrDisplayContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrDisplayContent)
    ustrMonitorID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrMonitorID) #{ "RunTypeID" : 902,"TaskRecID" : 24 }
    ustrDataType = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrDataType)  #"ShowNetworkAssets"

    replyJson=json.loads(ustrMonitorID)
    iRunType = replyJson["RunTypeID"]
    iTaskRecID=replyJson["TaskRecID"]

    targetData=json.loads(ustrDisplayContent)
    res=''
    if iRunType==g_i_ExecTypeID_Monitor_ShowNetworkSituation:
        #请求API提交数据
        res=MonitorApiHandler.AddNetworkSituation(target=targetData['target'],target_type=targetData['type'])
    elif iRunType==g_i_ExecTypeID_Monitor_ShowNetworkAssets:
        #请求API提交数据
        res=MonitorApiHandler.AddNetworkAssets(target=targetData['target'],target_type=targetData['type'])


    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpMonitor_SubCmd_Reply_Post_DisplayContent)
    retCommCTUnit.SetStrData(res)  #strOrigParamRunParam
    retCommCTUnit.SetParam(str(iRunType),str(iTaskRecID)) #strRunType strTaskRecID
    return retCommCTUnit


# ################################################################################################
#   下面是主命令通信接口 实现
# ################################################################################################


# 接收到 操作 Monitor 管套数据单元的处理
# start by sk. 170408
def HandleRecvCTUnit_OPMonitor(hlSockMang, iEachAcceptSock, ctUnitArray):
    retDataArray = []
    for eachCTUnit in ctUnitArray:
        eachRetCommCTUnit = None
        eachRetCommCTUnitArray = []
        if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if( eachCTUnit.s_iValue == g_i_OpMonitor_SubCmd_Post_DisplayContent):
                eachRetCommCTUnit = SubHandle_OPMonitor_Post_DisplayContent( eachCTUnit.s_strValue, eachCTUnit.s_strParam1,
                                                                             eachCTUnit.s_strParam2 )

        if( eachRetCommCTUnit):
            retDataArray.append(eachRetCommCTUnit)
        if( eachRetCommCTUnitArray):
            retDataArray.extend( eachRetCommCTUnitArray)
    if (not retDataArray):
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
    #g_mainOperateMonitorDB.ReConnect(u"127.0.0.1", 3306, u"lessnet", u",,,,,...../////", g_str_MultiMonitorBot_DBName)

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()

    # 获得管套管理对象
    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang
    iOPMonitor_ListenSock = hlSockMang.CreateListenSock( g_i_ListenSock_TYFBot_OP_Monitor_Operate)
    iAccept_OPMonitor_Sock_Array = []
    while(g_bSysRunning):
        bTaskBusy = False
        # 检查新接收的连接
        iNewAcceptSockIndex = hlSockMang.ExAcceptNewListenArriveSock( iOPMonitor_ListenSock)
        if( iNewAcceptSockIndex):
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSockIndex)
            CTYLB_Log.ShowLog(0, u'op-Monitor', u'from [%s:%d] new HLConnect %d accept.' % (strPeerName, iPeerPort, iNewAcceptSockIndex))
            bTaskBusy = True
            iAccept_OPMonitor_Sock_Array.append( iNewAcceptSockIndex)
            pass
        for iEachAcceptSock in iAccept_OPMonitor_Sock_Array:
            # 检查有否新数据包到达
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachAcceptSock)
            if( not bSockExist):
                # 检查是否管套已经关闭
                CTYLB_Log.ShowLog(0, u'op-Monitor', u'sock %d closed' % (iEachAcceptSock))
                iAccept_OPMonitor_Sock_Array.remove( iEachAcceptSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    HandleRecvCTUnit_OPMonitor( hlSockMang, iEachAcceptSock, ctUnitArray)

        if( not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    g_LessTYLB_Bot_FrameThread.SafeStop()
    CTYLB_Log.ShowLog(0, u'sys-echo', u'bye bye')

