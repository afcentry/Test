# FiberFBot.py
# 纤程FBot机器人的实现。
# 外部通过创建纤程单元，即可不断执行。通过Message的方式进行执行和调用
# start by sk. 180413


from TYBotSDK2.FBot.fbotV4 import FBotV4
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CTYLB_MainSys_MiscFunc, CSkBot_Common_Share

from .NatsMsgProcWideLangComu import CAsyncNats_MultiLang_Proc_Comu  # 异步NATs服务器通信
from TYBotSDK2.FiberFBot.FiberMangReal import FiberMang
import json

# 异步通信定义
class CAsyncNats_ProcComu(CAsyncNats_MultiLang_Proc_Comu):
    def __init__(self, strNATSServerAddr, strSelfRecvName):
        CAsyncNats_MultiLang_Proc_Comu.__init__(self, strNATSServerAddr, strSelfRecvName)

    def CheckRecv_Handle(self):
        iExecCount = 0
        origRecvMsgArray = self.CheckRecvMsg()
        for eachRecvMsg in origRecvMsgArray:
            # 处理各个消息单元
            #eachRecvMsg.s_strPeerMsgName
            #eachRecvMsg.s_iMsgType
            #eachRecvMsg.s_strMsgContent

            self.v_HandleRecvPacket(eachRecvMsg.s_strPeerMsgName, eachRecvMsg.s_iMsgType, eachRecvMsg.s_strMsgContent)

            if(not FBotV4.GetGlobalIsRunning()):
                break
            pass
        return iExecCount

    # 处理接收到的数据包
    def v_HandleRecvPacket(self, strFromName, iMsgType, strMsgContent):
        # self.AddContentToSend(eachRecvMsg.s_strPeerMsgName, eachRecvMsg.s_iMsgType, strReplyContent)
        pass


# URC各个节点，通信，纤程单元列表的结构
class CUTRC_NATs_ComuFiberList:
    s_g_str_Section_TaskUID="task_uid"
    s_g_str_Section_TaskName_StrParam="name_strparam"
    s_g_str_Section_TaskName_LongParam="name_longParam"

    def __init__(self):
        self.Clear()
        pass

    # 导出到字符串
    def ExportToStr(self):
        exDict={
            self.s_g_str_Section_TaskUID: self.s_dict_TaskUID,
            self.s_g_str_Section_TaskName_StrParam: self.s_dict_TaskName_strParam_UID,
            self.s_g_str_Section_TaskName_LongParam: self.s_dict_TaskName_LongParam_UID,
        }
        strTotal=json.dumps(exDict, ensure_ascii=True)
        return strTotal

    # 从字符串中读取
    def LoadFromStr(self, strContent):
        bRet = False

        self.Clear()

        if(strContent):
            try:
                dictContent=json.loads(strContent)


                strTryKey=self.s_g_str_Section_TaskUID
                if ( strTryKey in dictContent.keys()):
                    self.s_dict_TaskUID.update(dictContent[strTryKey])

                strTryKey = self.s_g_str_Section_TaskName_StrParam
                if (strTryKey in dictContent.keys()):
                    self.s_dict_TaskName_strParam_UID.update(dictContent[strTryKey])

                strTryKey = self.s_g_str_Section_TaskName_LongParam
                if (strTryKey in dictContent.keys()):
                    self.s_dict_TaskName_LongParam_UID.update(dictContent[strTryKey])

                bRet=True
            except Exception as e:
                #CTYLB_Log.ShowLog(1, "comu-fiber-list load msg error", str(e))
                CTYLB_MainSys_MiscFunc.ShowExceptionInfo(e)

        return bRet

    def Clear(self):
        self.s_dict_TaskUID={} # 任务UID列表。key=UID, 内容=0
        self.s_dict_TaskName_strParam_UID={} # 任务名字-参数：UID
        self.s_dict_TaskName_LongParam_UID={}  #任务名字-long参数，UID

    # 从FiberMang中读取内容
    def GetFromFiberMang(self, fiberMang):
        self.Clear()

        for eachFiberUID in fiberMang.s_dictUIDFiberTasks.keys():
            fiberUnit = fiberMang.s_dictUIDFiberTasks[eachFiberUID]
            if(fiberUnit.s_bExRemoteCallMe):
                self.s_dict_TaskUID[eachFiberUID] = 0

        for eachFiberStrParam in fiberMang.s_dictStrParamFiberTasks.keys():
            fiberUnit = fiberMang.s_dictStrParamFiberTasks[eachFiberStrParam]
            if(fiberUnit.s_bExRemoteCallMe):
                self.s_dict_TaskName_strParam_UID[eachFiberStrParam]= fiberUnit.s_lUniqueID

        for eachFiberLongParam in fiberMang.s_dictLongLongParamFiberTasks.keys():
            fiberUnit = fiberMang.s_dictLongLongParamFiberTasks[eachFiberLongParam]
            if(fiberUnit.s_bExRemoteCallMe):
                self.s_dict_TaskName_LongParam_UID[eachFiberLongParam] = fiberUnit.s_lUniqueID

    # 判断是否包含
    def IsContain_Key_StrParam(self, strParamKey):
        bRet=False
        if( strParamKey and (strParamKey in self.s_dict_TaskName_strParam_UID.keys())):
            bRet=True
        return bRet

    # 判断是否包含
    def IsContain_Key_StrLongParam(self, strLongParamKey):
        bRet=False
        if( strLongParamKey and (strLongParamKey in self.s_dict_TaskName_LongParam_UID.keys())):
            bRet=True
        return bRet



# 天元FiberBot实例,实现NATs客户端
class TYFiberBot_Mang_NATS_Instance_Base:
    def __init__(self, config_file="config/config.yaml", funcCallBack=None):
        # 保存本地变了
        self.s_funcTimerCallBack = funcCallBack


        # 创建进程间通信单元
        self.s_AsyncNATS_ProcComu=None
        self.v_CreateAsyncProcComu(config_file)
        if(self.s_AsyncNATS_ProcComu):
            self.s_AsyncNATS_ProcComu.StartComu()

        # 纤程管理单元实现
        self.s_FiberMang = FiberMang()

        # 初始化Fiber管理
        # 对信息传递 以纤程单元实现。收到nats服务器信息，判断是否在本地队列。不在，则发送给tybot

        pass

    # 创建异步进程通信单元
    def v_CreateAsyncProcComu(self, config_file):
        pass

    def Run(self):
        while(FBotV4.GetGlobalIsRunning()):
            self.LoopEventCallBack()

    # 单位时间不断调用
    def v_TimerCheck(self):
        return False

    def LoopEventCallBack(self):
        if(self.s_AsyncNATS_ProcComu):
            self.s_AsyncNATS_ProcComu.CheckRecv_Handle()

        self.s_FiberMang.TimerCheck()
        self.s_FiberMang.CheckTaskSleep()

        if (self.s_funcTimerCallBack):
            self.s_funcTimerCallBack()

        self.v_TimerCheck()

        pass

    def Quit(self):
        global IS_SYS_RUNNING
        IS_SYS_RUNNING = False

    def AddFiberUnit(self, fiberUnit):
        self.s_FiberMang.AddTask(fiberUnit)
        fiberUnit.v_SetParentMang(self.s_FiberMang)
