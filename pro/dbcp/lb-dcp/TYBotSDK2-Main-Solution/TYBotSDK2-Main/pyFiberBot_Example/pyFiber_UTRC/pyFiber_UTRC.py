#coding:utf-8
# pyFiber_UTRC.py
# 线程任务中心。支持NATs客户端，和FBot客户端
# start by sk. 180413

from TYBotSDK2.FiberFBot.FbTBot_UTRC_Server import TYFiberBot_UTRCSrv_FBot_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base, FiberGroupUnit_Base
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share

import time



class pyFiberUTRC_Run:
    '''
    用例交互协议说明：
    场景描述：FBotA主动连接BrainA，并向A发起任务
    请求（协议ID1001），BrainA收到任务请求，把任务
    内容发送给FBotA执行（协议ID1000）
    '''

    def __init__(self):
        self.s_utrcSrv_FBot_Instance = TYFiberBot_UTRCSrv_FBot_Instance()
        pass

    def start(self):
        self.s_utrcSrv_FBot_Instance.Run()


if __name__ == "__main__":
    brain = pyFiberUTRC_Run()
    brain.start()
