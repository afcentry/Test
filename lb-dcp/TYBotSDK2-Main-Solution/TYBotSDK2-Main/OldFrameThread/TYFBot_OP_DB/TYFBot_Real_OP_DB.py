# -*- coding:UTF-8 -*- 放到第一行标记
# TYFBot_Real_OP_DB.py 天元功能机器人－操作数据库的服务端
#
# start by sk. 170403
# fix bug, main FBot Loop inc effiency. sk. 170601.

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from exec_comb_db_func import CTYF_OpDB_OperateParamBlock, CTYF_OpDB_OperateResult
from Sk_LB_db_main_share_cp import CSkLBDB_MainConn
import time
import random
import os

# 全局系统运行标识
g_bSysRunning = True
g_strProgName = u'TianYuan Function Bot - Operate Database'
g_mainOperateDB = CSkLBDB_MainConn()

g_i_ListenSock_TYFBot_OP_DB_Operate_ParamBlock = 5  # 监听管套，操作数据库机器人，操作参数块
g_i_ListenSock_TYFBot_OP_DB_Operate_Result = 6      # 监听管套，操作数据库机器人，操作结果

g_i_OpParamBlock_SubCmd_RegiestDbTableField_Param = 501  # 注册数据库表字段参数
g_i_OpParamBlock_SubCmd_Reply_RegiestDbTableField_Param = 502  # 注册数据库表字段参数-返回
g_i_OpParamBlock_SubCmd_GetUnExecRecCount = 503  # 获得未处理的个数
g_i_OpParamBlock_SubCmd_Reply_GetUnExecRecCount = 504  # 获得未处理的个数-返回
g_i_OpParamBlock_SubCmd_GetRunParamBlock = 505  # 获得可运行的参数块
g_i_OpParamBlock_SubCmd_Reply_GetRunParamBlock = 506  # 获得可运行的参数块-返回
g_i_OpParamBlock_SubCmd_Finish_ParamBlock = 507  # finish参数块

g_i_OpResult_SubCmd_AddResult = 601  # 增加结果
g_bstr_ResultContentSplit = b'(;1-@;)'   # 结果内容的分隔符
g_i_OpResult_SubCmd_ReplyAddResult = 602  # 增加结果 返回

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, 'CTRL_C', "Ctrl+C Input, exiting")
    g_bSysRunning = False

# ################################################################################################
#   下面是子命令处理实现
# ################################################################################################

# 处理参数块注册数据库名字，返回单元值
# 	Get-db-operate-name: 申请，数据库操作名字，
#     	输入 objname, dbname，tablename，need_field_name，sign_id_field_name，last_ex_id,
#     	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 501，strValue = 输入内容，以;分隔
#     	返回: int_operate_db_id。iValue=502，strValue=字符串值
# start by sk. 170403
def SubHandle_OPParam_Regiest( bstrInputTotalParam):
    iRetRecID = 0
    bstrObjName = b''

    bstrParamArray = bstrInputTotalParam.split(b';')
    if( len(bstrParamArray) >= 6):
        bstrObjName = bstrParamArray[0]
        bstrDbName = bstrParamArray[1]
        bstrTableName = bstrParamArray[2]
        bstrFieldName = bstrParamArray[3]
        bstrSignIDFieldName = bstrParamArray[4]
        try:
            iLastExecID = int(bstrParamArray[5])
        except Exception as e:
            iLastExecID = 0
        iRetRecID = CTYF_OpDB_OperateParamBlock.RequestDbOperate( g_mainOperateDB.s_DbConn, bstrObjName, bstrDbName,
                                                                  bstrTableName, bstrFieldName, bstrSignIDFieldName, iLastExecID)
    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpParamBlock_SubCmd_Reply_RegiestDbTableField_Param)
    retCommCTUnit.SetStrData( str(iRetRecID))
    retCommCTUnit.SetParam(bstrObjName, b'')
    return retCommCTUnit

# 处理参数块 获得未处理的记录个数，返回计数值
# 	Get_unhandle_rec_count: 获得未处理的记录个数。
#     	输入：objname，
#     	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 503，strParam1= objname
#     	返回: iValue=504, strValue =未处理个数，strParam2=总记录个数, strParam1= objname
# start by sk. 170403
def SubHandle_OPParam_GetUnHandleRecCount( bstrObjName):
    iExecNotExecedRecCount, iExecTotalRecCount = CTYF_OpDB_OperateParamBlock.GetUnHandleRecID( g_mainOperateDB.s_DbConn, bstrObjName)
    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpParamBlock_SubCmd_Reply_GetUnExecRecCount)

    retCommCTUnit.SetStrData( str(iExecNotExecedRecCount))
    retCommCTUnit.SetParam(bstrObjName, str(iExecTotalRecCount))
    return retCommCTUnit

# 处理参数块 获得可运行的参数块，返回内容
# 	Get_next_param_block: 获得下部分参数块
#     	输入: objname, need_param_coun, eachCount。
#     	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 505，strParam1= objname，strValue =need_param_count, strParam2 = eachCount
#     	返回：多个参数块单元，每个单元为：CTYBot_CTUnit_CommonData，iValue = 506，strParam1= objname，strValue =paramValueArray: 以’\n’分割, strParam2=paramBlockID
# start by sk. 170403
def SubHandle_OPParam_GetNextParamBlock( bstrObjName, bstrNeedCount, bstrEachBlockCount):
    iNeedExCount = int(bstrNeedCount)
    iEachBlockCount = int(bstrEachBlockCount)
    retCommCTUnitArray = []

    for i in range(iNeedExCount):
        strExecParamSignID, execParamContentArray = CTYF_OpDB_OperateParamBlock.RequestParamBlockContent( g_mainOperateDB.s_DbConn,
                                                                                                          bstrObjName, iEachBlockCount)
        bstrExecParamSignID = strExecParamSignID.encode()
        bstrParamContentArray = CTYLB_MainSys_MiscFunc.SafeGetUTF8Array(execParamContentArray)
        if( strExecParamSignID and bstrParamContentArray):
            eachRetCTUnit = CTYBot_CTUnit_CommonData()
            eachRetCTUnit.SetIntData(g_i_OpParamBlock_SubCmd_Reply_GetRunParamBlock)
            bstrExTotalContent = b'\n'.join(bstrParamContentArray)
            eachRetCTUnit.SetStrData(bstrExTotalContent)
            eachRetCTUnit.SetParam( bstrObjName, bstrExecParamSignID)
            retCommCTUnitArray.append(eachRetCTUnit)
        else:
            # 数据库没有内容了
            break

    return retCommCTUnitArray

# 	finish_param_block: 参数块完成
# 	输入: objname, param_id。
# 	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 507，strParam1= objname，strValue =param_id, strParam2 = finish_status
# 	返回：无
# start by sk. 170403
def SubHandle_OPParam_FinishParamBlock(bstrObjName, bstrBlockParam, bstrExecStatus):
    try:
        iNewStatus = int(bstrExecStatus)
        CTYF_OpDB_OperateParamBlock.SetParamBlockStatus(g_mainOperateDB.s_DbConn, bstrObjName, bstrBlockParam, iNewStatus)
    except Exception as e:
        pass

#  	Add_result。
#     	输入 app_name, sub_task_name, param_id, request_title, result，
#     	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 601，strValue = result。 strParam1=request_Title。 strParam2= app_name, sub_task_name, param_id，以;分隔
#     	返回: strValue=保存结果个数。iValue=602
# start by sk. 170403
def SubHandle_OPResult_AddResult( bstrResultContent, bstrOrigReqTitle, bstrAppNameTaskNameParam):
    bstrAppTaskNameArray = bstrAppNameTaskNameParam.split(g_bstr_ResultContentSplit)
    if( len(bstrAppTaskNameArray) >= 3):
        bstrExecAppName = bstrAppTaskNameArray[0]
        bstrExecTaskName = bstrAppTaskNameArray[1]
        bstrExecParamSignID = bstrAppTaskNameArray[2]

        CTYF_OpDB_OperateResult.AddRecord( g_mainOperateDB.s_DbConn, bstrExecAppName, bstrExecTaskName, bstrExecParamSignID,
                                           bstrOrigReqTitle, bstrResultContent)
    pass


# ################################################################################################
#   下面是主命令通信接口 实现
# ################################################################################################


# 接收到 操作参数块 管套数据单元的处理
# start by sk. 170403
def HandleRecvCTUnit_OPParamBlock(hlSockMang, iEachAcceptSock, ctUnitArray):
    retDataArray = []
    for eachCTUnit in ctUnitArray:
        eachRetCommCTUnit = None
        eachRetCommCTUnitArray = []
        if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if( eachCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_RegiestDbTableField_Param):
                eachRetCommCTUnit = SubHandle_OPParam_Regiest( eachCTUnit.s_strValue)
            elif( eachCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_GetUnExecRecCount):
                eachRetCommCTUnit = SubHandle_OPParam_GetUnHandleRecCount( eachCTUnit.s_strParam1)
            elif (eachCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_GetRunParamBlock):
                eachRetCommCTUnitArray = SubHandle_OPParam_GetNextParamBlock(eachCTUnit.s_strParam1, eachCTUnit.s_strValue, eachCTUnit.s_strParam2)
            elif(eachCTUnit.s_iValue == g_i_OpParamBlock_SubCmd_Finish_ParamBlock):
                SubHandle_OPParam_FinishParamBlock(eachCTUnit.s_strParam1, eachCTUnit.s_strValue, eachCTUnit.s_strParam2)

        if( eachRetCommCTUnit):
            retDataArray.append(eachRetCommCTUnit)
        if( eachRetCommCTUnitArray):
            retDataArray.extend( eachRetCommCTUnitArray)
    hlSockMang.PassiveSend_To_AcceptSock(iEachAcceptSock, retDataArray)
    pass

# 接收到 操作结果 管套数据单元的处理
# start by sk. 170403
def HandleRecvCTUnit_OPResult(hlSockMang, iEachAcceptSock, ctUnitArray):
    retDataArray = []
    iReplyAddResultCount = 0
    
    for eachCTUnit in ctUnitArray:
        eachRetCommCTUnit = None
        eachRetCommCTUnitArray = []
        if( eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if( eachCTUnit.s_iValue == g_i_OpResult_SubCmd_AddResult):
                SubHandle_OPResult_AddResult( eachCTUnit.s_strValue, eachCTUnit.s_strParam1, eachCTUnit.s_strParam2)
                iReplyAddResultCount += 1

        if( eachRetCommCTUnit):
            retDataArray.append(eachRetCommCTUnit)
        if( eachRetCommCTUnitArray):
            retDataArray.extend( eachRetCommCTUnitArray)

    if( iReplyAddResultCount>0):
        CTYLB_Log.ShowLog(0, u'result-write', u'write %d result count' % iReplyAddResultCount)

    retCommCTUnit = CTYBot_CTUnit_CommonData()
    retCommCTUnit.SetIntData( g_i_OpResult_SubCmd_ReplyAddResult)
    retCommCTUnit.SetStrData( str(iReplyAddResultCount).encode())

    retDataArray.append(retCommCTUnit)
    hlSockMang.PassiveSend_To_AcceptSock(iEachAcceptSock, retDataArray)
    pass

# 主程序入口
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
    g_mainOperateDB.ReConnect(u"192.168.13.21", 3306, u"zhl_test", u"ABCabc123!@#", u'ty2_funcbot_operate')
    # g_mainOperateDB.ReConnect(u"172.16.56.130", 3306, u"testzhuangshiqi", u"abc888+222@@@", u'ty2_funcbot_operate')

    # 创建机器人框架
    g_LessTYLB_Bot_FrameThread = CLessTYBotFrameThread(config_file, db_file)
    # 设置默认环境处理
    g_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)
    # 准备运行
    g_LessTYLB_Bot_FrameThread.Prepare_Start()

    # 获得管套管理对象
    hlSockMang = g_LessTYLB_Bot_FrameThread.s_HLSockMang
    iOPParamBlock_ListenSock = hlSockMang.CreateListenSock( g_i_ListenSock_TYFBot_OP_DB_Operate_ParamBlock)
    iOPResult_ListenSock = hlSockMang.CreateListenSock( g_i_ListenSock_TYFBot_OP_DB_Operate_Result)
    iAccept_OPParamBlockSock_Array = []
    iAccept_OPResultSock_Array = []

    iLoopFreeCount = 0
    while(g_bSysRunning):
        bTaskBusy = False
        iNewAcceptSockIndex = hlSockMang.ExAcceptNewListenArriveSock( iOPParamBlock_ListenSock)
        if( iNewAcceptSockIndex):
            ustrPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSockIndex)
            CTYLB_Log.ShowLog(0, u'op-param-block', u'from [%s:%d] new HLConnect %d accept.' % (ustrPeerName, iPeerPort, iNewAcceptSockIndex))
            bTaskBusy = True
            iAccept_OPParamBlockSock_Array.append( iNewAcceptSockIndex)
            pass
        for iEachAcceptSock in iAccept_OPParamBlockSock_Array:
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachAcceptSock)
            if( not bSockExist):
                CTYLB_Log.ShowLog(0, u'op-param-block', u'sock %d closed' % (iEachAcceptSock))
                iAccept_OPParamBlockSock_Array.remove( iEachAcceptSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    HandleRecvCTUnit_OPParamBlock( hlSockMang, iEachAcceptSock, ctUnitArray)

        iNewAcceptSockIndex = hlSockMang.ExAcceptNewListenArriveSock( iOPResult_ListenSock)
        if( iNewAcceptSockIndex):
            ustrPeerName, iPeerPort = hlSockMang.GetSockPeerAddr(iNewAcceptSockIndex)
            CTYLB_Log.ShowLog(0, u'op-result', u'from [%s:%d] new HLConnect %d accept.' % (ustrPeerName, iPeerPort, iNewAcceptSockIndex))
            bTaskBusy = True
            iAccept_OPResultSock_Array.append( iNewAcceptSockIndex)
            pass
        for iEachAcceptSock in iAccept_OPResultSock_Array:
            bSockExist, ctUnitArray = hlSockMang.ActiveRecv_From_AcceptSock( iEachAcceptSock)
            if( not bSockExist):
                CTYLB_Log.ShowLog(0, u'op-result', u'sock %d closed' % (iEachAcceptSock))
                iAccept_OPResultSock_Array.remove( iEachAcceptSock)
                break
            else:
                if( ctUnitArray):
                    bTaskBusy = True
                    HandleRecvCTUnit_OPResult( hlSockMang, iEachAcceptSock, ctUnitArray)

        if( not bTaskBusy):
            iLoopFreeCount += 1
            if (iLoopFreeCount > 100):
                time.sleep(0.01)
        else:
            iLoopFreeCount = 0

    # 退出线程
    g_LessTYLB_Bot_FrameThread.SafeStop()
    CTYLB_Log.ShowLog(0, u'sys-echo', u'bye bye')

