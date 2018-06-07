# -*- coding:UTF-8 -*- 放到第一行标记
# TYFBot_OPWX_ExWeb.py 操作微信-登陆-外部Web输出 机器人实现
#
# start by sk. 170311

from datetime import datetime
from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
from TYBotSDK2.BotBase.Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_MainConn
import time
import os
from Sk_LB_db_FBot_OPWXExWeb_Real import CSkLBDB_ow_bot_out_logincode

# ################################################################################################
#   下面是节点系统单元实现
# ################################################################################################

# 单位时间的回调功能，如果有内容执行，则返回True，空闲，则返回False
# start by sk. 170222
def TimerCheck_PrepareSendContent():
    bRetValue = False  # 返回值。

    return bRetValue

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = 'TianYuan Function Bot - Operate WX ExConnect Web'
g_mainOperateWXExWebDB = CSkLBDB_MainConn()    # 链接微信bot数据库

g_str_TY2FuncBot_MiscCollect_DBName = 'ty2_funcbot_misc_collect'

g_strOPWeiXinSrvName = 'TYFBot_OP_WeiXin'
g_i_ListenSock_TYFBot_OP_WeiXin_Operate = 7  # 监听管套，操作微信机器人

g_i_OpWeiXin_SubCmd_GetLoginCode = 701  # 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Reply_GetLoginCode = 702  # 回复 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Get_ChatContent = 703  # 获得聊天的内容
g_i_OpWeiXin_SubCmd_Reply_Get_ChatText = 704  # 回复 获得聊天的内容
g_i_OpWeiXin_SubCmd_Send_ChatContent = 705  # 发送要和别人说的内容
g_i_OpWeiXin_SubCmd_Reply_SendChatContent = 706  # 回复 发送要和别人说的内容

# 存储微信登陆的信息
g_strWXLoginURL, g_strWXLoginImageContent, g_strWXLoginCreateTime = '', '', ''


# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, 'CTRL_C', "Ctrl+C Input, exiting")
    g_bSysRunning = False

####################################################################################
#  下面实现参数-数据库功能，和结果数据库功能的测试。
####################################################################################

# 获得要发送给参数管理的数据
def HandleSend_OpWeiXin_Srv():
    retSendUnitArray = []

    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpWeiXin_SubCmd_GetLoginCode)
    retSendUnitArray.append(sendCTUnit)

    return retSendUnitArray

def Handle_Recv_SubCmd_Reply_GetLoginCode(strImgContent, strURL, strTime):
    global g_strWXLoginURL, g_strWXLoginImageContent, g_strWXLoginCreateTime

    if __name__ == '__main__':
        if( (strURL == g_strWXLoginURL) and (strImgContent == g_strWXLoginImageContent) and (strTime == g_strWXLoginCreateTime) ):
            pass
        else:
            g_strWXLoginURL = strURL
            g_strWXLoginImageContent = strImgContent
            g_strWXLoginCreateTime = strTime

            try:
                execTime = datetime.strptime( strTime, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                execTime = datetime.now()
            # update db
            CSkLBDB_ow_bot_out_logincode.UpdateRecordContent( g_mainOperateWXExWebDB.s_DbConn, 1, strURL, strImgContent, execTime)
            CTYLB_Log.ShowLog(0, 'Update-Login_Content-Image', "New URL:[%s] time:[%s]" % (strURL, strTime))
    pass

# 处理接收到的weixin_caozuo
def HandleRecv_OPWeiXin_CTUnit( recvCTUnit):
    if (recvCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_GetLoginCode):
            # CTYLB_Log.ShowLog(0, 'recv-wx-data', 'recv login-code-reply:[] param: [%s] : [%s]' % (recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
            Handle_Recv_SubCmd_Reply_GetLoginCode( recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2)
        elif (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_Get_ChatText):
            CTYLB_Log.ShowLog(0, 'recv-wx-data', 'recv reply-chat result:[%s] param: [%s] : [%s]'
                              % (recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
        elif (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_SendChatContent):
            CTYLB_Log.ShowLog(0, 'recv-wx', 'recv sendtext-reply:[%s] param: [%s] : [%s]'
                              % (recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
    pass

# 主程序入口
if __name__ == '__main__':
    #获取配置文件路径及文件名，文件夹不存在则创建
    config_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),"config")
    config_file= os.path.join(config_dir,"config.ini")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.isfile(config_file):
        CTYLB_Log.ShowLog(0, 'Main', '[%s] config file missing...Quit!' % g_strProgName)
        #配置文件不存在，直接退出
        os._exit(-1)

    db_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),"db")
    db_file= os.path.join(db_dir,"data.db")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 链接主数据库
    g_mainOperateWXExWebDB.ReConnectTo_56_130_local_vm( g_str_TY2FuncBot_MiscCollect_DBName)

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()
    g_strSelfID = g_LessTYLB_Bot_FrameThread.GetMyName()

    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang

    # 测试 weixin-op
    # 获得管套管理对象, 操作结果，操作参数块
    connect_weixin_op_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_strOPWeiXinSrvName, g_i_ListenSock_TYFBot_OP_WeiXin_Operate)
    CTYLB_Log.ShowLog(0, 'exec', 'start HLSock connect remote [%s:%d] op-weixin Func' % (g_strOPWeiXinSrvName, g_i_ListenSock_TYFBot_OP_WeiXin_Operate))

    while(g_bSysRunning):
        bTaskBusy = False
        if( connect_weixin_op_Sock.ExecNextCheck()):
            bTaskBusy = True

        if( connect_weixin_op_Sock.CanExecSendData()):
            execSendCTArray = HandleSend_OpWeiXin_Srv()
            connect_weixin_op_Sock.ExecSendData( execSendCTArray)
            bTaskBusy = True

        recvCTArray = connect_weixin_op_Sock.PopRetriveRecvCTArray()
        recvCTArray = []
        if( recvCTArray):
            bTaskBusy = True
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connect_weixin_op_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                CTYLB_Log.ShowLog(0, 'recv-WeiXin-reply', 'from [%s:%d] recv len:[%d]' % ( strPeerName, iPeerPort, len(eachUnit.s_strValue)))
                HandleRecv_OPWeiXin_CTUnit( eachUnit)

        if( not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    g_LessTYLB_Bot_FrameThread.SafeStop()

    CTYLB_Log.ShowLog(0, 'Main', 'bye bye')

