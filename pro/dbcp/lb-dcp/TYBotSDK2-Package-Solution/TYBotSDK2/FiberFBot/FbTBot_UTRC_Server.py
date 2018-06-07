# FbTBot_UTRC_Server.py
# 纤程单元机器人-UTRC-服务端实现, 自动处理 客户端的列表单元，自动进行维护。自动进行消息中转。
#  自动进行FBot和远端的衔接
# start by sk. 180414
# add by sk. 180503. 增加请求客户端信息列表

from TYBotSDK2.FBot.fbotV4 import FBotV4
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CTYLB_MainSys_MiscFunc, CSkBot_Common_Share
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CTylb_Bot_Exec_Frame
from TYBotSDK2.FiberFBot.FiberMangReal import FiberMang
from .ShareCfgDef import Share_UTRC_CfgDef
from TYBotSDK2.FiberFBot.FiberFBot import CAsyncNats_ProcComu, TYFiberBot_Mang_NATS_Instance_Base, CUTRC_NATs_ComuFiberList
from TYBotSDK2.FiberFBot.FiberMangReal import CUTRC_NATs_Comu_RunMessageUnit
import json

# FBot UTRC服务单元，处理异步通信的实现类
class CAsyncNats_UTRCSrv_ProcComu(CAsyncNats_ProcComu):
    def __init__(self, strNATSServerAddr, strSelfRecvName):
        self.s_recvClientFibersDicts={} # 接收到客户端 纤程名字典. key=客户端名字, 内容=CUTRC_NATs_ComuFiberList
        self.s_recvClientCmdMsgArray=[]  # 接收到客户端需要执行的命令队列。包含：源名字，目标名字 CUTRC_NATs_Comu_RunMessageUnit
        self.s_recvClientReplyCmdMsgResult_Array=[]  # 接收到客户端执行返回的命令队列。包含：源名字，目标名字 CUTRC_NATs_Comu_RunMessageUnit
        self.s_recvClient_RequestAllClientInfo_Array=[]  # 请求所有客户端信息队列。 包含：请求的客户端列表

        CAsyncNats_ProcComu.__init__(self, strNATSServerAddr, strSelfRecvName)

    # 处理接收到的数据包
    def v_HandleRecvPacket(self, strFromName, iMsgType, strMsgContent):
        if(iMsgType == Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Report_FiberUnitArray):

            comuFiberNamesUnit = CUTRC_NATs_ComuFiberList()
            if(comuFiberNamesUnit.LoadFromStr(strMsgContent)):
                CTYLB_Log.ShowLog(0, "Recv %s Report Fiber" % (strFromName), "count:%d" % (len(comuFiberNamesUnit.s_dict_TaskName_strParam_UID)))
                self.s_recvClientFibersDicts[strFromName] = comuFiberNamesUnit

        elif(iMsgType == Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Run_Message):
            comuMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
            if(comuMsgUnit.LoadFromStr(strMsgContent)):
                self.s_recvClientCmdMsgArray.append(comuMsgUnit)
            pass

        elif(iMsgType == Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_Message_Result):
            comuReplyMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
            if(comuReplyMsgUnit.LoadFromStr(strMsgContent)):
                self.s_recvClientReplyCmdMsgResult_Array.append(comuReplyMsgUnit)
            pass

        elif(iMsgType==Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Request_AllClientInfo):
            self.s_recvClient_RequestAllClientInfo_Array.append(strFromName)
            pass

        # self.AddContentToSend(eachRecvMsg.s_strPeerMsgName, eachRecvMsg.s_iMsgType, strReplyContent)
        pass

    # 获得接收到的客户端 纤程字典
    def Pop_Recv_ClientFiberDict(self):
        retDict={}
        if(self.s_recvClientFibersDicts):
            retDict = self.s_recvClientFibersDicts
            self.s_recvClientFibersDicts={}

        return retDict

    # 获得接收到的命令
    def Pop_Recv_EachClientCmdMsgUnit(self):
        retUnit=None
        if(len(self.s_recvClientCmdMsgArray)>0):
            retUnit=self.s_recvClientCmdMsgArray.pop(0)
        return retUnit

    # 获得接收到的命令
    def Pop_Recv_EachClient_ReplyCmdMsgResultUnit(self):
        retUnit=None
        if(len(self.s_recvClientReplyCmdMsgResult_Array)>0):
            retUnit=self.s_recvClientReplyCmdMsgResult_Array.pop(0)
        return retUnit

    # 获得请求列表单元
    # add by sk. 180503
    def Pop_Recv_Request_AllClientInfo(self):
        retClientName=""
        if(len(self.s_recvClient_RequestAllClientInfo_Array)>0):
            retClientName=self.s_recvClient_RequestAllClientInfo_Array.pop(0)
        return retClientName


# 天元FiberBot实例,实现NATs客户端，同时作为UTRC服务端节点
class TYFiberBot_Mang_UTRC_NATS_Instance(TYFiberBot_Mang_NATS_Instance_Base):
    def __init__(self, config_file="config/config.yaml", funcCallBack=None):
        TYFiberBot_Mang_NATS_Instance_Base.__init__(self,config_file,funcCallBack)
        pass

    # 创建异步进程通信单元
    def v_CreateAsyncProcComu(self, config_file):

        # 创建进程间通信单元
        strNatSrvAddr = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC,
                                                                 Share_UTRC_CfgDef.g_str_key_NATs_Addr, "")
        strSelfNATSProcServerName = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC,
                                                                             Share_UTRC_CfgDef.g_str_key_NAT_Proc_ServerName, "")

        self.s_AsyncNATS_ProcComu = CAsyncNats_UTRCSrv_ProcComu(strNATSServerAddr=strNatSrvAddr,
                                                        strSelfRecvName=strSelfNATSProcServerName)
        pass

# Fiber纤程单元的列表
# start by sk. 180415
class Collect_FbNameDict_Mang:
    s_g_iType_LocalPeerNats = 1  # 本地NAT节点
    s_g_iType_Peer_FBot = 2  # 伙伴FBot服务器
    s_g_iType_Local_FBotClient = 3 # 本地的FBot客户端

    def __init__(self):
        self.s_totalNatsClientFbNamesDict = {}  # 总的NATs客户端 纤程单元 字典, key=NAT名字, value=CUTRC_NATs_ComuFiberList
        self.s_selfFBotClient_FbNamesDict = {}  # 我的FBot 客户端 纤程单元 字典, key=FBot-Client名字, value=CUTRC_NATs_ComuFiberList

        self.s_peerFBotSrv_Nats_FbNamesDict = {}  # 伙伴FBot服务器 它本地纤程单元 字典,  key=对方NAT名字, value=CUTRC_NATs_ComuFiberList
        self.s_peerFBotSrv_Fbot_ClientNamesDict = {}  # 伙伴FBot服务器 它FBot客户端的纤程单元 字典,  key=对方NAT名字, value=CUTRC_NATs_ComuFiberList

        self.s_bUpdate=False

    # 输出所有内容到字符串
    # add by sk. 180503
    def ExportAllToStr(self):
        strEx_NatsClientDict={}
        strEx_FBotClientDict={}
        strEx_PeerFBotSrv_Nats_ClientDict={}
        strEx_PeerFBotSrv_FBot_ClientDict={}

        for eachFName in self.s_totalNatsClientFbNamesDict.keys():
            eachUnit=self.s_totalNatsClientFbNamesDict[eachFName]
            strEx_NatsClientDict[eachFName] = eachUnit.ExportToStr()

        for eachFName in self.s_selfFBotClient_FbNamesDict.keys():
            eachUnit=self.s_selfFBotClient_FbNamesDict[eachFName]
            strEx_FBotClientDict[eachFName] = eachUnit.ExportToStr()

        for eachFName in self.s_peerFBotSrv_Fbot_ClientNamesDict.keys():
            eachUnit=self.s_peerFBotSrv_Fbot_ClientNamesDict[eachFName]
            strEx_PeerFBotSrv_FBot_ClientDict[eachFName] = eachUnit.ExportToStr()

        for eachFName in self.s_peerFBotSrv_Nats_FbNamesDict.keys():
            eachUnit=self.s_peerFBotSrv_Nats_FbNamesDict[eachFName]
            strEx_PeerFBotSrv_Nats_ClientDict[eachFName] = eachUnit.ExportToStr()

        dict={
            "NatsClient": strEx_NatsClientDict,
            "FBotlient": strEx_FBotClientDict,
            "PeerFBotSrv_NatsClient":strEx_PeerFBotSrv_Nats_ClientDict,
            "PeerFBotSrv_FBotClient":strEx_PeerFBotSrv_FBot_ClientDict,
        }
        strTotal=json.dumps(dict, ensure_ascii=False)
        return strTotal

    # 节点单元-纤程名字 字典- 从字符串中加载内容。
    # 字典的key=客户端名字. 内容=CUTRC_NATs_ComuFiberList
    @staticmethod
    def FbNamesDict_LoadFromStr(clientName_FbNames_Dict, strFullContent):
        bRet=False

        stNameContentDict=json.loads(strFullContent)

        clientName_FbNames_Dict.clear()
        for eachName in stNameContentDict.keys():
            combFibUnit = CUTRC_NATs_ComuFiberList()
            if(combFibUnit.LoadFromStr(stNameContentDict[eachName])):
                clientName_FbNames_Dict[eachName] = combFibUnit

        bRet=True
        return bRet

    # 节点单元-纤程名字 字典- 输出内容到 字符串中
    # 字典的key=客户端名字. 内容=CUTRC_NATs_ComuFiberList
    @staticmethod
    def FbNamesDict_ExportToStr(clientName_FbNames_Dict):
        strExportPrepareDict={}
        for eachName in clientName_FbNames_Dict.keys():
            comuFibUnit = clientName_FbNames_Dict[eachName]
            strExportPrepareDict[eachName] = comuFibUnit.ExportToStr()
        strTotal = json.dumps(strExportPrepareDict)
        return strTotal

    # 处理接收到的Nats客户端单元
    # 参数为一个字典。key=NAT客户端名字，内容=CUTRC_NATs_ComuFiberList
    def Handle_Recv_NATSClients_FbNames_Dict(self, recv_Client_FbNames_Dict):
        self.s_bUpdate=True
        for eachClientName in recv_Client_FbNames_Dict.keys():
            self.s_totalNatsClientFbNamesDict[eachClientName] = recv_Client_FbNames_Dict[eachClientName]
        pass

    s_g_str_Key_LocalPeerNats="peer_nats"
    s_g_str_Key_Local_FBotClient="local_fbot_clients"

    # 处理接收到的FBot-Peer服务端，的客户端单元列表
    def Handle_Recv_PeerFBot_FbNames_Dict(self, strContent):
        dictContent = json.loads(strContent)
        # 导入FBot列表
        if(self.s_g_str_Key_Local_FBotClient in dictContent.keys()):
            strFbotClientNamesDict = dictContent[self.s_g_str_Key_Local_FBotClient]
            Collect_FbNameDict_Mang.FbNamesDict_LoadFromStr(self.s_selfFBotClient_FbNamesDict, strFbotClientNamesDict)

        # 导入nats列表
        if (self.s_g_str_Key_LocalPeerNats in dictContent.keys()):
            strNatsClientNamesDict = dictContent[self.s_g_str_Key_LocalPeerNats]
            Collect_FbNameDict_Mang.FbNamesDict_LoadFromStr(self.s_totalNatsClientFbNamesDict,
                                                            strNatsClientNamesDict)

            pass

    # 处理接收到 FBot-ExecClient 的单元列表
    def Handle_Recv_FBot_ExecClient_FbNames_Dict(self, strClientName, strContent):
        execComuFbList = None
        if(strClientName in self.s_selfFBotClient_FbNamesDict.keys()):
            execComuFbList = self.s_selfFBotClient_FbNamesDict[strClientName]
        else:
            execComuFbList = CUTRC_NATs_ComuFiberList()
            self.s_selfFBotClient_FbNamesDict[strClientName] = execComuFbList

        if(execComuFbList):
            execComuFbList.LoadFromStr(strContent)

    # 构建发送给伙伴FBot的数据包。只发送 本地NATS和本地FBot客户端
    def Construct_Ex_PeerFBotSrv_Content(self):
        strLocalFBotClientNames = Collect_FbNameDict_Mang.FbNamesDict_ExportToStr(self.s_selfFBotClient_FbNamesDict)
        strNatsClientContentDict=Collect_FbNameDict_Mang.FbNamesDict_ExportToStr(self.s_totalNatsClientFbNamesDict)

        totalExDict={
            self.s_g_str_Key_Local_FBotClient: strLocalFBotClientNames,
            self.s_g_str_Key_LocalPeerNats: strNatsClientContentDict
        }

        strTotalEx=json.dumps(totalExDict)
        return strTotalEx

    # 根据节点地址单元，获得客户端位置信息。
    def GetRemoteClientName_By_FbUnit_Content(self, strTaskFullName, strTaskParam, lTaskParam1, lTaskParam2):
        iRetDomainType=0
        strRetClientName=''

        strStrParamKey, strLongKey=FiberMang.GetTaskKey(strTaskFullName, strTaskParam, lTaskParam1, lTaskParam2)

        for eachClientName in self.s_totalNatsClientFbNamesDict.keys():
            comuFbListUnit = self.s_totalNatsClientFbNamesDict[eachClientName]
            if(comuFbListUnit.IsContain_Key_StrParam(strStrParamKey) or
                   comuFbListUnit.IsContain_Key_StrLongParam(strLongKey)):
                strRetClientName=eachClientName
                iRetDomainType=self.s_g_iType_LocalPeerNats
                break

        if(not strRetClientName):
            for eachClientName in self.s_selfFBotClient_FbNamesDict.keys():
                comuFbListUnit = self.s_selfFBotClient_FbNamesDict[eachClientName]
                if(comuFbListUnit.IsContain_Key_StrParam(strStrParamKey) or
                       comuFbListUnit.IsContain_Key_StrLongParam(strLongKey)):
                    strRetClientName=eachClientName
                    iRetDomainType=self.s_g_iType_Local_FBotClient
                    break

        if(not strRetClientName):
            for eachClientName in self.s_peerFBotSrv_Nats_FbNamesDict.keys():
                comuFbListUnit = self.s_peerFBotSrv_Nats_FbNamesDict[eachClientName]
                if(comuFbListUnit.IsContain_Key_StrParam(strStrParamKey) or
                       comuFbListUnit.IsContain_Key_StrLongParam(strLongKey)):
                    strRetClientName=eachClientName
                    iRetDomainType=self.s_g_iType_Peer_FBot
                    break

        if(not strRetClientName):
            for eachClientName in self.s_peerFBotSrv_Fbot_ClientNamesDict.keys():
                comuFbListUnit = self.s_peerFBotSrv_Fbot_ClientNamesDict[eachClientName]
                if(comuFbListUnit.IsContain_Key_StrParam(strStrParamKey) or
                       comuFbListUnit.IsContain_Key_StrLongParam(strLongKey)):
                    strRetClientName=eachClientName
                    iRetDomainType=self.s_g_iType_Peer_FBot
                    break

        return iRetDomainType, strRetClientName


# 天元FiberBot实例。FBot功能包含
class TYFiberBot_UTRCSrv_FBot_Instance(TYFiberBot_Mang_UTRC_NATS_Instance):
    def __init__(self, config_file="config/config.yaml", funcCallBack=None):
        self.s_collect_FbNameDict_Mang = Collect_FbNameDict_Mang()  # 集合纤程单元的管理


        # 临时存储处理FBot-客户端的Fb单元列表 字典
        self.s_recvFBotClientFibersDicts={} # 接收到FBot客户端 纤程名字典. key=FBot客户端名字, 内容=CUTRC_NATs_ComuFiberList

        TYFiberBot_Mang_UTRC_NATS_Instance.__init__(self, config_file, funcCallBack)
        # 保存本地变了

        iFbUTRC_ListenPeer_Port = Share_UTRC_CfgDef.g_iFbUTRC_ListenPeer_Port  # 纤程TRC服务器的监听端口
        # 线程UTRC服务器，对FBot客户端的监听端口
        iFbUTRC_AcceptExecClient_ListenPort=Share_UTRC_CfgDef.g_iFbUTRC_AcceptExecClient_ListenPort

        connectSrvAddr={}
        strPeerFbUTCServerAddr = CTylb_Bot_Exec_Frame.ReadIniSectionValue(config_file, Share_UTRC_CfgDef.g_str_section_FiberUTRC,
                                                                           Share_UTRC_CfgDef.g_str_key_FbUTRC_FBot_PeerServerAddr, "")
        if(strPeerFbUTCServerAddr):
            connectSrvAddr[strPeerFbUTCServerAddr] = [iFbUTRC_ListenPeer_Port]

        # 创建FBot服务器
        loopCallBack=[]
        if(self.s_funcTimerCallBack):
            loopCallBack=[self.s_funcTimerCallBack]

        loopCallBack.append(self.LoopEventCallBack)
        self.s_RunFBotV4=FBotV4(listen_socks=[iFbUTRC_ListenPeer_Port, iFbUTRC_AcceptExecClient_ListenPort],
                                listen_accpet_callback=self.FBot_Listen_Accept_Callback,
                                config_file=config_file, loop_event_callbacks=loopCallBack,
                                connect_to_socks=connectSrvAddr)

        # 针对 PeerSrv的消息处理
        self.s_RunFBotV4.add_listen_callbacks( Share_UTRC_CfgDef.g_iPeerFbUTRC_Cmd_BroadCast_Peer_FbUnitNames,
                                               self.OnListen_Recv_Peer_BroadCastFbUnitName)
        self.s_RunFBotV4.add_listen_callbacks(Share_UTRC_CfgDef.g_iPeerFbUTRC_Cmd_NeedPeerFBot_Run_Message,
                                              self.OnListen_Recv_Peer_ExecRunMessage)

        # 针对 FBot-ExecClient - g_iFbUTRC_AcceptExecClient_ListenPort 的消息处理. client发到utrc服务端的
        self.s_RunFBotV4.add_listen_callbacks(Share_UTRC_CfgDef.g_iFBot_Cmd_Nop_SendEcho_To_Srv,
                                              self.OnListen_Recv_Client_Nop_SendEcho)
        self.s_RunFBotV4.add_listen_callbacks(Share_UTRC_CfgDef.g_iFbot_Cmd_TransExecMsg_To_Srv,
                                              self.OnListen_Recv_Client_TransExecMsg)
        self.s_RunFBotV4.add_listen_callbacks(Share_UTRC_CfgDef.g_iFBot_Cmd_Report_FbUnitList_To_Srv,
                                              self.OnListen_Recv_Client_Report_FbUnitList)
        self.s_RunFBotV4.add_listen_callbacks(Share_UTRC_CfgDef.g_iFBot_Cmd_Reply_ExecMsg_To_Srv,
                                              self.OnListen_Recv_Client_Reply_execMsg)


        if(strPeerFbUTCServerAddr):
            self.s_RunFBotV4.add_connect_to_callbacks(
                sock_id=strPeerFbUTCServerAddr, sock_port=Share_UTRC_CfgDef.g_iFbUTRC_ListenPeer_Port,
                cmd_id=Share_UTRC_CfgDef.g_iPeerFbUTRC_Cmd_BroadCast_Peer_FbUnitNames,
                callback=self.OnFBot_PeerSrv_BroadCastPeerFbUnitName, is_auto_callback=True)

        # 初始化Fiber管理
        # 对信息传递 以纤程单元实现。收到nats服务器信息，判断是否在本地队列。不在，则发送给tybot
        self.s_TimerDiff_PeerFBotSrv_FbUnit_Notify = CSkBot_Common_Share.CSkBot_TimeIdentify(30)
        self.s_toBeSend_PeerFBot_FbNames_Package = None  # 等待发送的广播名字数据包
        self.s_toBeSend_PeerFBot_PackageArray = []  # 等到发送给伙伴FBot的数据包队列
        self.s_toBeSend_FBotClient_PackageDict={}  # 等待发送给 客户端的 Package. key=名字, 内容=[]

        pass

    # 回复数据包 需要发送给 伙伴FBot的
    def ReplyPackage_Send_To_PeerFBot(self, strPeerName):
        retCTUnitArray=[]
        if (self.s_toBeSend_PeerFBot_FbNames_Package):
            retCTUnitArray.append(self.s_toBeSend_PeerFBot_FbNames_Package)
            self.s_toBeSend_PeerFBot_FbNames_Package = None
        if(self.s_toBeSend_PeerFBot_PackageArray):
            retCTUnitArray.extend(self.s_toBeSend_PeerFBot_PackageArray)
            self.s_toBeSend_PeerFBot_PackageArray.clear()

        return retCTUnitArray

    # 回复数据包 需要发送给 客户端的
    def ReplyPackage_Send_To_ExecClient(self, strClientName):
        # 把需要执行的命令包发送出去
        retCTUnitArray=[]
        if(strClientName in  self.s_toBeSend_FBotClient_PackageDict.keys()):
            execClientDict = self.s_toBeSend_FBotClient_PackageDict[strClientName]
            retCTUnitArray.extend(execClientDict)
            execClientDict.clear()

        return retCTUnitArray

    # 执行-FBot-执行客户端，发送握手包
    def OnListen_Recv_Client_Nop_SendEcho(self, peerName, value, param1, param2, is_last_package):
        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_ExecClient(peerName)

        return retCTUnitArray

    # 执行-FBot-执行客户端，执行命令
    def OnListen_Recv_Client_TransExecMsg(self, peerName, value, param1, param2, is_last_package):
        # 把需要的数据包发送出去
        self.ExecRunMessage(Collect_FbNameDict_Mang.s_g_iType_Local_FBotClient, value)
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_ExecClient(peerName)

        return retCTUnitArray

    # 执行-FBot-执行客户端，广播 纤程单元
    def OnListen_Recv_Client_Report_FbUnitList(self, peerName, value, param1, param2, is_last_package):
        # 处理接收到内容
        self.s_collect_FbNameDict_Mang.Handle_Recv_FBot_ExecClient_FbNames_Dict(peerName, value)

        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_ExecClient(peerName)

        return retCTUnitArray

    # 执行-FBot-执行客户端，回应执行结果
    def OnListen_Recv_Client_Reply_execMsg(self, peerName, value, param1, param2, is_last_package):
        # 处理接收到内容
        # 对执行结构进行分析。找到源对象，发送返回结果.
        self.Exec_Reply_Message_Result(Collect_FbNameDict_Mang.s_g_iType_Local_FBotClient, value)

        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_ExecClient(peerName)

        return retCTUnitArray



    # 执行-伙伴FBot服务器，连接-广播 纤程单元
    def OnFBot_PeerSrv_BroadCastPeerFbUnitName(self, peerName, value, param1, param2, is_last_package):
        # 把需要的数据包发送出去
        retCTUnitArray=[]
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_PeerFBot(peerName)

        return retCTUnitArray

    # 伙伴FBot监听模式，接收到伙伴FBot的广播 纤程单元列表
    # start by sk. 180415
    def OnListen_Recv_Peer_BroadCastFbUnitName(self, peerName, value, param1, param2, is_last_package):
        CTYLB_Log.ShowLog(0, "from %s"%(peerName), "recv fiber name list")
        self.s_collect_FbNameDict_Mang.Handle_Recv_PeerFBot_FbNames_Dict(value)

        retCTUnitArray = []
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_PeerFBot(peerName)
        return retCTUnitArray


    # 伙伴FBot监听模式，接收到伙伴FBot的 执行命令的请求
    # start by sk. 180415
    def OnListen_Recv_Peer_ExecRunMessage(self, peerName, value, param1, param2, is_last_package):
        # 找到节点，投递，执行命令
        CTYLB_Log.ShowLog(0, "from %s" % (peerName), "recv peer-fbot-srv exec fiber cmd")

        self.ExecRunMessage(Collect_FbNameDict_Mang.s_g_iType_Peer_FBot, value)

        retCTUnitArray = []
        if(is_last_package):
            retCTUnitArray = self.ReplyPackage_Send_To_PeerFBot(peerName)
        return retCTUnitArray

    def FBot_Listen_Accept_Callback(self, **kwargs):
        strTotal=""
        for key in kwargs:
            strTotal += " %s"%(str(kwargs[key]))
        CTYLB_Log.ShowLog(0, "listen_accept", strTotal)
        pass

    def Run(self):
        self.s_RunFBotV4.run()

    # 获得 from和dest的描述名字
    @staticmethod
    def GetFromDestFullName(comuMsgUnit):
        strFromSub = ""
        if (comuMsgUnit.s_strFromFbUnit_StrParam and
                comuMsgUnit.s_lFromFbUnit_lParam1 and comuMsgUnit.s_lFromFbUnit_lParam2):
            strFromSub = ":%s:%d:%d" % (comuMsgUnit.s_strFromFbUnit_StrParam,
                                        comuMsgUnit.s_lFromFbUnit_lParam1, comuMsgUnit.s_lFromFbUnit_lParam2)
        strFrom = "%s%s" % (comuMsgUnit.s_strFromFbUnit_FullName, strFromSub)

        strDestSub = ""
        if (comuMsgUnit.s_strDestFbUnit_StrParam and
                comuMsgUnit.s_lDestFbUnit_lParam1 and comuMsgUnit.s_lDestFbUnit_lParam2):
            strDestSub = ":%s:%d:%d" % (comuMsgUnit.s_strDestFbUnit_StrParam,
                                        comuMsgUnit.s_lDestFbUnit_lParam1, comuMsgUnit.s_lDestFbUnit_lParam2)

        strDest = "%s%s" % (comuMsgUnit.s_strDestFbUnit_FullName, strDestSub)

        return strFrom, strDest

    # 执行 来自各个方面的 运行消息。
    def ExecRunMessage(self, iFromDomainType, strMsgContent):
        comuMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
        if (comuMsgUnit.LoadFromStr(strMsgContent)):
            strFrom, strDest = self.GetFromDestFullName(comuMsgUnit)
            CTYLB_Log.ShowLog(0, "请求执行", "[%s] -> [%s]:%d" % (strFrom, strDest, comuMsgUnit.s_iRun_MessageID))

            iDomainType, strDestClientName = self.s_collect_FbNameDict_Mang.GetRemoteClientName_By_FbUnit_Content(
                comuMsgUnit.s_strDestFbUnit_FullName, comuMsgUnit.s_strDestFbUnit_StrParam,
                comuMsgUnit.s_lDestFbUnit_lParam1, comuMsgUnit.s_lDestFbUnit_lParam2)
            if (strDestClientName):
                if (iDomainType == Collect_FbNameDict_Mang.s_g_iType_LocalPeerNats):
                    # 传递给该client单元
                    self.s_AsyncNATS_ProcComu.AddContentToSend(
                        strDestClientName, Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Run_Message,
                        strMsgContent)

                elif (iDomainType == Collect_FbNameDict_Mang.s_g_iType_Local_FBotClient):
                    # 增加到队列
                    newPackage = FBotV4.make_package(command_id=Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Run_Message,
                                                     value=strMsgContent)
                    # 传递给FBot单元
                    toBeSendArray = []
                    if (strDestClientName in self.s_toBeSend_FBotClient_PackageDict.keys()):
                        toBeSendArray = self.s_toBeSend_FBotClient_PackageDict[strDestClientName]
                    else:
                        self.s_toBeSend_FBotClient_PackageDict[strDestClientName] = toBeSendArray
                    toBeSendArray.append(newPackage)

                elif (iDomainType == Collect_FbNameDict_Mang.s_g_iType_Peer_FBot):
                    # 增加到队列
                    newPackage = FBotV4.make_package(command_id=Share_UTRC_CfgDef.g_iPeerFbUTRC_Cmd_NeedPeerFBot_Run_Message,
                                                     value=strMsgContent)
                    # 传递给FBot单元
                    self.s_toBeSend_PeerFBot_PackageArray.append(newPackage)
                    pass
            else:
                CTYLB_Log.ShowLog(1, "Not Found Dest", "%s -> %s" % (strFrom, strDest))
                pass

        pass


    # 执行 来自各个方面的 运行消息的结果，返回初始单元
    def Exec_Reply_Message_Result(self, iFromDomainType, strMsgContent):
        comuMsgUnit_ReplyResult = CUTRC_NATs_Comu_RunMessageUnit()
        if (comuMsgUnit_ReplyResult.LoadFromStr(strMsgContent)):
            iDomainType, strDestClientName = self.s_collect_FbNameDict_Mang.GetRemoteClientName_By_FbUnit_Content(
                comuMsgUnit_ReplyResult.s_strFromFbUnit_FullName, comuMsgUnit_ReplyResult.s_strFromFbUnit_StrParam,
                comuMsgUnit_ReplyResult.s_lFromFbUnit_lParam1, comuMsgUnit_ReplyResult.s_lFromFbUnit_lParam2)

            strFrom, strDest = self.GetFromDestFullName(comuMsgUnit_ReplyResult)
            CTYLB_Log.ShowLog(0, "执行 回复", "[%s] -> [%s]:%d" % (strFrom, strDest, comuMsgUnit_ReplyResult.s_iRun_MessageID))

            if (strDestClientName):
                if (iDomainType == Collect_FbNameDict_Mang.s_g_iType_LocalPeerNats):
                    # 传递给该client单元
                    self.s_AsyncNATS_ProcComu.AddContentToSend(
                        strDestClientName, Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_Message_Result,
                        strMsgContent)

                elif (iDomainType == Collect_FbNameDict_Mang.s_g_iType_Local_FBotClient):
                    # 增加到队列
                    newPackage = FBotV4.make_package(command_id=Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_Message_Result,
                                                     value=strMsgContent)
                    # 传递给FBot单元
                    toBeSendArray = []
                    if (strDestClientName in self.s_toBeSend_FBotClient_PackageDict.keys()):
                        toBeSendArray = self.s_toBeSend_FBotClient_PackageDict[strDestClientName]
                    else:
                        self.s_toBeSend_FBotClient_PackageDict[strDestClientName] = toBeSendArray
                    toBeSendArray.append(newPackage)

                elif (iDomainType == Collect_FbNameDict_Mang.s_g_iType_Peer_FBot):
                    # 增加到队列
                    newPackage = FBotV4.make_package(command_id=Share_UTRC_CfgDef.g_iPeerFbUTRC_Cmd_NeedPeerFBot_Reply_Message_Result,
                                                     value=strMsgContent)
                    # 传递给FBot单元
                    self.s_toBeSend_PeerFBot_PackageArray.append(newPackage)
                    pass
            else:
                CTYLB_Log.ShowLog(1, "Not Found Dest", "%s -> %s" % (strFrom, strDest))
                pass

        pass

    # 执行 回复 构建所有客户端信息.
    # start by sk. 180503
    def Exec_Reply_BuildAllClientInfo(self, strClientName):
        strInfo=self.s_collect_FbNameDict_Mang.ExportAllToStr()
        self.s_AsyncNATS_ProcComu.AddContentToSend(strClientName, Share_UTRC_CfgDef.g_iFbUTRC_Cmd_Reply_AllClientInfo, strInfo)
        pass


    # 单位时间不断调用
    def v_TimerCheck(self):
        # 更新接收到的客户端单元 纤程 列表
        recvDict = self.s_AsyncNATS_ProcComu.Pop_Recv_ClientFiberDict()
        self.s_collect_FbNameDict_Mang.Handle_Recv_NATSClients_FbNames_Dict(recvDict)

        # 更新执行发送任务
        eachcmdMsgUnit = self.s_AsyncNATS_ProcComu.Pop_Recv_EachClientCmdMsgUnit()
        if(eachcmdMsgUnit):
            self.ExecRunMessage(Collect_FbNameDict_Mang.s_g_iType_LocalPeerNats,
                                eachcmdMsgUnit.ExportToStr())

        # 每段时间给Peer广播，我的 NATs和FBot的 Fiber列表
        self.s_Exec_SendFbList_To_PeerFBot()

        # 每段时间检查接收的 命令消息执行结果 数据包，进行传递处理
        eachCmdReplyMsgResult = self.s_AsyncNATS_ProcComu.Pop_Recv_EachClient_ReplyCmdMsgResultUnit()
        if(eachCmdReplyMsgResult):
            self.Exec_Reply_Message_Result(Collect_FbNameDict_Mang.s_g_iType_LocalPeerNats,
                                           eachCmdReplyMsgResult.ExportToStr())

        # 检查获取客户端列表.
        # add by sk. 180503
        strClient_RequestAllClientInfo=self.s_AsyncNATS_ProcComu.Pop_Recv_Request_AllClientInfo()
        if(strClient_RequestAllClientInfo):
            self.Exec_Reply_BuildAllClientInfo(strClient_RequestAllClientInfo)
            pass

        return False

    # 每段时间给Peer广播，我的 NATs和FBot的 Fiber列表
    # start by sk. 180415
    def s_Exec_SendFbList_To_PeerFBot(self):
        if(self.s_TimerDiff_PeerFBotSrv_FbUnit_Notify.CheckTimeDiff()):
            strSendContent = self.s_collect_FbNameDict_Mang.Construct_Ex_PeerFBotSrv_Content()
            self.s_toBeSend_PeerFBot_FbNames_Package=FBotV4.make_package(
                Share_UTRC_CfgDef.g_iPeerFbUTRC_Cmd_BroadCast_Peer_FbUnitNames, strSendContent)
        pass
