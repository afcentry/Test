# PyFiber_BrainCore_API.py
# python Fiber单元 大脑内核-API
# start by sk. 180510

import time
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share
from TYBotSDK2.FiberFBot.FbTBot_UTRC_Client import TYFiberBot_Mang_NATS_UTRClient_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base, FiberGroupUnit_Base, FiberMsgRet, CUTRC_NATs_Comu_RunMessageUnit
from .ShareCfgDef import Share_UTRC_CfgDef
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CTylb_Bot_Exec_Frame
from TYBotSDK2.FBot.fbotV4 import FBotV4

# 全局定义
g_runTinyBrainCore = None

# 大脑内核单元的实现
class PyFiber_PyBrainCore:
    def __init__(self, config_file="config/config.yaml"):
        self.s_utrcClient = TYFiberBot_Mang_NATS_UTRClient_Instance(config_file)
        self.strMyFBotID = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FBot,
                                                               Share_UTRC_CfgDef.g_str_key_myid, "")
        self.Prepare()

    def Prepare(self):
        # 准备，增加
        self.ExecAPICallFiber=Exec_API_CallFiber(self.strMyFBotID)
        self.s_utrcClient.AddFiberUnit(self.ExecAPICallFiber)
        pass

    def TimerCheck(self):
        self.s_utrcClient.LoopEventCallBack()

# 内部支持-外部执行API的Fiber接口
class Exec_API_CallFiber(FiberUnit_Base):

    s_g_strMySubFixFiberName = ".Exec_API_CallFiber"

    def __init__(self, strSelfClientID):
        self.strMyFullName = strSelfClientID + Exec_API_CallFiber.s_g_strMySubFixFiberName
        FiberUnit_Base.__init__(self, self.strMyFullName, bExRemoteCallMe=True)
        self.s_TimerSend = CSkBot_Common_Share.CSkBot_TimeIdentify(10)

        self.s_tobe_RunExecMsg={} # 等待调度运行的，远端执行消息. key=msgID, 内容=CUTRC_NATs_Comu_RunMessageUnit。
        self.s_finish_RunExecMsg={} #已经完成的执行消息. key=msgID, 内容=完成返回结果 FiberMsgRet
        self.s_runningMsgID=""
        self.s_runningRemoteExecMsgID=""
        self.s_runningMsgContent=None # 正在运行的消息内容

    # 请求执行命令。返回 命令UID
    def RequestExecCmd(self, strDestFiberName, messageID, strDestFiberParam="", lDestFiberParam1=0, lDestFiberParm2=0,
                     strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):
        # 加入单元到等待队列
        runMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()

        runMsgUnit.SetContent_FromFiberUnit(self)
        runMsgUnit.SetContent_DestFiberUnit(strDestFiberName, strDestFiberParam, 0, 0)
        runMsgUnit.SetContent_MsgContent(messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2)
        runMsgUnit.s_strGlobalMsg_UID=FiberMsgRet.BuildUniqueStr(self.s_strFullTaskName, strDestFiberName)

        self.s_tobe_RunExecMsg[runMsgUnit.s_strGlobalMsg_UID] = runMsgUnit

        return runMsgUnit.s_strGlobalMsg_UID

    # 查询是否完成。返回 bFinish, msgRetValue
    def QueryExecCmdFinish(self, strMsgUID):
        bRetFinish=False
        msgRetValue=None

        if( strMsgUID in self.s_finish_RunExecMsg.keys()):
            msgRetValue=self.s_finish_RunExecMsg[strMsgUID]
            self.s_finish_RunExecMsg.pop(strMsgUID)
            bRetFinish=True
        return bRetFinish, msgRetValue

    # 当接收到远端的消息，的处理
    def v_On_RemoteReplyMsgResult(self, strMsgExecUID, msgExecRet):
        if(strMsgExecUID==self.s_runningRemoteExecMsgID):
            self.s_finish_RunExecMsg[self.s_runningMsgID] = msgExecRet
            # 清除正在运行的内容
            self.s_runningMsgID=""
            self.s_runningRemoteExecMsgID=""
            self.s_runningMsgContent=None
        pass

    def CancelExecCmd(self, strMsgUID):
        if(self.s_runningMsgID == strMsgUID):
            self.s_runningMsgID=""
            self.s_runningRemoteExecMsgID=""
            self.s_runningMsgContent=None

        # 在等待队列中?
        if(strMsgUID in self.s_tobe_RunExecMsg.keys()):
            self.s_tobe_RunExecMsg.pop(strMsgUID)

        # 在完成队列?
        if(strMsgUID in self.s_finish_RunExecMsg.keys()):
            self.s_finish_RunExecMsg.pop(strMsgUID)
        pass

    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        bRet = False

        # 当前是否正在运行远端任务？
        if(self.s_runningMsgID):
            pass
        else:
            if(len(self.s_tobe_RunExecMsg)>0):
                bRet=True

                # 取出第一个等待单元
                keyValuePair = self.s_tobe_RunExecMsg.popitem()
                self.s_runningMsgID=keyValuePair[0]
                self.s_runningMsgContent=keyValuePair[1]

                # 执行命令
                execFiberMsgRet=None

                if(self.s_runningMsgContent.s_strDestFbUnit_StrParam):
                    execFiberMsgRet = self.SendTaskMsg_StrParam(
                        strFbUnitFullName=self.s_runningMsgContent.s_strDestFbUnit_FullName,
                        messageID=self.s_runningMsgContent.s_iRun_MessageID,
                        strDestTaskParam=self.s_runningMsgContent.s_strDestFbUnit_StrParam,
                        strMsgJsonParam=self.s_runningMsgContent.s_strMsgJsonParam_Orig,
                        strMsgParam=self.s_runningMsgContent.s_strMsgParam_Orig,
                        lMsgParam1=self.s_runningMsgContent.s_lMsgParam1,
                        lMsgParam2=self.s_runningMsgContent.s_lMsgParam2
                    )
                else:
                    execFiberMsgRet = self.SendTaskMsg_LongParam(
                        strFbUnitFullName=self.s_runningMsgContent.s_strDestFbUnit_FullName,
                        messageID=self.s_runningMsgContent.s_iRun_MessageID,
                        lTaskParam1=self.s_runningMsgContent.s_lDestFbUnit_lParam1,
                        lTaskParam2=self.s_runningMsgContent.s_lDestFbUnit_lParam2,
                        strMsgJsonParam=self.s_runningMsgContent.s_strMsgJsonParam_Orig,
                        strMsgParam=self.s_runningMsgContent.s_strMsgParam_Orig,
                        lMsgParam1=self.s_runningMsgContent.s_lMsgParam1,
                        lMsgParam2=self.s_runningMsgContent.s_lMsgParam2
                    )
                if(execFiberMsgRet):
                    if(execFiberMsgRet.s_iExecResult==FiberMsgRet.s_g_iExecResult_Normal):
                        self.s_finish_RunExecMsg[self.s_runningMsgID] = execFiberMsgRet
                        # 完成，清除
                        self.s_runningMsgContent=None
                        self.s_runningMsgID=""

                    elif(execFiberMsgRet.s_iExecResult==FiberMsgRet.s_g_iExecResult_Remote_Wait_Reply):
                        # 等待
                        self.s_runningRemoteExecMsgID=execFiberMsgRet.s_strRetValue
                        pass

                    else:
                        CTYLB_Log.ShowLog(1, "unknown type task.", "API running error")

            pass

        return bRet

    pass


# 外部全局实现
class Global_TinyBrainCore:
    def __init__(self):
        pass

    @staticmethod
    def InitBrainCore():
        global g_runTinyBrainCore
        g_runTinyBrainCore = PyFiber_PyBrainCore()
        pass

    @staticmethod
    def TimerCheck():
        global g_runTinyBrainCore
        g_runTinyBrainCore.TimerCheck()

    @staticmethod
    def IsGlobalRunning():
        bRet=True
        if(not FBotV4.GetGlobalIsRunning()):
            bRet=False
        return bRet

# 基本的执行API的功能
class PyExCallAPI_Base:
    def __init__(self):
        pass

    # 执行远端Fiber的命令
    def ExecFiberCmd(self, strDestFiberName, messageID, strDestFiberParam="", lDestFiberParam1=0, lDestFiberParm2=0,
                     strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        strExecMsgUID = g_runTinyBrainCore.ExecAPICallFiber.RequestExecCmd(
            strDestFiberName, messageID, strDestFiberParam=strDestFiberParam,
            lDestFiberParam1=lDestFiberParam1, lDestFiberParm2=lDestFiberParm2,
            strMsgJsonParam=strMsgJsonParam,
            strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        failTimeCheck = CSkBot_Common_Share.CSkBot_TimeIdentify(30)
        # 循环查询
        while(Global_TinyBrainCore.IsGlobalRunning()):
            if(failTimeCheck.CheckTimeDiff()):
                # 是否超时?
                break
            g_runTinyBrainCore.TimerCheck()

            bTaskFinish, execCmdRet=g_runTinyBrainCore.ExecAPICallFiber.QueryExecCmdFinish(strExecMsgUID)
            if(bTaskFinish):
                return execCmdRet

        # 取消
        g_runTinyBrainCore.ExecAPICallFiber.CancelExecCmd(strExecMsgUID)
        # 此处返回失败
        failMsgRet = FiberMsgRet(FiberMsgRet.s_g_iExecResult_Fail)
        return failMsgRet

