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

# 是否需要整体系统退出？
# start by sk. 170116
def IsGlobalStopExit():
    bRetValue = not g_bSysRunning
    return bRetValue

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, 'CTRL_C', u"Ctrl+C Input, Exiting...")
    g_bSysRunning = False

class P2PServer:
    '''
    分布式隧道网络服务器节点实现
    Start By Pxk. 171214
    '''
    def __init__(self,name="TY_LB_Srv_V2",config="config/config.yaml"):
        '''
        初始化函数
        :param name: 服务器名称
        :param config: 服务器运行参数配置yaml文件
        '''
        self.name=name
        self.config_file=config

    def check_config_exists(self):
        '''
        检查配置文件是否存在
        :return: 存在返回 True,否则返回False
        '''
        # 获取配置文件路径及文件名，文件夹不存在则创建
        config_dir =os.path.dirname(self.config_file)
        config_file = self.config_file
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if not os.path.isfile(config_file):
            CTYLB_Log.ShowLog(0, 'P2PServer', '[%s] config file missing...Quit!' % self.name)
            # 配置文件不存在，直接退出
            return False
        return True

    def start(self):
        '''
        启动服务器
        :return: 无
        '''
        if not self.check_config_exists():
            return
        global g_bSysRunning
        g_bSysRunning = True
        CTYLB_MainSys_MiscFunc.SetConsoleCompatible()
        # 登记异常处理函数
        signal.signal(signal.SIGINT, CtrlCHandle)
        signal.signal(signal.SIGTERM, CtrlCHandle)

        m = CTYLB_Peer_Server(self.config_file)
        m.run(self.name, IsGlobalStopExit)

        CTYLB_Log.ShowLog(0, 'P2PServer', '[%s] Bye Bye' % self.name)

    def stop(self):
        '''
        停止服务器
        :return:无
        '''
        global g_bSysRunning
        CTYLB_Log.ShowLog(1, 'Stop Cmd', u"Stop Command, Exiting...")
        g_bSysRunning = False


