# pyFiber_FBot_execClient_Test1.py
# python Fiber单元 FBot 客户端 测试程序1
# start by sk. 180415

import time
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share
from TYBotSDK2.FiberFBot.FbTBot_UTRC_Client import TYFiberBot_Mang_NATS_UTRClient_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base, FiberGroupUnit_Base, FiberMsgRet
from datetime import datetime

g_iExecCmd=100  # 执行的命令ID, 100以上
g_str_pyFiberTest2_Apple_FiberUnit="apple_fiber"

class MyAppFiber_FBotExecClient_Test(FiberUnit_Base):
    s_g_strMyFiberName="MyAppFiber_FBotExecClient_Test"
    def __init__(self):
        FiberUnit_Base.__init__(self, self.s_g_strMyFiberName, bExRemoteCallMe=True)
        self.s_TimerSend=CSkBot_Common_Share.CSkBot_TimeIdentify(8)
        self.s_dict_msgResult = {}  # 消息结果

    def v_OnInit(self):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "OnInit")
        # 初始化
        pass

    def v_OnClose(self):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "v_OnClose")
        # 删除
        pass


    def OnMessage_Sample(self, fromSenderUnit, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "recv %s message,second to first." % (fromSenderUnit.s_strFullTaskName))
        pass

    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        bRet=False
        if(self.s_TimerSend.CheckTimeDiff()):
            msgResult = self.SendTaskMsg_StrParam(g_str_pyFiberTest2_Apple_FiberUnit, g_iExecCmd, strMsgParam="这是测试1")
            if (msgResult.s_iExecResult == FiberMsgRet.s_g_iExecResult_Remote_Wait_Reply):
                self.s_dict_msgResult[msgResult.s_strRetValue] = datetime.now()
        return bRet


    # 虚函数，通知远端发送回消息
    # add by sk. 180415
    def v_On_RemoteReplyMsgResult(self, strMsgExecUID, msgExecRet):
        if(strMsgExecUID in self.s_dict_msgResult.keys()):
            oldTime = self.s_dict_msgResult[strMsgExecUID]
            timeDiff = datetime.now() - oldTime
            CTYLB_Log.ShowLog(0, "recv task reply", "time:%d, still count:%d" %
                              (timeDiff.total_seconds(), len(self.s_dict_msgResult)))
            self.s_dict_msgResult.pop(strMsgExecUID)
        pass

    # 处理消息
    def v_HandleMessage(self, fromSenderUnit, messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):

        fiberMsgRet = FiberUnit_Base.v_HandleMessage(self,fromSenderUnit, messageID, strMsgJsonParam,
                                                   strMsgParam, lMsgParam1, lMsgParam2)

        if(messageID==g_iExecCmd):
            fiberMsgRet = self.OnMessage_Sample(fromSenderUnit, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2)

        return fiberMsgRet

    pass

class PyFiber_FBotClient_Test1:
    '''
    用例交互协议说明：

    Test1向Test2发送会话1。ID1000，Test2收到后，回复1001。 本地收到1001后，继续发送1000，重新循环

    '''

    def __init__(self):
        self.s_timeIdentify = CSkBot_Common_Share.CSkBot_TimeIdentify()
        self.s_utrcClient = TYFiberBot_Mang_NATS_UTRClient_Instance()

    def Prepare(self):
        self.s_utrcClient.AddFiberUnit(MyAppFiber_FBotExecClient_Test())

    def start(self):
        self.s_utrcClient.Run()


if __name__ == "__main__":
    funcBot = PyFiber_FBotClient_Test1()
    funcBot.Prepare()
    funcBot.start()
