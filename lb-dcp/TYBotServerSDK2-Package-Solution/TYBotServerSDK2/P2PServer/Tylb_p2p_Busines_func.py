# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_p2p_Busines_func.py p2p功能业务定义的共享文件
#
# start by sk. 170125



# C_TYLB_P2P_ShakeHand_Client_Server 握手定义
class CT2P_SHand_Ct_Srv:
    s_iMnCmd_CtSv_0_Pass = 0     # 客户端和服务端之间主动连接，和监听等待接受连接，为了触发让对方发送，而操作的一个等待命令

    # 客户端和服务端的握手
    s_iMnCmd_Ct_Sv_1_ReportName = 1   # 客户端向服务端发，报告客户端名字
    s_iSubCmd_Ct_Sv_1_None = 0     # 子命令，客户端向服务端发 －－－
    s_iMnCmd_Sv_Ct_2_ReplySrvName = 2   # 服务端向客户端发，回应服务端名字
    s_iSubCmd_Sv_Ct_2_None = 0  # 子命令，服务端向客户端发 －－－

    # 客户端和服务端的正常数据传输, listen-accept 和 connect
    s_iMnCmd_Sv_Ct_3_Accept_TimerCheck = 3   # accept的服务端，向客户端发送web会话，让客户端回复数据，或者交互
    s_iSubCmd_Sv_Ct_3_None = 0  # 子命令，服务端向客户端发 －－－
    s_iMnCmd_Ct_Sv_4_Reply_TimerCheck = 4   # 客户端向服务端回复，时间检查
    s_iSubCmd_Ct_Sv_4_None = 0  # 子命令，客户端向服务端回复 －－－

    # 客户端和服务端的正常数据传输, connect 和 listen-accept
    s_iMnCmd_Ct_Sv_5_Connect_SendCheck = 5  # 客户端连接服务端，发送检查数据包
    s_iSubCmd_Ct_Sv_5_None = 0  # 子命令，客户端向服务端回复 －－－
    s_iMnCmd_Sv_Ct_6_Reply_SendCheck = 6   # 服务端向客户端回应，附带参数等内容
    s_iSubCmd_Sv_Ct_6_None = 0  # 子命令，服务端向客户端发 －－－

    # 服务端和客户端的正常数据传输, 服务端connect 和 客户端listen-accept
    s_iMnCmd_Sv_Ct_7_Connect_SendCheck = 7  # 服务端连接客户端，发送检查数据包
    s_iSubCmd_Sv_Ct_7_None = 0  # 子命令，服务端向客户端发 －－－
    s_iMnCmd_Ct_Sv_12_Reply_SendCheck = 12  # srv链接connect后，客户端向服务端回复检查，发送检查数据包
    s_iSubCmd_Ct_Sv_12_None = 0  # 子命令， 客户端向服务端 －－－

    # 服务端和服务端的正常数据传输, connect 和 listen-accept
    s_iMnCmd_Sv_Sv_8_Connect_SendCheck = 8   # 服务端连服务端，主动发送检查包。post
    s_iSubCmd_Sv_Sv_8_None = 0  # 子命令，服务端向服务端发 －－－
    s_iMnCmd_Sv_Sv_9_Reply_SendCheck = 8   # 服务端连服务端，回应发送检查包。http
    s_iSubCmd_Sv_Sv_9_None = 0  # 子命令，服务端向服务端发 －－－

    # 服务端和服务端的握手
    s_iMnCmd_Sv_Sv_10_Connect_ReportName = 10  # 服务端连服务端，报告名字
    s_iSubCmd_Sv_Sv_10_None = 0    # 子命令，服务端向服务端发
    s_iMnCmd_Sv_Sv_11_ReplyReportName = 11  # 服务端连服务端，回应名字
    s_iSubCmd_Sv_Sv_11_None = 0    # 子命令，服务端向服务端发

    pass
