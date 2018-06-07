# pyFiber_Show_UTRCInfo.py
# python 显示 UTRC信息
# start by sk. 180503

import time, json
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share
from TYBotSDK2.FiberFBot.FbTBot_UTRC_Client import TYFiberBot_Mang_NATS_UTRClient_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base, FiberGroupUnit_Base, FiberMsgRet
from datetime import datetime
from TYBotSDK2.FiberFBot.ShareCfgDef import Share_UTRC_CfgDef
from TYBotSDK2.FiberFBot.FiberFBot import CUTRC_NATs_ComuFiberList

g_str_Apple_FiberName="apple_fiber"  # 远端名字.
g_iExecCmd=100  # 执行的命令ID, 100以上

g_str_CPP_FiberName="LessSimpleMasterMan.FbTask_OtherCallMe" # C#远端名字
g_iCPP_Fiber_RemoteExecMsg=1056


# 查询 UTRC 客户端单元的管理实例
class TYFiberBot_QueryUTRCClient_Instance(TYFiberBot_Mang_NATS_UTRClient_Instance):
    def __init__(self, config_file="config/config.yaml", funcCallBack=None):
        TYFiberBot_Mang_NATS_UTRClient_Instance.__init__(self, config_file, funcCallBack)

    def PromptQueryUTRCList(self):
        self.s_AsyncNATS_ProcComu.AddContentToSend(
            self.s_strNATSProcServerName, Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Request_AllClientInfo,
            "")
        pass

    def PopRecveplyQueryAllClient(self):
        return self.s_AsyncNATS_ProcComu.Pop_Recv_Reply_QueryAllClient()


class Fiber_Show_UTRCInfo(FiberUnit_Base):
    s_g_strMyFiberName="Fiber_Show_UTRCInfo"

    def __init__(self):
        FiberUnit_Base.__init__(self, self.s_g_strMyFiberName, bExRemoteCallMe=True)
        self.s_TimerSend=CSkBot_Common_Share.CSkBot_TimeIdentify()
        self.s_dict_AllUTRCClientInfo={}

    def OnMessage_Sample(self, fromSenderUnit, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        CTYLB_Log.ShowLog(0, self.s_g_strMyFiberName, "recv %s message,first to second" % (fromSenderUnit.s_strFullTaskName))
        pass

    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        if(self.s_TimerSend.CheckShow()):
            # UTRC的NATS提交发送
            pass
        pass

    # 处理消息
    def v_HandleMessage(self, fromSenderUnit, messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        fiberMsgRet = FiberUnit_Base.v_HandleMessage(self,fromSenderUnit, messageID, strMsgJsonParam,
                                                   strMsgParam, lMsgParam1, lMsgParam2)

        return fiberMsgRet

    pass

# 服务端 四个类型 的节点类型
s_dict_NatsClient={}
s_dict_FBotClient={}
s_dict_PeerFBotSrv_NatsClient={}
s_dict_PeerFBotSrv_FBotClient={}

# 运行单元入口
class PyFiberTest1:

    def __init__(self):
        self.s_utrcClient = TYFiberBot_QueryUTRCClient_Instance(funcCallBack= self.funcCheckCallBack)
        self.s_TimerSend=CSkBot_Common_Share.CSkBot_TimeIdentify()


    def funcCheckCallBack(self):
        # 提交请求进行发送
        if(self.s_TimerSend.CheckTimeDiff()):
            self.s_utrcClient.PromptQueryUTRCList()

        # 查询接收到的内容
        strList=self.s_utrcClient.PopRecveplyQueryAllClient()
        if(strList):
            srvTypesFiberDict = json.loads(strList)

            # 每个类型的内容进行加载
            for eachType in srvTypesFiberDict:
                execDestDict=None
                if(eachType== "NatsClient"):
                    execDestDict=s_dict_NatsClient
                elif(eachType== "FBotlient"):
                    execDestDict = s_dict_FBotClient
                elif(eachType== "PeerFBotSrv_NatsClient"):
                    execDestDict = s_dict_PeerFBotSrv_NatsClient
                elif(eachType== "PeerFBotSrv_FBotClient"):
                    execDestDict = s_dict_PeerFBotSrv_FBotClient

                subClientFiberDict = srvTypesFiberDict[eachType]
                if(execDestDict != None):
                    # 字典的每个 主机单元的 fiber列表进行加载
                    execDestDict.clear()
                    for eachSubClientName in subClientFiberDict.keys():
                        strSubClientFiberList = subClientFiberDict[eachSubClientName]

                        curComuFiberNamesUnit = CUTRC_NATs_ComuFiberList()
                        if (curComuFiberNamesUnit.LoadFromStr(strSubClientFiberList)):
                            execDestDict[eachSubClientName] = curComuFiberNamesUnit

                    CTYLB_Log.ShowLog(0, eachType, "Count:%d"%(len(execDestDict)))

            #构建本地的客户端信息.
            pass
        pass

    def Prepare(self):
        self.s_utrcClient.AddFiberUnit(Fiber_Show_UTRCInfo())


    def start(self):
        self.s_utrcClient.Run()

if __name__ == "__main__":
    funcBot = PyFiberTest1()
    funcBot.Prepare()
    funcBot.start()
