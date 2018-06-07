# pyFiberTest1_SimpleApp.py
# python Fiber单元 测试程序1
# start by sk. 180413

import time
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share
from TYBotSDK2.FiberFBot.FbTBot_UTRC_Client import TYFiberBot_Mang_NATS_UTRClient_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base, FiberGroupUnit_Base, FiberMsgRet
from datetime import datetime

g_str_Apple_FiberName="apple_fiber"  # 远端名字.
g_iExecCmd=100  # 执行的命令ID, 100以上

g_str_CPP_FiberName="LessSimpleMasterMan.FbTask_OtherCallMe" # C#远端名字
g_iCPP_Fiber_RemoteExecMsg=1056

class MyAppFiber_Sub_First(FiberUnit_Base):
    s_g_strMyFiberName="MyAppFiber_Sub_First"

    def __init__(self):
        FiberUnit_Base.__init__(self, self.s_g_strMyFiberName, bExRemoteCallMe=True)
        self.s_TimerSend=CSkBot_Common_Share.CSkBot_TimeIdentify()

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
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "recv %s message,first to second" % (fromSenderUnit.s_strFullTaskName))
        pass

    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        strMsgParam="从：发出消息 %s" % (self.s_g_strMyFiberName)
        strJsonParam = str(datetime.now())
        if(self.s_TimerSend.CheckShow()):
            msgResult = self.SendTaskMsg_StrParam(g_str_Apple_FiberName, g_iExecCmd,
                                      strMsgJsonParam=strJsonParam, strMsgParam=strMsgParam)
            if(msgResult.s_iExecResult == FiberMsgRet.s_g_iExecResult_Remote_Wait_Reply):
                self.s_dict_msgResult[msgResult.s_strRetValue] = datetime.now()

            msgResult = self.SendTaskMsg_StrParam(g_str_CPP_FiberName, g_iCPP_Fiber_RemoteExecMsg, strMsgParam="这是py语言")
        pass

    # 虚函数，通知远端发送回消息
    # add by sk. 180415
    def v_On_RemoteReplyMsgResult(self, strMsgExecUID, msgExecRet):
        if(strMsgExecUID in self.s_dict_msgResult.keys()):
            oldTime = self.s_dict_msgResult[strMsgExecUID]
            timeDiff = datetime.now() - oldTime
            CTYLB_Log.ShowLog(0, "recv task reply", "time:%d, still count:%d" %
                              (timeDiff.total_seconds(), len(self.s_dict_msgResult)))
            self.s_dict_msgResult.pop(strMsgExecUID)
        else:
            CTYLB_Log.ShowLog(0, "Recv Reply from:%s"%strMsgExecUID, msgExecRet.s_strRetValue)
        pass

    # 处理消息
    def v_HandleMessage(self, fromSenderUnit, messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        fiberMsgRet = FiberUnit_Base.v_HandleMessage(self,fromSenderUnit, messageID, strMsgJsonParam,
                                                   strMsgParam, lMsgParam1, lMsgParam2)

        if(messageID==g_iExecCmd):
            fiberMsgRet = self.OnMessage_Sample(fromSenderUnit, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2)
            if(fiberMsgRet.s_iExecResult == FiberMsgRet.s_g_iExecResult_Remote_Wait_Reply):
                self.s_dict_msgResult[fiberMsgRet.s_strRetValue] = datetime.now()
                pass

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

    '''
    def HandleRecv_100(self, value, param1, param2, is_last_package):
        #CTYLB_Log.ShowLog(0,'hello', "recv-1001")
        retCTUnitArray = []
        if(is_last_package):
            if(self.timeIdentify.CheckShow()):
                sendCTUnit = FBot.make_package(100, "", "", "testzhuangshiqi")
                retCTUnitArray = [sendCTUnit]
        return retCTUnitArray


    def HandleRecv_200(self, value, param1, param2, is_last_package):
        CTYLB_Log.ShowLog(0,'hello', "recv-1000")

        retCTUnitArray = []
        #if(is_last_package):
        #    sendCTUnit = FBot.make_package(1001, "aa", "bb", "testzhuangshiqi-test2")
        #    retCTUnitArray = [sendCTUnit]
        return retCTUnitArray
    '''

    def Prepare(self):
        self.s_utrcClient.AddFiberUnit(MyAppFiber_Sub_First())


    def start(self):
        self.s_utrcClient.Run()
        '''
        bot = FBot(connect_to_socks={"pyFiberTest2_Listen": [1001]}, report_status=True, comment="执行加法计算")
        bot.add_connect_to_callbacks("pyFiberTest2_Listen", 1001, 100, self.HandleRecv_100, True)
        bot.add_connect_to_callbacks("pyFiberTest2_Listen", 1001, 200, self.HandleRecv_200, False)

        bot.run()
        '''


if __name__ == "__main__":
    funcBot = PyFiberTest1()
    funcBot.Prepare()
    funcBot.start()
