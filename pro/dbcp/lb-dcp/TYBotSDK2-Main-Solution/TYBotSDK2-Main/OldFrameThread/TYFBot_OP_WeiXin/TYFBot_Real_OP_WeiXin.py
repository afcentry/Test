# -*- coding:UTF-8 -*- 放到第一行标记
# TYFBot_Real_OP_WeiXin.py 天元功能机器人－操作WeiXin的服务端
#
# start by sk. 170407

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_MainConn
from Sk_LB_db_FBot_WeiXin_Real import CSkLBDB_ow_bot_out_logincode, CSkLBDB_ow_bot_out_chatcontent, CSkLBDB_ow_bot_in_sendchatcontent
import time
from datetime import datetime
import random
import os

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = u'TianYuan Function Bot - Operate WeiXin'
g_mainOperateWeiXinDB = CSkLBDB_MainConn()    # 链接微信bot数据库

g_ustr_WeiXinBot_DBName = u'ty2_weixin_msg_trans'
g_i_ListenSock_TYFBot_OP_WeiXin_Operate = 7  # 监听管套，操作微信机器人

g_i_OpWeiXin_SubCmd_GetLoginCode = 701  # 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Reply_GetLoginCode = 702  # 回复 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Get_ChatContent = 703  # 获得聊天的内容
g_i_OpWeiXin_SubCmd_Reply_Get_ChatText = 704  # 回复 获得聊天的内容
g_i_OpWeiXin_SubCmd_Send_ChatContent = 705  # 发送要和别人说的内容
g_i_OpWeiXin_SubCmd_Reply_SendChatContent = 706  # 回复 发送要和别人说的内容

g_ustr_ContentSplit = u'(;1-@;)'   # 内容的分隔符



# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, u'CTRL_C', u"Ctrl+C Input, exiting")
    g_bSysRunning = False

# ################################################################################################
#   下面是子命令处理实现
# ################################################################################################

# 处理操作WeiXin 获得登陆二维码，返回计数值
# 	输入: iValue=701
# 	返回: strValue=微信登录需要扫码的图片的Base64转码。iValue=702, strParam1=URL, strParam2=createTime
# start by sk. 170407
def SubHandle_OPWeiXin_GetLoginCode():
    # 执行，让机器人生成二维码链接，再读取数据库记录内容
    ustrURL, ustrImgData, createTime = CSkLBDB_ow_bot_out_logincode.ReadByRecID( g_mainOperateWeiXinDB.s_DbConn, 1)

    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpWeiXin_SubCmd_Reply_GetLoginCode)
    retCommCTUnit.SetStrData( ustrImgData)
    retCommCTUnit.SetParam( ustrURL, createTime.strftime(u'%Y-%m-%d %H:%M:%S'))
    return retCommCTUnit

# 处理操作WeiXin 获得别人发送的聊天的内容
# 	输入: iValue=703
# 	返回: strValue=别人和我说话的文字内容。iValue=704，strParam1=说话者的ID，strParam2=说话的时间<分割>内容类型-文字-图片<分割>是个人
#           还是群<分割>如果是群，群名是什么
# start by sk. 170407
def SubHandle_OPWeiXin_GetChatContent():
    retCTUnitArray = []
    iFinishStatus = 2

    iNotExecIDArray = CSkLBDB_ow_bot_out_chatcontent.GetRecList_By_StatusNotEquValue( g_mainOperateWeiXinDB.s_DbConn, iFinishStatus)
    if( iNotExecIDArray):
        for iEachRecID in iNotExecIDArray:
            ustrExecContent, iExecTypeS, ustrExecFromS, iExecFromType, ustrExecFromGroupName, iExecExStatus, execCreateTime =\
                CSkLBDB_ow_bot_out_chatcontent.ReadByRecID( g_mainOperateWeiXinDB.s_DbConn, iEachRecID)
            # 格式化输出记录
            eachRetCommCTUnit = CTYBot_CTUnit_CommonData()
            eachRetCommCTUnit.SetIntData( g_i_OpWeiXin_SubCmd_Reply_Get_ChatText)
            eachRetCommCTUnit.SetStrData( ustrExecContent)

            strRecvTime = execCreateTime.strftime(u'%Y-%m-%d %H:%M:%S')
            paramContentArray = [strRecvTime, str(iExecTypeS), str(iExecFromType), ustrExecFromGroupName]
            ustrParam2 = g_ustr_ContentSplit.join(paramContentArray)
            eachRetCommCTUnit.SetParam( ustrExecFromS, ustrParam2)
            retCTUnitArray.append( eachRetCommCTUnit)
            # 记录状态修改
            CSkLBDB_ow_bot_out_chatcontent.Update_ExStatus( g_mainOperateWeiXinDB.s_DbConn, iEachRecID, iFinishStatus)
    else:
        # 如果为空，加入临时空单元
        eachRetCommCTUnit = CTYBot_CTUnit_CommonData()
        retCTUnitArray.append(eachRetCommCTUnit)

    return retCTUnitArray

# 处理操作WeiXin 执行 发送要和别人说的内容
# 	输入: strValue=要发送的内容，iValue=705，strParam1=要发送对象的ID，strParam2=内容类型-文字-图片<分割>是个人，还是群<分割>群名
# 	返回: strValue=无。iValue=706，strParam1=0，发送失败，未登陆；=1，表示发送成功。
# start by sk. 170407
def SubHandle_OPWeiXin_SendChatContent( ustrContent, ustrDestUserName, ustrCombParam):
    ustrTypeS = u'1'
    ustrToStatus = u'0'
    # 分解获得参数
    ustrParamSubArray = ustrCombParam.split( g_ustr_ContentSplit)

    ustrToS, ustrToType, ustrToGroupName, ustrStatusS = u'', u'', u'', u''
    if( len(ustrParamSubArray) >=3):
        ustrToType = ustrParamSubArray[0]
        ustrIsGroup = ustrParamSubArray[1]
        ustrToGroupName = ustrParamSubArray[2]
    CSkLBDB_ow_bot_in_sendchatcontent.AddNewdRec(g_mainOperateWeiXinDB.s_DbConn, ustrContent, ustrTypeS, ustrDestUserName,
                                                 ustrToType, ustrToGroupName, ustrToStatus)
    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpWeiXin_SubCmd_Reply_SendChatContent)
    retCommCTUnit.SetStrData( u'1')
    return retCommCTUnit

# ################################################################################################
#   下面是主命令通信接口 实现
# ################################################################################################


# 接收到 操作WeiXin 管套数据单元的处理
# start by sk. 170407
def HandleRecvCTUnit_OPWeiXin(hlSockMang, iEachAcceptSock, ctUnitArray):
    retDataArray = []
    for eachCTUnit in ctUnitArray:
        eachRetCommCTUnit = None
        eachRetCommCTUnitArray = []
        if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if( eachCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_GetLoginCode):
                eachRetCommCTUnit = SubHandle_OPWeiXin_GetLoginCode( )
            elif( eachCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Get_ChatContent):
                eachRetCommCTUnitArray = SubHandle_OPWeiXin_GetChatContent( )
            elif (eachCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Send_ChatContent):
                eachRetCommCTUnit = SubHandle_OPWeiXin_SendChatContent(eachCTUnit.s_strValue, eachCTUnit.s_strParam1, eachCTUnit.s_strParam2)

        if( eachRetCommCTUnit):
            retDataArray.append(eachRetCommCTUnit)
        if( eachRetCommCTUnitArray):
            retDataArray.extend( eachRetCommCTUnitArray)
    if( not retDataArray):
        retDataArray.append( CTYBot_CTUnit_CommonData())
    hlSockMang.PassiveSend_To_AcceptSock(iEachAcceptSock, retDataArray)
    pass

# ################################################################################################
#   主程序入口 实现
# ################################################################################################
if __name__ == '__main__':
    #获取配置文件路径及文件名，文件夹不存在则创建
    config_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"config")
    config_file= os.path.join(config_dir,u"config.ini")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.isfile(config_file):
        CTYLB_Log.ShowLog(0, u'Main', u'[%s] config file missing...Quit!' % g_strProgName)
        #配置文件不存在，直接退出
        os._exit(-1)

    db_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),u"db")
    db_file= os.path.join(db_dir,u"data.db")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 链接主数据库
    g_mainOperateWeiXinDB.ReConnect(u"172.16.56.130", 3306, u"testzhuangshiqi", u"abc888+222@@@", g_ustr_WeiXinBot_DBName)

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()

    # 获得管套管理对象
    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang
    iOPWeiXin_ListenSock = hlSockMang.CreateListenSock( g_i_ListenSock_TYFBot_OP_WeiXin_Operate)
    iAccept_OPWeiXin_Sock_Array = []
    while(g_bSysRunning):
        bTaskBusy = False
        # 检查新接收的连接
        iNewAcceptSockIndex = hlSockMang.ExAcceptNewListenArriveSock( iOPWeiXin_ListenSock)
        if( iNewAcceptSockIndex):
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSockIndex)
            CTYLB_Log.ShowLog(0, u'op-WeiXin', u'from [%s:%d] new HLConnect %d accept.' % (strPeerName, iPeerPort, iNewAcceptSockIndex))
            bTaskBusy = True
            iAccept_OPWeiXin_Sock_Array.append( iNewAcceptSockIndex)
            pass
        for iEachAcceptSock in iAccept_OPWeiXin_Sock_Array:
            # 检查有否新数据包到达
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachAcceptSock)
            if( not bSockExist):
                # 检查是否管套已经关闭
                CTYLB_Log.ShowLog(0, u'op-WeiXin', u'sock %d closed' % (iEachAcceptSock))
                iAccept_OPWeiXin_Sock_Array.remove( iEachAcceptSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    HandleRecvCTUnit_OPWeiXin( hlSockMang, iEachAcceptSock, ctUnitArray)

        if( not bTaskBusy):
            time.sleep(0.1)

    # 退出线程
    g_LessTYLB_Bot_FrameThread.SafeStop()
    CTYLB_Log.ShowLog(0, u'sys-echo', u'bye bye')

