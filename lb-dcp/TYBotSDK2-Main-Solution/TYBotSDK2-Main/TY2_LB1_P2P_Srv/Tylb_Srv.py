# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Srv.py server-realize
#
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式

import sys
import signal
import os
from TYBotServerSDK2.P2PServer.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotServerSDK2.P2PServer.Tylb_Support_Srv import CTYLB_Peer_Server

g_bSysRunning = True
g_ustrProgName = u"TY_LB_Srv_V3.0"

# 是否需要整体系统退出？
# start by sk. 170116
def IsGlobalStopExit():
    bRetValue = not g_bSysRunning
    return bRetValue

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting %s"%(g_ustrProgName))
    g_bSysRunning = False

if __name__ == '__main__':
    CTYLB_MainSys_MiscFunc.SetConsoleCompatible()
    # 登记异常处理函数
    signal.signal(signal.SIGINT, CtrlCHandle)
    signal.signal(signal.SIGTERM, CtrlCHandle)
    #获取配置文件路径及文件名，文件夹不存在则创建
    config_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"config")
    config_file= os.path.join(config_dir, u"config.yaml")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.isfile(config_file):
        CTYLB_Log.ShowLog(0, u'Main', u'[%s] config file missing...Quit!' % g_ustrProgName)
        #配置文件不存在，直接退出
        os._exit(-1)
    m = CTYLB_Peer_Server( config_file)
    m.run( g_ustrProgName, IsGlobalStopExit)

    CTYLB_Log.ShowLog(0, u'Main', u'[%s] bye bye' % g_ustrProgName)

