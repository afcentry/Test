# FbTBot_UTRC_Client.py
# 纤程任务 bot,UTRC客户端单元实现
# start by sk. 180414


from .FiberFBot import TYFiberBot_Mang_NATS_Instance_Base, CAsyncNats_ProcComu, CUTRC_NATs_ComuFiberList
from .ShareCfgDef import Share_UTRC_CfgDef
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CTylb_Bot_Exec_Frame
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CTYLB_MainSys_MiscFunc, CSkBot_Common_Share
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.FBot.fbotV4 import FBotV4
from TYBotSDK2.FiberFBot.FiberMangReal import CUTRC_NATs_Comu_RunMessageUnit


# FBot UTRC Client单元，处理异步通信的实现类
class CAsyncNats_UTRCClient_ProcComu(CAsyncNats_ProcComu):
    def __init__(self, strNATSServerAddr, strSelfRecvName):
        self.s_recvClientCmdMsgArray=[]  # 接收到客户端需要执行的命令队列。包含：源名字，目标名字 CUTRC_NATs_Comu_RunMessageUnit
        self.s_recvClient_CmdReplyMsgResult_Array=[]  # 接收到客户端 _远端处理结果  CUTRC_NATs_Comu_RunMessageUnit
        self.s_recvSrv_Reply_QueryAllClient_Array=[]  # 接收到查询所有客户端的信息.

        CAsyncNats_ProcComu.__init__(self, strNATSServerAddr, strSelfRecvName)

    # 处理接收到的数据包
    def v_HandleRecvPacket(self, strFromName, iMsgType, strMsgContent):
        if(iMsgType == Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Run_Message):
            comuMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
            if(comuMsgUnit.LoadFromStr(strMsgContent)):
                self.s_recvClientCmdMsgArray.append(comuMsgUnit)
            pass

        elif(iMsgType == Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_Message_Result):
            comuReplyResultMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
            if(comuReplyResultMsgUnit.LoadFromStr(strMsgContent)):
                self.s_recvClient_CmdReplyMsgResult_Array.append(comuReplyResultMsgUnit)

        elif(iMsgType==Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_AllClientInfo):
            self.s_recvSrv_Reply_QueryAllClient_Array.append(strMsgContent)

        pass

    # 获得接收到的命令
    def Pop_Recv_EachClientCmdMsgUnit(self):
        retUnit=None
        if(len(self.s_recvClientCmdMsgArray)>0):
            retUnit=self.s_recvClientCmdMsgArray.pop(0)
        return retUnit

    # 获得接收到的返回命令
    def Pop_Recv_Client_ReplyCmdMsgResult(self):
        retUnit=None
        if(len(self.s_recvClient_CmdReplyMsgResult_Array)>0):
            retUnit=self.s_recvClient_CmdReplyMsgResult_Array.pop(0)
        return retUnit

    # 获得接收到的所有客户端信息
    def Pop_Recv_Reply_QueryAllClient(self):
        retInfo=None
        if(len(self.s_recvSrv_Reply_QueryAllClient_Array)>0):
            retInfo=self.s_recvSrv_Reply_QueryAllClient_Array.pop(0)
        return retInfo


# 天元FiberBot实例,作为UTRC的客户端，简单APP
class TYFiberBot_Mang_NATS_UTRClient_Instance(TYFiberBot_Mang_NATS_Instance_Base):
    def __init__(self, config_file="config/config.yaml", funcCallBack=None):
        TYFiberBot_Mang_NATS_Instance_Base.__init__(self, config_file, funcCallBack)

        # 如果有更新，2秒发一次。否则，半分钟发一次 我的单元列表
        self.s_TimerCheck=CSkBot_Common_Share.CSkBot_TimeIdentify(2)
        self.s_AlwaysSendFbUnitList_TimerCheck=CSkBot_Common_Share.CSkBot_TimeIdentify(30)
        self.s_FBotSendFbUnitList_TimerCheck=CSkBot_Common_Share.CSkBot_TimeIdentify(30)

        CLessTYBotFrameThread.SetDefaultConsoleCompatible(FBotV4.environment_event_handle)

        # 初始化，加载FBot的配置
        strFBotUTRC_Server = CTylb_Bot_Exec_Frame.ReadIniSectionValue(
            config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC, Share_UTRC_CfgDef.g_str_key_FBot_UTRC_Server, "")
        self.s_utrcFBot = None

        self.s_toBeSend_FBot_PackageArray = []  # 等到发送给伙伴FBot的数据包队列
        self.s_timeDiff_SendInit = CSkBot_Common_Share.CSkBot_TimeIdentify(1)

        if( strFBotUTRC_Server):
            loopCallBack=[]
            if(self.s_funcTimerCallBack):
                loopCallBack.append((self.s_funcTimerCallBack))
            loopCallBack.append(self.LoopEventCallBack)

            connectUTRCFBotSrvAddr={strFBotUTRC_Server: [Share_UTRC_CfgDef.g_iFbUTRC_AcceptExecClient_ListenPort]}
            self.s_utrcFBot=FBotV4(connect_to_socks=connectUTRCFBotSrvAddr, loop_event_callbacks=loopCallBack,
                                   config_file=config_file )

            self.s_utrcFBot.add_connect_to_callbacks(
                sock_id=strFBotUTRC_Server, sock_port=Share_UTRC_CfgDef.g_iFbUTRC_AcceptExecClient_ListenPort,
                cmd_id=Share_UTRC_CfgDef. g_iFBot_Cmd_Nop_SendEcho_To_Srv,
                callback=self.OnFBot_InitCall_LoopSendToSrv, is_auto_callback=True)

            self.s_utrcFBot.add_connect_to_callbacks(
                sock_id=strFBotUTRC_Server, sock_port=Share_UTRC_CfgDef.g_iFbUTRC_AcceptExecClient_ListenPort,
                cmd_id=Share_UTRC_CfgDef.g_iFBot_Cmd_NeedExecCmd_To_Client,
                callback=self.OnFBot_Client_Cmd_NeedExecCmd, is_auto_callback=False)

            self.s_utrcFBot.add_connect_to_callbacks(
                sock_id=strFBotUTRC_Server, sock_port=Share_UTRC_CfgDef.g_iFbUTRC_AcceptExecClient_ListenPort,
                cmd_id=Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_Message_Result,
                callback=self.OnFBot_Client_Cmd_ReplyMessageResult, is_auto_callback=False)

        pass

    # 创建异步进程通信单元
    def v_CreateAsyncProcComu(self, config_file):
        # 创建进程间通信单元
        strNatSrvAddr = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC,
                                                                 Share_UTRC_CfgDef.g_str_key_NATs_Addr, "")
        self.s_strNATSProcServerName = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC,
                                                                                Share_UTRC_CfgDef.g_str_key_NAT_Proc_ServerName, "")
        self.s_strNATSProcSelfName = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC,
                                                                              Share_UTRC_CfgDef.g_str_key_NAT_Proc_ServerName, "")
        strSelfNATSProcComuName = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FBot,
                                                                           Share_UTRC_CfgDef.g_str_key_myid, "")

        if(strNatSrvAddr and self.s_strNATSProcServerName and self.s_strNATSProcSelfName and strSelfNATSProcComuName):
            self.s_AsyncNATS_ProcComu = CAsyncNats_UTRCClient_ProcComu(strNATSServerAddr=strNatSrvAddr,
                                                            strSelfRecvName=strSelfNATSProcComuName)
        else:
            CTYLB_Log.ShowLog(1, "NATS-Client_NotCreate", "")

        pass


    # 执行-FBot，事件 - 不断调用，发送echo数据包
    def OnFBot_InitCall_LoopSendToSrv(self, value, param1, param2, is_last_package):
        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            # 是否到了时间，不断广播我的单元状态?
            retCTUnitArray = self.GetPackages_Send_To_FBotSrv()

        return retCTUnitArray

    # 执行-FBot服务器，发送给客户端，需要执行命令
    def OnFBot_Client_Cmd_NeedExecCmd(self, value, param1, param2, is_last_package):
        # 分析执行此数据包
        comuMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
        if (comuMsgUnit.LoadFromStr(value)):
            comuUtrcExecResult = self.s_FiberMang.HandleExRemoteExecCmd(comuMsgUnit)
            # 执行完成后，返回此数据包
            execResultPackage = FBotV4.make_package(Share_UTRC_CfgDef.g_iFBot_Cmd_Reply_ExecMsg_To_Srv,
                                                    comuUtrcExecResult.ExportToStr())
            self.s_toBeSend_FBot_PackageArray.append(execResultPackage)

        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.GetPackages_Send_To_FBotSrv()

        return retCTUnitArray

    # 执行-FBot服务器，发送给客户端，执行命令的结果
    def OnFBot_Client_Cmd_ReplyMessageResult(self, value, param1, param2, is_last_package):
        # 分析执行此数据包
        comuMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
        if (comuMsgUnit.LoadFromStr(value)):
            self.s_FiberMang.HandleExReplyRemoteExecResult(comuMsgUnit)

        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.GetPackages_Send_To_FBotSrv()

        return retCTUnitArray


    # 获得需要发送给 FBot服务端的数据包
    def GetPackages_Send_To_FBotSrv(self):
        retCTUnitArray = []

        bSendList = True
        # 如果没有修改，则等更长时间再发送
        if (not self.s_FiberMang.PopRetrive_RemoteExec()):
            if (not self.s_FBotSendFbUnitList_TimerCheck.CheckTimeDiff()):
                bSendList = False
        if (bSendList):
            # 发送纤程列表名字
            comuFiberList = CUTRC_NATs_ComuFiberList()
            comuFiberList.GetFromFiberMang(self.s_FiberMang)

            retCTUnitArray.append(FBotV4.make_package(Share_UTRC_CfgDef.g_iFBot_Cmd_Report_FbUnitList_To_Srv,
                                                      comuFiberList.ExportToStr()))

        if(self.s_toBeSend_FBot_PackageArray):
            retCTUnitArray.extend(self.s_toBeSend_FBot_PackageArray)
            self.s_toBeSend_FBot_PackageArray.clear()

        if(not retCTUnitArray):
            if(self.s_timeDiff_SendInit.CheckTimeDiff()):
                retCTUnitArray.append(FBotV4.make_package(Share_UTRC_CfgDef.g_iFBot_Cmd_Nop_SendEcho_To_Srv))

        return retCTUnitArray

    # 单位时间不断调用
    def v_TimerCheck(self):
        bRetValue = False
        # 每隔2秒钟，广播我的客户端列表。
        if(self.s_TimerCheck.CheckTimeDiff()):
            bSendList=True
            # 如果没有修改，则等更长时间再发送
            if(not self.s_FiberMang.Pop_Reset_LastModifyFlag()):
                if(not self.s_AlwaysSendFbUnitList_TimerCheck.CheckTimeDiff()):
                    bSendList=False
            if(bSendList):
                self.Exec_SendUTRC_FiberList()

            bRetValue = True

        # 检查需要发送到远端的命令
        iExecCount=0
        while(iExecCount<5):
            nextRemoteExecMsgUnit=self.s_FiberMang.PopRetrive_RemoteExec()
            if(nextRemoteExecMsgUnit):
                # 执行，提交到远端服务端，进行发送
                strExecContent=nextRemoteExecMsgUnit.ExportToStr()
                if(self.s_AsyncNATS_ProcComu):
                    self.s_AsyncNATS_ProcComu.AddContentToSend(
                        self.s_strNATSProcServerName, Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Run_Message,
                        strExecContent )
                if(self.s_utrcFBot):
                    newPackage=FBotV4.make_package(Share_UTRC_CfgDef.g_iFbot_Cmd_TransExecMsg_To_Srv,strExecContent)
                    self.s_toBeSend_FBot_PackageArray.append(newPackage)
                bRetValue=True
            else:
                break
            iExecCount+=1

        # 检查异步进程通信，处理接收的命令
        if(self.Exec_CheckExec_RecvAsyncProcComuCmd()):
            bRetValue=True

        if(self.Exec_CheckExec_RecvAsyncProcCmd_ReplyCmdResult()):
            bRetValue=True

        return bRetValue

    # 检查接收的数据包
    def Exec_CheckExec_RecvAsyncProcComuCmd(self):
        bRetValue=False

        if(self.s_AsyncNATS_ProcComu):
            iExecCount=0
            while(iExecCount<5):
                nextRemoteExecMsgUnit = self.s_AsyncNATS_ProcComu.Pop_Recv_EachClientCmdMsgUnit()
                if(nextRemoteExecMsgUnit):
                    # 处理，执行
                    comuUtrcExecResult = self.s_FiberMang.HandleExRemoteExecCmd(nextRemoteExecMsgUnit)
                    self.s_AsyncNATS_ProcComu.AddContentToSend(self.s_strNATSProcServerName,
                                                               Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_Message_Result,
                                                               comuUtrcExecResult.ExportToStr())
                    bRetValue=True
                else:
                    break
                iExecCount+=1

        return bRetValue

    # 检查接收的数据包
    def Exec_CheckExec_RecvAsyncProcCmd_ReplyCmdResult(self):
        bRetValue=False

        if(self.s_AsyncNATS_ProcComu):
            iExecCount=0
            while(iExecCount<5):
                nextRemote_ReplyExecMsg_Result = self.s_AsyncNATS_ProcComu.Pop_Recv_Client_ReplyCmdMsgResult()
                if(nextRemote_ReplyExecMsg_Result):
                    # 处理，执行
                    self.s_FiberMang.HandleExReplyRemoteExecResult(nextRemote_ReplyExecMsg_Result)
                    bRetValue=True
                else:
                    break
                iExecCount+=1

        return bRetValue


    # 执行发送
    def Exec_SendUTRC_FiberList(self):
        # 获得单元列表
        comuFiberList = CUTRC_NATs_ComuFiberList()
        comuFiberList.GetFromFiberMang(self.s_FiberMang)

        strFiberListContent = comuFiberList.ExportToStr()

        if(self.s_AsyncNATS_ProcComu):
            # 发送到远端
            self.s_AsyncNATS_ProcComu.AddContentToSend(
                self.s_strNATSProcServerName, Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Report_FiberUnitArray,
                strFiberListContent)

        if(self.s_utrcFBot):
            # 此处工作，已经在另外地方执行。
            pass
        pass

    # 执行运行
    def Run(self):
        if(self.s_utrcFBot):
            self.s_utrcFBot.run()
        else:
            TYFiberBot_Mang_NATS_Instance_Base.Run(self)
