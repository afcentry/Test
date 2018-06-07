# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Sk_Sock_Sys_Echo_Srv.py 天元机器人－Echo的功能Sample
#
# start by sk. 170222
# develop into sock version.

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
import time
import random
import os

# 全局系统运行标识
g_bSysRunning = True
g_ustrProgName = u'TYBot_Echo_Server'

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting %s" % (g_ustrProgName))
    g_bSysRunning = False

# ################################################################################################
#   下面是节点系统单元实现
# ################################################################################################

# 接收到管套数据单元的处理
# start by sk. 170307
def HandleRecvSockCTUnit(hlSockMang, iEachAcceptSock, ctUnitArray):
    retDataArray = []
    for eachCTUnit in ctUnitArray:
        if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            retCommData = CTYBot_CTUnit_CommonData()
            retCommData.SetStrData( eachCTUnit.s_strValue)
            CTYLB_Log.ShowLog(0, u'recv & reply', eachCTUnit.s_strValue)
            retDataArray.append(retCommData)
    hlSockMang.PassiveSend_To_AcceptSock(iEachAcceptSock, retDataArray)
    pass

# 主程序入口
if __name__ == '__main__':
    #获取配置文件路径及文件名，文件夹不存在则创建
    config_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"config")
    config_file= os.path.join(config_dir,u"config.yaml")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.isfile(config_file):
        CTYLB_Log.ShowLog(0, u'Main', u'[%s] config file missing...Quit!' % g_ustrProgName)
        #配置文件不存在，直接退出
        os._exit(-1)

    db_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"db")
    db_file= os.path.join(db_dir,u"data.db")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    g_iSockEchoListenPort = 2  # Echo端口

    # 创建机器人框架
    g_LessTYLB_Bot_Echo_Srv_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_Echo_Srv_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_Echo_Srv_FrameThread.Prepare_Start()

    # 获得管套管理对象
    hlSockMang = g_LessTYLB_Bot_Echo_Srv_FrameThread.s_HLSockMang
    iListenSockIndex = hlSockMang.CreateListenSock( g_iSockEchoListenPort)
    iNewAcceptSockIndexArray = []
    while(g_bSysRunning):
        bTaskBusy = False
        iNewAcceptSockIndex = hlSockMang.ExAcceptNewListenArriveSock( iListenSockIndex)
        if( iNewAcceptSockIndex):
            bstrPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSockIndex)
            CTYLB_Log.ShowLog(0, u'sys-echo', u'from [%s:%d] new HLConnect %d accept.' % (bstrPeerName, iPeerPort, iNewAcceptSockIndex))
            bTaskBusy = True
            iNewAcceptSockIndexArray.append( iNewAcceptSockIndex)
            pass
        for iEachAcceptSock in iNewAcceptSockIndexArray:
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachAcceptSock)
            if( not bSockExist):
                CTYLB_Log.ShowLog(0, u'sys-echo', u'sock %d closed' % (iEachAcceptSock))
                iNewAcceptSockIndexArray.remove( iEachAcceptSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    HandleRecvSockCTUnit( hlSockMang, iEachAcceptSock, ctUnitArray)
        if (not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    g_LessTYLB_Bot_Echo_Srv_FrameThread.SafeStop()
    CTYLB_Log.ShowLog(0, u'sys-echo', u'bye bye %s' % (g_ustrProgName))

