# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Base_Def.py 机器人的基本定义
#
#  机器人ID命名规则：s_g_iDataType_ 和 s_g_strBotName_ 是数据类型，和机器人名字的前缀，固定
#    名字: 前缀固定_名字描述_书写者代号_版本。
#        例如: s_g_iDataType_TaskRegCenter_sk_v1 表示 sk书写的，第1版本，TaskRegCenter，任务注册中心
#     变量为：tbot_功能名字_sk_V1
#
# start by sk. 170212

class CTYLB_Bot_BaseDef:
    s_g_iDataType_Small_For_Reserved=100  # 比此值小的数据类型值保留

    # 下面100-1000，为分布运算的命令ID分配。包括插件单元，和运算单元
    s_g_iDataType_CommonTask = 100  # 通用任务变量

    s_g_iMainCmd_CommonTask_SingleData = 0    # 主命令，通用任务－数据分配－参数，可设置传递参数类型
    s_g_iSubCmd_CommonTask_SingleData = 0  # 子命令，无
    s_g_iSubCmd_CommonTask_User = 100 # 100以上命令由用户定义

    # 下面是公用的机器人名字
    s_g_strBotName_Echo_sk_v1 = u'tbot_echo'   # Echo的机器人名字

    # 下面100-1000，为分布运算的命令ID分配。包括插件单元，和运算单元
    s_g_iDataType_TaskRegCenter_sk_v1 = 101  # 任务登记中心数据类型
    s_g_strBotName_TaskRegCenter_sk_v1 = u'TaskRegCenter'   # 任务管理中心的机器人名字

    s_g_iMainCmd_TaskRegCenter_ReportMyStatus = 0    # 主命令，登记我状态，现在跑了多少了。数据包格式为：CTYBot_CTUnit_TaskRegCenter_ReportMyStatus
    s_g_iSubCmd_TaskRegCenter_ReportMyStatus_None = 0  # 子命令，登记状态。  命令包含：支持运算ID，能够接收的命令数，当前正在运算的数量

    s_g_iMainCmd_TaskRegCenter_AssignTask = 1    # 主命令，分配任务
    s_g_iSubCmd_TaskRegCenter_AssignTask_Param = 0    # 子命令，分配任务的名字队列参数
    s_g_iSubCmd_TaskRegCenter_AssignTask_BroadCast_Param = 1    # 子命令，分配广播参数

    s_g_iMainCmd_TaskRegCenter_ReportResult = 2    # 主命令，报告运行结果
    s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl = 0    # 子命令，Ping结果, 路由结果, Web爬虫结果

    s_g_iMainCmd_TaskRegCenter_Request_ReportMangStatus = 3    # 主命令，请求报告管理端状态
    s_g_iSubCmd_TaskRegCenter_Request_ReportMangStatus = 0    # 子命令，请求报告管理状态

    s_g_iMainCmd_TaskRegCenter_Reply_ReportMangStatus = 4    # 主命令，回复报告管理端状态
    s_g_iSubCmd_TaskRegCenter_Reply_ReportMangStatus = 0    # 子命令，回复报告管理状态

    s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock = 5    # 主命令，分配任务-Web名字列表块
    s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock = 0    # 子命令，分配任务-Web名字列表块

    s_g_iMainCmd_TaskRegCenter_Reply_WebName_Result_StrBlock = 6    # 主命令，回复Web名字的字符串结果
    s_g_iSubCmd_TaskRegCenter_Reply_WebName_Result_StrBlock = 0    # 子命令，

    s_g_iMainCmd_TaskRegCenter_ReportResult_V2 = 7    # 主命令，报告运行结果 V2
    s_g_iSubCmd_TaskRegCenter_ReportResult_V2_PingTraceWebCrawl = 0    # 子命令，Ping结果, 路由结果, Web爬虫结果

    '''
    s_g_iDataType_DScan_WebCraw_sk_v1 = 102    # 网页爬取插件
    s_g_strBotName_DScan_WebCraw_sk_v1 = 'tbot_DScan_WebCraw_sk_v1'   # 机器人名字
    s_g_iDataType_DScan_TraceRoute_sk_v1 = 103    # 路由跟踪
    s_g_strBotName_DScan_TraceRoute_sk_v1 = 'tbot_DScan_WebCraw_sk_v1'   # 机器人名字
    s_g_iDataType_DScan_Ping_Domain_sk_v1 = 104    # 域名ping
    s_g_strBotName_DScan_Ping_Domain_sk_v1 = 'tbot_DScan_WebCraw_sk_v1'   # 机器人名字
    '''

    s_g_iDataType_HLSockSession = 105  # 高层管套会话
    s_g_iMainCmd_HLSockSession = 0    # 主命令，管套会话数据
    s_g_iSubCmd_HLSockSession = 0    # 子命令，管套会话数据

    # 下面是聊天内容。
    s_g_iDataType_simp_chat = 102  # 简单的聊天内容
    s_g_iMainCmd_SimpChat_SendText = 1    # 主命令，发送文字信息
    s_g_iSubCmd_SimpChat_SendText = 0    # 子命令，发送文字信息

    s_g_iSockEchoListenPort = 2  # Echo端口
    s_g_iTaskMang_Listen_Port_PromptTask = 3   # 任务管理中心，对任务提交者的监听端口
    s_g_iTaskMang_Listen_Port_PluginStatusResult = 4   # 任务管理中心，插件报告状态，和传回结果。收到后，发送参数块过去

    s_g_iDataType_SimuSystemNotify = 106  # 模拟系统通知
    s_g_iMainCmd_SimuSystemNotify = 0    # 主命令，暂时未用
    s_g_iSubCmd_SimuSystemNotify = 0    # 子命令，暂时未用


    pass
