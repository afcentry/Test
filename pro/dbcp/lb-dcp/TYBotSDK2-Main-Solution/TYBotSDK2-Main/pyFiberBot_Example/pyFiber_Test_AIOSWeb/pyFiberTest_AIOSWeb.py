# pyFiberTest1_SimpleApp.py
# python Fiber单元 测试程序1
# start by sk. 180413

import time
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share
from TYBotSDK2.FiberFBot.FbTBot_UTRC_Client import TYFiberBot_Mang_NATS_UTRClient_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base, FiberGroupUnit_Base, FiberMsgRet

g_iExecCmd=100  # 执行的命令ID, 100以上

class MyAppFiber_TestWebAOS(FiberUnit_Base):
    s_g_strMyFiberName="MyAppFiber_TestWebAOS"
    def __init__(self):
        FiberUnit_Base.__init__(self, self.s_g_strMyFiberName, bExRemoteCallMe=True)
        self.s_TimerSend=CSkBot_Common_Share.CSkBot_TimeIdentify(10)

    def v_OnInit(self):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "OnInit")
        # 初始化
        pass

    def v_OnClose(self):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "v_OnClose")
        # 删除
        pass


    def OnMessage_Sample(self, fromSenderUnit, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "recv %s message, json:[%s], msg:[%s]" %
                          (fromSenderUnit.s_strFullTaskName, strMsgJsonParam, strMsgParam))
        msgRet=FiberMsgRet(strRetValue=strMsgParam+"->苹果回复ing", lRetValue=lMsgParam1, lRetValue2=lMsgParam2)
        return msgRet
        pass

    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        bRet=False

        strRemoteWebOsFiberName="PyFiberAIOSWebOS"
        remoteCommandID=100

        if(self.s_TimerSend.CheckTimeDiff()):
            self.SendTaskMsg_StrParam( strFbUnitFullName=strRemoteWebOsFiberName, messageID=remoteCommandID, )

        #CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "v_Base_TimerCheck")
        #if(self.s_TimerSend.CheckTimeDiff()):
        #    self.PostTaskMsg_StrParam(MyAppFiber_Second.s_g_strMyFiberName, "", iFirstSendToSecond)
        return bRet

    # 处理消息
    def v_HandleMessage(self, fromSenderUnit, messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        fiberMsgRet = FiberUnit_Base.v_HandleMessage(self,fromSenderUnit, messageID, strMsgJsonParam,
                                                   strMsgParam, lMsgParam1, lMsgParam2)

        if(messageID==g_iExecCmd):
            fiberMsgRet = self.OnMessage_Sample(fromSenderUnit, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2)

        return fiberMsgRet

    pass

class PyFiberTest1:
    '''
    用例交互协议说明：

    Test1向Test2发送会话1。ID1000，Test2收到后，回复1001。 本地收到1001后，继续发送1000，重新循环

    '''

    def __init__(self):
        self.s_timeIdentify = CSkBot_Common_Share.CSkBot_TimeIdentify()
        self.s_utrcClient = TYFiberBot_Mang_NATS_UTRClient_Instance()

    def Prepare(self):
        self.s_utrcClient.AddFiberUnit(MyAppFiber_TestWebAOS())

    def start(self):
        self.s_utrcClient.Run()


if __name__ == "__main__":
    funcBot = PyFiberTest1()
    funcBot.Prepare()
    funcBot.start()
