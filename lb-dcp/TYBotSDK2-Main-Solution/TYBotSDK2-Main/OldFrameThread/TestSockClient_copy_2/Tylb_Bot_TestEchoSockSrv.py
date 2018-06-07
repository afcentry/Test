# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_TestEchoSockSrv.py 测试 echo－srv.
#
# start by sk. 170307

from datetime import datetime
from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
from TYBotSDK2.BotBase.Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
import time
import random
import os

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
g_iEchoSockSrvPort = 2
g_strEchoSockSrvName = 'tbot_echo_3'
g_strSelfID = ''
g_strProgName = 'TYBot_Test_Some_Sock_Server'
g_strOPDBSrvName = 'TYFBot_OP_DB'

g_i_ListenSock_TYFBot_OP_DB_Operate_ParamBlock = 5  # 监听管套，操作数据库机器人，操作参数块
g_i_ListenSock_TYFBot_OP_DB_Operate_Result = 6      # 监听管套，操作数据库机器人，操作结果

g_strRecvParamIDArray = []   # 接收到的参数块id队列


g_strOPWeiXinSrvName = 'TYFBot_OP_WeiXin'
g_i_ListenSock_TYFBot_OP_WeiXin_Operate = 7  # 监听管套，操作微信机器人

g_i_OpWeiXin_SubCmd_GetLoginCode = 701  # 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Reply_GetLoginCode = 702  # 回复 获得登录二维码图片
g_i_OpWeiXin_SubCmd_Get_ChatContent = 703  # 获得聊天的内容
g_i_OpWeiXin_SubCmd_Reply_Get_ChatText = 704  # 回复 获得聊天的内容
g_i_OpWeiXin_SubCmd_Send_ChatContent = 705  # 发送要和别人说的内容
g_i_OpWeiXin_SubCmd_Reply_SendChatContent = 706  # 回复 发送要和别人说的内容


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
    sendCTUnit.SetIntData(g_i_OpWeiXin_SubCmd_Get_ChatContent)
    retSendUnitArray.append(sendCTUnit)

    return retSendUnitArray

# 处理接收到的weixin_caozuo
def HandleRecv_OPWeiXin_CTUnit( recvCTUnit):
    if (recvCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_GetLoginCode):
            CTYLB_Log.ShowLog(0, 'recv-wx-data', 'recv login-code-reply:[] param: [%s] : [%s]' % (recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
        elif (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_Get_ChatText):
            CTYLB_Log.ShowLog(0, 'recv-wx-data', 'recv reply-chat result:[%s] param: [%s] : [%s]'
                              % (recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
        elif (recvCTUnit.s_iValue == g_i_OpWeiXin_SubCmd_Reply_SendChatContent):
            CTYLB_Log.ShowLog(0, 'recv-wx', 'recv sendtext-reply:[%s] param: [%s] : [%s]'
                              % (recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
    pass

'''
####################################################################################
#  下面实现参数-数据库功能，和结果数据库功能的测试。
####################################################################################

g_i_OpParamBlock_SubCmd_RegiestDbTableField_Param = 501  # 注册数据库表字段参数
g_i_OpParamBlock_SubCmd_Reply_RegiestDbTableField_Param = 502  # 注册数据库表字段参数-返回
g_i_OpParamBlock_SubCmd_GetUnExecRecCount = 503  # 获得未处理的个数
g_i_OpParamBlock_SubCmd_Reply_GetUnExecRecCount = 504  # 获得未处理的个数-返回
g_i_OpParamBlock_SubCmd_GetRunParamBlock = 505  # 获得可运行的参数块
g_i_OpParamBlock_SubCmd_Reply_GetRunParamBlock = 506  # 获得可运行的参数块-返回
g_i_OpParamBlock_SubCmd_Finish_ParamBlock = 507  # finish参数块

g_i_OpResult_SubCmd_AddResult = 601  # 增加结果
g_i_OpResult_SubCmd_ReplyAddResult = 602  # 增加结果 返回

# 获得要发送给参数管理的数据
def HandleSend_ParamData_To_OPDBSrv():
    retSendUnitArray = []

    # 发送注册数据库信息
    strTaskAppName = 'Get_EnterPrise_DomainName'
    strSubTaskName = datetime.now().strftime('%Y_%m_%D#%H_%M_%S')
    strDBName = 'ty2_zhl_enterprises'
    strTableName = 'ty2_enterprises'
    strFieldName = 'name'
    strParamSignIDField = 'id'
    iLastExecID = 0

    strCombArray = [strTaskAppName, strDBName, strTableName, strFieldName, strParamSignIDField, str(iLastExecID)]
    strFixValue = ';'.join(strCombArray)
    sendCTUnit = CTYBot_CTUnit_CommonData()
    sendCTUnit.SetIntData(g_i_OpParamBlock_SubCmd_RegiestDbTableField_Param)
    sendCTUnit.SetStrData(strFixValue)

    retSendUnitArray.append(sendCTUnit)

    # 发送获得未执行的记录个数请求
    sendCTUnit2 = CTYBot_CTUnit_CommonData()
    sendCTUnit2.SetIntData(g_i_OpParamBlock_SubCmd_GetUnExecRecCount)
    sendCTUnit2.SetParam(strTaskAppName, '')
    retSendUnitArray.append(sendCTUnit2)

    # 发送获得参数的请求
    sendCTUnit3 = CTYBot_CTUnit_CommonData()
    sendCTUnit3.SetIntData(g_i_OpParamBlock_SubCmd_GetRunParamBlock)
    sendCTUnit3.SetStrData('5')
    sendCTUnit3.SetParam(strTaskAppName, '3')
    retSendUnitArray.append(sendCTUnit3)

    # 发送之前参数块完成的命令
    global g_strRecvParamIDArray
    if( g_strRecvParamIDArray > 0):
        for eachParamID in g_strRecvParamIDArray:
            sendCTUnit4 = CTYBot_CTUnit_CommonData()
            sendCTUnit4.SetIntData(g_i_OpParamBlock_SubCmd_Finish_ParamBlock)
            sendCTUnit4.SetStrData(eachParamID)
            sendCTUnit4.SetParam(strTaskAppName, '2')
            retSendUnitArray.append(sendCTUnit4)
        g_strRecvParamIDArray = []

    return retSendUnitArray

# 获得要发送给结果的数据
def HandleSend_Result_To_OPDBSrv():
    retSendUnitArray = []

    strTaskAppName = 'Get_EnterPrise_DomainName'
    strSubTaskName = datetime.now().strftime('%Y_%m_%D#%H_%M_%S')
    strParamSign = 'param-sign-testzhuangshiqi-111'

    iResultCount = random.randint(10, 100)
    for iIndex in range(iResultCount):
        strResult = u'获得某某1aaa公司-企业名字信息asdf.com-- %s %d ' % (strSubTaskName, iIndex)
        strOrigTitleDomain = u'企业某某1aaa公司--%s %d' % (strSubTaskName, iIndex)

        contentArray = [strTaskAppName, strSubTaskName, strParamSign]
        strParam2Content = ';'.join(contentArray)

        sendCTUnit = CTYBot_CTUnit_CommonData()
        sendCTUnit.SetIntData(g_i_OpResult_SubCmd_AddResult)
        sendCTUnit.SetStrData(strResult)
        sendCTUnit.SetParam(strOrigTitleDomain, strParam2Content)
        retSendUnitArray.append(sendCTUnit)

    return retSendUnitArray


# 处理接收到的参数结果数据
def HandleRecv_ParamData_CTUnit( recvCTUnit):
    if (recvCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
        if (recvCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Reply_RegiestDbTableField_Param):
            CTYLB_Log.ShowLog(0, 'recv-param-data', 'recv register result:[%s] param: [%s] : [%s]' % (recvCTUnit.s_strValue,
                              recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
        elif (recvCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Reply_GetUnExecRecCount):
            CTYLB_Log.ShowLog(0, 'recv-param-data',
                              'recv reply-count result:[%s] param: [%s] : [%s]'
                              % (recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
        elif (recvCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Reply_GetRunParamBlock):
            CTYLB_Log.ShowLog(0, 'recv-get-param-block-data', 'recv register result:[%s] param: [%s] : [%s]'
                              % (recvCTUnit.s_strValue, recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
            g_strRecvParamIDArray.append( recvCTUnit.s_strParam2)

    pass

# 处理接收到的结果数据
def HandleRecv_Result_CTUnit( recvCTUnit):
    CTYLB_Log.ShowLog(0, 'recv-result-reply',
                      'recv op-db result:[%d][%s] param: [%s] : [%s]' % (recvCTUnit.s_iValue, recvCTUnit.s_strValue,
                                                                        recvCTUnit.s_strParam1, recvCTUnit.s_strParam2))
'''


# 处理 发送数据到echo服务端
# start by sk. 170307
def HandleSendDataToEchoSrv():
    curExecTime = datetime.now()
    newCTUnit = CTYBot_CTUnit_CommonData()

    strLarge = 'xxsseefa'
    iLargeRandCount = random.randint( 250,1800)
    for iSub in range(iLargeRandCount):
        strLarge += 'xx11223344xqwe333dd3xx11223344xqwe3333xx11223344xqwe3333xx11223344xqwe3333xx11223344xqwe3333xx11223344xqwe3333'
    strContent = '1 hello %s, huge:%d, mid-huge-size:%d,' % (curExecTime.strftime('%H:%M:%S'), iLargeRandCount, len(strLarge))
    strContent += strLarge
    newCTUnit.SetStrData(strContent)
    CTYLB_Log.ShowLog(0, 'send', "send huge count:%d total size:%d" % (iLargeRandCount, len(strContent)))

    newCTUnit1 = CTYBot_CTUnit_CommonData()
    strContent = '2 hello %s, I am %s' % (curExecTime.strftime('%H:%M:%S'), g_strSelfID)
    newCTUnit1.SetStrData(strContent)

    newCTUnit2 = CTYBot_CTUnit_CommonData()
    strContent = '3 hello %s, I am %s' % (curExecTime.strftime('%H:%M:%S'), g_strSelfID)
    newCTUnit2.SetStrData(strContent)

    retCTArray = [newCTUnit, newCTUnit1, newCTUnit2]
    return retCTArray

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

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()
    g_strSelfID = g_LessTYLB_Bot_FrameThread.GetMyName()

    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang

    '''
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
    '''

    '''
    # 测试 db-op
    # 获得管套管理对象, 操作结果，操作参数块
    connect_OPDB_Param_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_strOPDBSrvName, g_i_ListenSock_TYFBot_OP_DB_Operate_ParamBlock)
    connect_OPDB_Result_Sock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_strOPDBSrvName, g_i_ListenSock_TYFBot_OP_DB_Operate_Result)
    CTYLB_Log.ShowLog(0, 'exec', 'start HLSock %d,%d connect remote [%s] Result & Param Func' % (connect_OPDB_Param_Sock.s_iExecConnectSockIndex, connect_OPDB_Result_Sock.s_iExecConnectSockIndex, g_strOPDBSrvName))

    while(g_bSysRunning):
        bTaskBusy = False
        if( connect_OPDB_Param_Sock.ExecNextCheck() and connect_OPDB_Result_Sock.ExecNextCheck()):
            bTaskBusy = True

        if( connect_OPDB_Param_Sock.CanExecSendData()):
            execSendCTArray = HandleSend_ParamData_To_OPDBSrv()
            connect_OPDB_Param_Sock.ExecSendData( execSendCTArray)
            bTaskBusy = True
        if( connect_OPDB_Result_Sock.CanExecSendData()):
            # execSendCTArray = HandleSend_Result_To_OPDBSrv()
            # connect_OPDB_Result_Sock.ExecSendData( execSendCTArray)
            bTaskBusy = True

        recvCTArray = connect_OPDB_Param_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connect_OPDB_Param_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                CTYLB_Log.ShowLog(0, 'recv-ParamBlock-reply', 'from [%s:%d] recv len:[%d]' % ( strPeerName, iPeerPort, len(eachUnit.s_strValue)))
                HandleRecv_ParamData_CTUnit( eachUnit)

        recvCTArray = connect_OPDB_Result_Sock.PopRetriveRecvCTArray()
        if( recvCTArray):
            bTaskBusy = True
            strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(connect_OPDB_Param_Sock.s_iExecConnectSockIndex)
            for eachUnit in recvCTArray:
                CTYLB_Log.ShowLog(0, 'recv-Result-reply', 'from [%s:%d] recv len:[%d]' % ( strPeerName, iPeerPort, len(eachUnit.s_strValue)))
                HandleRecv_Result_CTUnit( eachUnit)


        if( not bTaskBusy):
            time.sleep(0.1)
    '''

    # 获得管套管理对象
    connectEchoSockArray = []
    iMaxCount = 1  # random.randint(2,6)
    for i in range(iMaxCount):
        connectEchoSock = CTYFBot_OpSession_ConnectSock( hlSockMang, g_strEchoSockSrvName, g_iEchoSockSrvPort, 3, 1200)
        connectEchoSockArray.append(connectEchoSock)
    CTYLB_Log.ShowLog(0, 'exec', 'start %d HLSock connect remote' % (iMaxCount))

    while(g_bSysRunning):
        bTaskBusy = False
        for eachConnSock in connectEchoSockArray:
            if( eachConnSock.ExecNextCheck()):
                bTaskBusy = True
            if( eachConnSock.CanExecSendData()):
                execSendCTArray = HandleSendDataToEchoSrv()
                eachConnSock.ExecSendData( execSendCTArray)
                bTaskBusy = True
            recvCTArray = eachConnSock.PopRetriveRecvCTArray()
            if( recvCTArray):
                bTaskBusy = True
                strPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(eachConnSock.s_iExecConnectSockIndex)
                for eachUnit in recvCTArray:
                    CTYLB_Log.ShowLog(0, 'recv-reply', 'from [%s:%d] recv [%s]' % ( strPeerName, iPeerPort, eachUnit.s_strValue))

        if( not bTaskBusy):
            time.sleep(0.01)

    for eachConnSock in connectEchoSockArray:
        eachConnSock.Close()

    # 退出线程
    g_LessTYLB_Bot_FrameThread.SafeStop()

    CTYLB_Log.ShowLog(0, 'Main', 'bye bye')

