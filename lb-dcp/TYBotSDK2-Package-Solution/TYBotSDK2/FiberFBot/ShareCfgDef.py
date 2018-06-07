# ShareCfgDef.py
# 共享配置定义
# start by sk. 180414

class Share_UTRC_CfgDef:
    # 下面是服务器的地址
    g_strNats_Server_Addr = ""

    g_iFbUTRC_Cmd_Report_FiberUnitArray = 100  # 报告广播纤程单元队列。内容格式为 CUTRC_NATs_ComuFiberList json:
            # {"UID-List", [uid1, uid2, uid3...]}
            # {"TaskNameList", ["strTaskName-strParam", "strTaskName-strParam"]}
            # {"TaskName_LongParam_List", {"strTaskName-longParam", "strTaskName-longParam2"]}

    g_iFbUTRC_Cmd_Run_Message = 130  #  nats方式，作为UTRC认识的命令，运行消息。CUTRC_NATs_Comu_RunMessageUnit
    g_iFbUTRC_Cmd_Reply_Message_Result = 131  # 返回运行消息的结果。CUTRC_NATs_Comu_RunMessageUnit

    g_iFbUTRC_Cmd_Request_AllClientInfo = 132  # 请求所有客户端单元列表。参数：无
    g_iFbUTRC_Cmd_Reply_AllClientInfo = 133  # 回复，所有客户端单元列表。返回参数：dict_运行参数列表


    g_iFbUTRC_ListenPeer_Port= 20  # 纤程TRC服务器的监听端口。

    g_iPeerFbUTRC_Cmd_BroadCast_Peer_FbUnitNames = 101  # 伙伴纤程单元名字 广播
    g_iPeerFbUTRC_Cmd_NeedPeerFBot_Run_Message = 102  # 需要伙伴运行消息。内容格式为：CUTRC_NATs_Comu_RunMessageUnit
    g_iPeerFbUTRC_Cmd_NeedPeerFBot_Reply_Message_Result = 103  # 需要伙伴返回运行结果消息。内容格式为：CUTRC_NATs_Comu_RunMessageUnit

    g_iFbUTRC_AcceptExecClient_ListenPort= 21  # 线程UTRC服务器，对FBot客户端的监听端口
    # 下面用于FBot之间的通信。Msg=g_iFbUTRC_Cmd_Run_Message, param1=下面的值. value为具体内容
    g_iFBot_Cmd_Nop_SendEcho_To_Srv=110  # 不断发送空数据包握手
    g_iFbot_Cmd_TransExecMsg_To_Srv=111  # 传递-需要执行消息的命令
    g_iFBot_Cmd_Report_FbUnitList_To_Srv=112  # 广播FBot单元列表。内容为 CUTRC_NATs_ComuFiberList
    g_iFBot_Cmd_Reply_ExecMsg_To_Srv=113  # 回复执行消息

    g_iFBot_Cmd_NeedExecCmd_To_Client=120  # 需要fbot客户端执行命令


    # 下面相关FBot的配置
    g_str_Section_FBot_UTRC = "FiberFBotUTRC"
    g_str_key_FbUTRC_AcceptExecClient_ListenPort = "FbUTRC_AcceptExecClient_ListenPort"

    # 下面关于NATs进程通信的配置
    g_str_section_FiberUTRC = "FiberUTRC"
    g_str_key_FbUTRC_ListenPort = "FbUTRC_ListenPeer_Port"
    g_str_key_FbUTRC_FBot_PeerServerAddr = "Peer_FbUTRC_FBot_ServersAddr"

    g_str_key_NATs_Addr = "NATS_SERVER_ADDR"
    g_str_key_NAT_Proc_ServerName = "NTS_ProcessComu_ServerName"

    g_str_section_FBot = "client"
    g_str_key_myid = "myid"

    # 下面相关 FBot-Client使用，连接FBot-UTRC服务器的节点
    g_str_key_FBot_UTRC_Server = "FBot_UTRC_Server"
