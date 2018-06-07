# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_p2p_Db_console.py 控制台表操作实现
#
# start by sk. 170128
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# fix sql query to batch exec mode. by sk. 180311
# update by sk. 180318, 增加send_recv_session的操作时间字段，增加session_data的内容长度字段，增加清除表的功能
# update by sk. 180409, 增加ST_tpd_send_recv_session的保留发送参数字段，reserved_send_param

import pandas as pd
from .Tylb_p2p_Db_Share import CTYLB_DB_Lite_CommFuncShare, CTYLB_SQLite_DB_Conn  # 数据库共享功能实现
from .Tylb_p2p_share import CTYLB_MainSys_MiscFunc
from datetime import datetime

# #######################################################
# 实现对伙伴客户端应答表的功能
#
# start by sk, 170128
# #######################################################
class CTYLBDB_tpd_peek_ack:
    s_strTableName = "tpd_peer_ack"
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 初始化创建表
    # start by sk, 170128
    @staticmethod
    def CreateNewTable(dbLiteConn):
        CTYLB_DB_Lite_CommFuncShare.CreateTable(dbLiteConn, CTYLBDB_tpd_peek_ack.s_strTableName,
                                                '''
                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                peer_client_name TEXT,
                                                last_valid_session_id INTEGER,
                                                last_recv_time datetime,
                                                retry_req_time1 datetime,
                                                retry_req_time2 datetime,
                                                retry_req_time3 datetime,
                                                retry_count INTEGER''',
                                                [['index_name', 'peer_client_name'],
                                                 ['index_valid_session_id', 'last_valid_session_id']])

    # -增加一个记录：
    # start by sk, 170128
    @staticmethod
    def AddNewdRec(dbConn, strPeerClientName, iLastSessionID):
        strPeerClientName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPeerClientName)
        iRetNewRecID = CTYLB_DB_Lite_CommFuncShare.ExecInsertRecField3(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName,
                                                                 "peer_client_name", strPeerClientName,
                                                                 "last_valid_session_id", str(iLastSessionID),
                                                                 "retry_count", '0')
        return iRetNewRecID

    # 读取记录：根据记录ID，获得记录内容
    # start by sk, 161215
    @staticmethod
    def ReadByRecID(dbConn, iRecID):
        strRetClientName = ''
        iRetLastSessionID = 0
        retLastRecvTime = None
        retReqTime1, retReqTime2, retReqTime3 = None, None, None
        iRetRetryCount = 0

        strQueryReply = "select * from " + CTYLBDB_tpd_peek_ack.s_strTableName + " where id=" + str(iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetClientName = recFrameReply["peer_client_name"][0]
            iRetLastSessionID = recFrameReply["last_valid_session_id"][0]
            retLastRecvTime = recFrameReply["last_recv_time"][0]
            retReqTime1 = recFrameReply["retry_req_time1"][0]
            retReqTime2 = recFrameReply["retry_req_time2"][0]
            retReqTime3 = recFrameReply["retry_req_time3"][0]
            iRetRetryCount = recFrameReply["retry_count"][0]
        return strRetClientName, iRetLastSessionID, retLastRecvTime, retReqTime1, retReqTime2, retReqTime3, iRetRetryCount

    # 设置时间字段
    # start by sk, 170128
    @staticmethod
    def UpdateRec_LastRecvTime(dbConn, iRecID, lastRecvTime):
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName,
                                                                   "last_recv_time", lastRecvTime, 'id', str(iRecID))

    # 设置最新到达的会话ID
    # start by sk, 170202
    @staticmethod
    def UpdatePeerName_LastValidSessionID(dbConn, strPeerName, iLastValidSessionID):
        strPeerName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPeerName)
        strClause = "peer_client_name='%s'" % (strPeerName)
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField1(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName, strClause,
                                                        'last_valid_session_id', str(iLastValidSessionID))

    # 搜索某用户最后的id
    # start by sk. 170202
    @staticmethod
    def GetMax_PeerName_SessionID( dbConn, strPeerName):
        strPeerName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPeerName)
        iRetValue = 0  # 初始化

        strMaxQueryField = 'max(last_valid_session_id)'
        strQuery = u"select %s from %s where %s='%s'" % \
                   (strMaxQueryField, CTYLBDB_tpd_peek_ack.s_strTableName, 'peer_client_name', strPeerName)
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetValue = recFrame[strMaxQueryField][0]
            if( not iRetValue):
                iRetValue = 0
        else:
            iRetValue = 0
        return iRetValue

    # 设置时间字段
    # start by sk, 170128
    @staticmethod
    def UpdateRec_NextRetryReqTime(dbConn, iRecID, nextRetryReqTime):
        strClientName, iLastSessionID, lastRecvTime, reqTime1, reqTime2, reqTime3, iOrigRetryCount = \
            CTYLBDB_tpd_peek_ack.ReadByRecID(myConn.s_dbConn, iRecID)
        if( len(strClientName) > 0):
            iSetRetryCount = 0
            strNextReqField = ''

            if( iOrigRetryCount == 0):
                strNextReqField = 'retry_req_time1'
                iSetRetryCount = 1
            elif( iOrigRetryCount == 1):
                strNextReqField = 'retry_req_time2'
                iSetRetryCount = 2
            elif (iOrigRetryCount == 2):
                strNextReqField = 'retry_req_time3'
                iSetRetryCount = 3
            CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName,
                                                                       strNextReqField, nextRetryReqTime, 'id', str(iRecID))
            strClause = 'id=%d' % (iRecID)
            CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField1(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName, strClause,
                                                            'retry_count', str(iSetRetryCount))
            pass

    # 读取用户名记录列表
    # start by sk, 170202
    @staticmethod
    def Get_PeerName_Array(dbConn):
        strClause = 'id>0'
        strPeerNameArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName, 'peer_client_name', strClause)
        strRetDistPeerNameArray = []
        for eachPeerName in strPeerNameArray:
            if( eachPeerName not in strRetDistPeerNameArray):
                strRetDistPeerNameArray.append( eachPeerName)
        return strRetDistPeerNameArray

    # 删除记录：根据用户名，删除记录
    # start by sk, 161215
    @staticmethod
    def DeleteRec_By_PeerName(dbConn, strPeerClientName):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName, "peer_client_name", strPeerClientName)

    # 删除记录：根据记录ID，删除记录
    # start by sk, 161215
    @staticmethod
    def DeleteRec(dbConn, iRecID):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName, "id", str(iRecID))

    # 清除表的所有记录
    # start by sk, 180318
    @staticmethod
    def EmptyTable(dbConn):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_peek_ack.s_strTableName, '', '')


# 发送接收会话 记录单元
# start by sk. 180311
class ST_tpd_send_recv_session:
    id = 0
    iType = 0
    iStatus = 0
    strMyName = ''
    strDestName = ''
    iTaskType = 0
    iSessionID = 0
    iTaskParam1 = 0
    iSessionType = 0
    iReservedSendParam=0
    execAtionTime = datetime.now()


# #######################################################
# 实现 发送接收数据会话 管理功能
#
# start by sk, 170128
# update by sk, 180409
# #######################################################
class CTYLBDB_tpd_send_recv_session:
    s_strTableName = "tpd_send_recv_session"
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 初始化创建表
    # start by sk, 170128
    @staticmethod
    def CreateNewTable(dbLiteConn):
        CTYLB_DB_Lite_CommFuncShare.CreateTable(dbLiteConn, CTYLBDB_tpd_send_recv_session.s_strTableName,
                                                '''
                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                send_recv_type INTEGER,
                                                cur_status INTEGER,
                                                myname TEXT,
                                                destname TEXT,
                                                task_type INTEGER,
                                                session_id_value INTEGER,
                                                action_time DATETIME,
                                                task_param1 INTEGER,
                                                reserved_send_param INTEGER,
                                                session_type INTEGER''',
                                                [['index_send_recv', 'send_recv_type'],
                                                 ['index_my_name', 'myname'],
                                                 ['index_dest_name', 'destname'],
                                                 ['index_task_type', 'task_type'],
                                                 ['index_session_id', 'session_id_value'],
                                                 ['index_task_param1', 'task_param1'],
                                                 ['index_session_type', 'session_type']])

    # -增加一个记录：
    # start by sk, 170128
    @staticmethod
    def AddNewdRec(dbConn, iType, iStatus, strMyName, strDestName, iTaskType, iSessionID, iSessionType, iTaskParam1, iReservedSendParam=0):
        strMyName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strMyName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        iRetNewRecID = CTYLB_DB_Lite_CommFuncShare.ExecInsertRecField8(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName,
                                                                       "send_recv_type", str(iType),
                                                                       "cur_status", str(iStatus),
                                                                       "myname", strMyName,
                                                                       "destname", strDestName,
                                                                       "task_type", str(iTaskType),
                                                                       "session_id_value", str(iSessionID),
                                                                       "task_param1", str(iTaskParam1),
                                                                       "session_type", str(iSessionType))
        if(iRetNewRecID):
            strClause='id=%d'%(iRetNewRecID)
            CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField1(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, strClause,
                                                            "reserved_send_param", str(iReservedSendParam))
            CTYLBDB_tpd_send_recv_session.UpdateField_ActionTime(dbConn, iRetNewRecID, datetime.now())
        return iRetNewRecID

    # 设置时间
    # start by sk, 170128
    @staticmethod
    def UpdateField_ActionTime(dbConn, iRecID, actionTime):
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName,
                                                                   'action_time', actionTime, 'id', str(iRecID))

    # 读取记录：根据记录ID，获得记录内容
    # start by sk, 161215
    @staticmethod
    def ReadByRecID(dbConn, iRecID):
        iRetType, iRetStatus = 0, 0
        strRetMyName, strRetDestName = '', ''
        iRetTaskType, iRetSessionID, iRetSessionType = 0, 0, 0
        iRetTaskParam1 = 0
        retActionTime = datetime.now()
        iReservedSendParam = 0

        strQueryReply = "select * from " + CTYLBDB_tpd_send_recv_session.s_strTableName + " where id=" + str(iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetType  = recFrameReply["send_recv_type"][0]
            iRetStatus = recFrameReply["cur_status"][0]
            strRetMyName = recFrameReply["myname"][0]
            strRetDestName = recFrameReply["destname"][0]
            iRetTaskType = recFrameReply["task_type"][0]
            iRetSessionID = recFrameReply["session_id_value"][0]
            iRetTaskParam1 = recFrameReply["task_param1"][0]
            iRetSessionType = recFrameReply["session_type"][0]
            iReservedSendParam = recFrameReply["reserved_send_param"][0]
            retActionTime = CTYLB_MainSys_MiscFunc.GetDateTime_From_Str(recFrameReply["action_time"][0])
        return iRetType, iRetStatus, strRetMyName, strRetDestName, iRetTaskType, iRetSessionID, iRetSessionType, \
               iRetTaskParam1, retActionTime, iReservedSendParam

    # 读取记录：根据记录ID，获得记录内容
    # start by sk, 170204
    @staticmethod
    def ReadByRecID_DestName(dbConn, iRecID):
        strRetDestName = ''

        strQueryReply = "select destname from " + CTYLBDB_tpd_send_recv_session.s_strTableName + " where id=" + str(iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetDestName = recFrameReply["destname"][0]
        return strRetDestName

    # 删除记录：根据记录ID，删除记录
    # start by sk, 161215
    @staticmethod
    def DeleteRec(dbConn, iRecID):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, "id", str(iRecID))


    # 把读取的DataFrame转成记录单元队列
    # start by sk, 180311
    @staticmethod
    def __Convert_DataFrame_To_SessionUnit_Array(readDataFrame):
        retSessionRecvSessionUnitArray = []

        recCount = len(readDataFrame)  # 记录个数
        for iIndex in range(recCount):
            tpdSendRecvUnit = ST_tpd_send_recv_session()

            tpdSendRecvUnit.id = readDataFrame["id"][iIndex]
            tpdSendRecvUnit.iType  = readDataFrame["send_recv_type"][iIndex]
            tpdSendRecvUnit.iStatus = readDataFrame["cur_status"][iIndex]
            tpdSendRecvUnit.strMyName = readDataFrame["myname"][iIndex]
            tpdSendRecvUnit.strDestName = readDataFrame["destname"][iIndex]
            tpdSendRecvUnit.iTaskType = readDataFrame["task_type"][iIndex]
            tpdSendRecvUnit.iSessionID = readDataFrame["session_id_value"][iIndex]
            tpdSendRecvUnit.iTaskParam1 = readDataFrame["task_param1"][iIndex]
            tpdSendRecvUnit.iSessionType = readDataFrame["session_type"][iIndex]
            tpdSendRecvUnit.iReservedSendParam = readDataFrame["reserved_send_param"][iIndex]

            tpdSendRecvUnit.execAtionTime = CTYLB_MainSys_MiscFunc.GetDateTime_From_Str(readDataFrame["action_time"][iIndex])

            retSessionRecvSessionUnitArray.append(tpdSendRecvUnit)

        return retSessionRecvSessionUnitArray

    # 获得对应用户空闲需要发送的数据包 记录单元
    # start by sk, 180311
    @staticmethod
    def GetUsersStatus_Type_SessionUnit_Array(dbConn, iSendRecvType, strFromUser, strDestUser, iCurStatus):
        strQuery = "select * from %s where send_recv_type=%d and myname='%s' and destname='%s' and cur_status=%d order by id" % (
            CTYLBDB_tpd_send_recv_session.s_strTableName, iSendRecvType, strFromUser, strDestUser, iCurStatus)
        recFrameReply = pd.read_sql_query(strQuery, dbConn)
        retSessionRecvSessionUnitArray = CTYLBDB_tpd_send_recv_session.__Convert_DataFrame_To_SessionUnit_Array(recFrameReply)

        return retSessionRecvSessionUnitArray

    # 获得对应用户空闲需要发送的数据包
    # start by sk, 170128
    @staticmethod
    def GetUsersStatus_Type_RecID_Array(dbConn, iSendRecvType, strFromUser, strDestUser, iCurStatus):
        strFromUser = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromUser)
        strDestUser = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestUser)
        strClause = "send_recv_type=%d and myname='%s' and destname='%s' and cur_status=%d order by id" % (iSendRecvType, strFromUser, strDestUser, iCurStatus)
        retIDArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, 'id', strClause, True)
        return retIDArray

    # 获得字段最大值
    # start by sk. 161121
    @staticmethod
    def GetMax_FromToUser_SendRecvType_SessionID( dbConn, iSendRecvType, strFromName, strDestName):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        iRetValue = 0  # 初始化

        strMaxQueryField = 'max(session_id_value)'
        strQuery = u"select %s from %s where %s=%d and %s='%s' and %s='%s'" % \
                   (strMaxQueryField, CTYLBDB_tpd_send_recv_session.s_strTableName, 'send_recv_type', iSendRecvType,
                    'myname', strFromName, 'destname', strDestName)
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetValue = recFrame[strMaxQueryField][0]
            if( not iRetValue):
                iRetValue = 0
        else:
            iRetValue = 0
        return iRetValue


    # 获得对应用户名字状态范围会话 记录单元
    # start by sk, 180311
    @staticmethod
    def Get_MyDestName_Status_RangeValueSession_DataUnitArray(dbConn, iSendRecvType, strFromName, strDestName, iExecStatus, iMaxSessionValue):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        strQuery = "select * from %s where send_recv_type=%d and myname='%s' and destname='%s' and cur_status=%d and session_id_value<=%d order by session_id_value" %\
                    (CTYLBDB_tpd_send_recv_session.s_strTableName, iSendRecvType, strFromName, strDestName, iExecStatus, iMaxSessionValue)
        recFrameReply = pd.read_sql_query(strQuery, dbConn)
        retSessionRecvSessionUnitArray = CTYLBDB_tpd_send_recv_session.__Convert_DataFrame_To_SessionUnit_Array(recFrameReply)

        return retSessionRecvSessionUnitArray

    # 获得字段最大值
    # start by sk. 161121
    @staticmethod
    def Get_MyDestName_Status_RangeValueSession_RecIDArray( dbConn, iSendRecvType, strFromName, strDestName, iExecStatus, iMaxSessionValue):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        strClause = "send_recv_type=%d and myname='%s' and destname='%s' and cur_status=%d and session_id_value<=%d order by session_id_value" %\
                    (iSendRecvType, strFromName, strDestName, iExecStatus, iMaxSessionValue)
        retIDArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, 'id', strClause, True)
        return retIDArray

    # 搜索下一个存在的记录，根据用户和接收类型，和开始会话ID
    # start by sk. 170202
    @staticmethod
    def Search_NextExist_RecBy_SendRecvType_FromToUser_SessionID( dbConn, iSendRecvType, strFromName, strDestName, iStartSessionID):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        iRetNextMaxNotExistSessionValue = 0
        strClause = "send_recv_type=%d and myname='%s' and destname='%s' and session_id_value>%d ORDER BY session_id_value" % \
                    (iSendRecvType, strFromName, strDestName, iStartSessionID)
        iRetID = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause( dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, 'id', strClause)
        if (iRetID and iRetID > 0):
            strReadClause = 'id=%d' % iRetID
            iSessionValue = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause( dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName,
                                                                                     'session_id_value', strReadClause)
            if( iSessionValue and iSessionValue > 0):
                iRetNextMaxNotExistSessionValue = iSessionValue
        return iRetNextMaxNotExistSessionValue

    # 根据发送接收类型，和用户名字，和会话id，读取记录id
    # start by sk. 170202
    @staticmethod
    def SearchRecBy_SendRecvType_FromToUser_SessionID( dbConn, iSendRecvType, strFromName, strDestName, iSessionID):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        strClause = "send_recv_type=%d and myname='%s' and destname='%s' and session_id_value=%d" % (iSendRecvType, strFromName, strDestName, iSessionID)
        iRetID = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause( dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, 'id', strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID


    # 获得 发送接收类型，和用户名字，和会话id，读取 记录单元
    # start by sk, 180318
    @staticmethod
    def ReadRecUnit_By_SendRecvType_FromToUser_SessionID( dbConn, iSendRecvType, strFromName, strDestName, iSessionIDValue):
        strClause = "send_recv_type=%d and myname='%s' and destname='%s' and session_id_value=%d" % (iSendRecvType, strFromName, strDestName, iSessionIDValue)
        strQuery = "select * from %s where %s" % (CTYLBDB_tpd_send_recv_session.s_strTableName, strClause)
        recFrameReply = pd.read_sql_query(strQuery, dbConn)
        retSessionRecvSessionUnitArray = CTYLBDB_tpd_send_recv_session.__Convert_DataFrame_To_SessionUnit_Array(recFrameReply)

        retSessionRecUnit = retSessionRecvSessionUnitArray[0] if(retSessionRecvSessionUnitArray) else None
        return retSessionRecUnit


    # 根据发送接收类型，和用户名字，和会话id，读取记录id
    # start by sk. 170202
    @staticmethod
    def SearchRecBy_SendRecvType_FromToUser_SessionID_Param( dbConn, iSendRecvType, strFromName, strDestName, iSessionID, iTaskParam):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        strClause = "send_recv_type=%d and myname='%s' and destname='%s' and session_id_value=%d and task_param1=%d" %\
                    (iSendRecvType, strFromName, strDestName, iSessionID, iTaskParam)
        iRetID = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause( dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, 'id', strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID


    # 根据发送接收类型，和来源用户名，读取记录id队列
    # start by sk. 170204
    @staticmethod
    def GetUsersStatus_Type_FromUser_RecID_Array(dbConn, iSendRecvType, strFromUser, iCurStatus):
        strFromUser = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromUser)
        strClause = "send_recv_type=%d and myname='%s' and cur_status=%d" % (iSendRecvType, strFromUser, iCurStatus)
        retIDArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, 'id', strClause, True)
        return retIDArray

    # 更新状态
    # start by sk, 170128
    @staticmethod
    def UpdateField_RecStatus(dbConn, iRecID, iNewStatus):
        strClause = 'id=%d' % (iRecID)
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField1(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, strClause, 'cur_status', str(iNewStatus))

    # 更新保留发送参数
    # start by sk, 180409
    @staticmethod
    def UpdateField_ReservedSendParam(dbConn, iRecID, iReservedSendParam):
        strClause = 'id=%d' % (iRecID)
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField1(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, strClause,
                                                        'reserved_send_param', str(iReservedSendParam))

    # 读取记录：根据记录ID，读取状态值
    # start by sk, 170204
    @staticmethod
    def ReadRec_Status(dbConn, iRecID):
        iRetStatus = 0

        strQueryReply = "select cur_status from " + CTYLBDB_tpd_send_recv_session.s_strTableName + " where id=" + str(iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetStatus = recFrameReply["cur_status"][0]
        return iRetStatus

    # 删除表中 来源和目标为 特定 用户名的记录
    # start by sk, 180318
    @staticmethod
    def DeleteRec_By_MyNameOrDestName(dbConn, strOperateName):
        strSQL = "delete from %s where myname='%s' or destname='%s'" % (CTYLBDB_tpd_send_recv_session.s_strTableName, strOperateName, strOperateName)
        updateCur = dbConn.cursor()
        updateCur.execute(strSQL)
        updateCur.close()
        dbConn.commit() #确认更新记录

    # 清除表的所有记录
    # start by sk, 180318
    @staticmethod
    def EmptyTable(dbConn):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_send_recv_session.s_strTableName, '', '')

# 读取tpd会话数据的结构
# start by sk. 180311
class ST_tpd_session_data:
    id = 0
    iBelongSessionID=0
    iSeqIndex = 0
    strContent = ''
    iLastPacket = 0
    iContentLength = 0


# #######################################################
# 实现 会话数据 管理功能
#
# start by sk, 170128
# 增加内容长度的字段。 by sk. 180318
# #######################################################
class CTYLBDB_tpd_session_data:
    s_strTableName = "tpd_session_data"
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 初始化创建表
    # start by sk, 170128
    @staticmethod
    def CreateNewTable(dbLiteConn):
        CTYLB_DB_Lite_CommFuncShare.CreateTable(dbLiteConn, CTYLBDB_tpd_session_data.s_strTableName,
                                                '''
                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                belong_session_id INTEGER,
                                                seq_index INTEGER,
                                                strContent TEXT,
                                                content_length INTEGER,
                                                last_packet INTEGER''',
                                                [['index_belong_session_id', 'belong_session_id'],
                                                 ['index_seq_index', 'seq_index']])

    # -增加一个记录：
    # start by sk, 170128
    @staticmethod
    def AddNewdRec(dbConn, iBelongSessionID, iSeqIndex, iLastPacket, strContent):
        strContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strContent)
        iRetNewRecID = CTYLB_DB_Lite_CommFuncShare.ExecInsertRecField5(dbConn, CTYLBDB_tpd_session_data.s_strTableName,
                                                                       "belong_session_id", str(iBelongSessionID),
                                                                       "seq_index", str(iSeqIndex),
                                                                       "strContent", strContent,
                                                                       "content_length", str(len(strContent)),
                                                                       "last_packet", str(iLastPacket))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得记录内容
    # start by sk, 161215
    @staticmethod
    def ReadByRecID(dbConn, iRecID):
        iBelongSessionID, iRetSeqIndex = 0, 0
        strRetContent = ''
        iRetLastPacket = 0

        strQueryReply = "select * from " + CTYLBDB_tpd_session_data.s_strTableName + " where id=" + str(iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iBelongSessionID  = recFrameReply["belong_session_id"][0]
            iRetSeqIndex = recFrameReply["seq_index"][0]
            strRetContent = recFrameReply["strContent"][0]
            iRetLastPacket = recFrameReply["last_packet"][0]
        return iBelongSessionID, iRetSeqIndex, strRetContent, iRetLastPacket

    # 批量读取符合状态会话条件的记录
    # start by sk. 180311
    @staticmethod
    def GetBelongSessionID_SessionUnit_Array(dbConn, iBelongSessionID):
        retSessionUnitArray = []

        strQuery = "select * from %s where belong_session_id=%d order by seq_index" % (
            CTYLBDB_tpd_session_data.s_strTableName, iBelongSessionID)
        recFrameReply = pd.read_sql_query(strQuery, dbConn)
        recCount = len(recFrameReply)  # 记录个数
        for iIndex in range(recCount):
            tpdSessionData = ST_tpd_session_data()

            tpdSessionData.id = recFrameReply["id"][iIndex]
            tpdSessionData.iBelongSessionID  = recFrameReply["belong_session_id"][iIndex]
            tpdSessionData.iSeqIndex = recFrameReply["seq_index"][iIndex]
            tpdSessionData.strContent = recFrameReply["strContent"][iIndex]
            tpdSessionData.iLastPacket = recFrameReply["last_packet"][iIndex]
            tpdSessionData.iContentLength = recFrameReply["content_length"][iIndex]

            retSessionUnitArray.append(tpdSessionData)

        return retSessionUnitArray

    # 读取符合状态值条件的记录ID队列
    # start by sk, 170128
    @staticmethod
    def GetBelongSessionID_RecID_Array(dbConn, iBelongSessionID):
        strClause = 'belong_session_id=%d order by seq_index' % (iBelongSessionID)
        retIDArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_session_data.s_strTableName, 'id', strClause, True)
        return retIDArray

    # 读取符合状态值条件的记录ID队列
    # start by sk, 170128
    @staticmethod
    def GetBelongSessionID_RecID_Array(dbConn, iBelongSessionID):
        strClause = 'belong_session_id=%d order by seq_index' % (iBelongSessionID)
        retIDArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_session_data.s_strTableName, 'id', strClause, True)
        return retIDArray

    # 读取符合状态值条件的记录ID队列
    # start by sk, 170128
    @staticmethod
    def GetMaxSubIndex_By_SessionRecID(dbConn, iBelongSessionID):
        strClause = 'belong_session_id=%d' % (iBelongSessionID)
        iRetMaxSeqIndex = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause(dbConn, CTYLBDB_tpd_session_data.s_strTableName, 'max(seq_index)', strClause)
        if( not iRetMaxSeqIndex):
            iRetMaxSeqIndex = 0
        return iRetMaxSeqIndex

    # 获得记录的内容长度
    # start by sk, 180318
    @staticmethod
    def GetContentLength_By_RecID(dbConn, iRecID):
        strClause = 'id=%d' % (iRecID)
        iRetContentLength = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause(dbConn, CTYLBDB_tpd_session_data.s_strTableName, 'content_length', strClause)
        if( not iRetContentLength):
            iRetContentLength = 0
        return iRetContentLength


    # 获得所属会话ID的记录 的 内容长度
    # start by sk, 180318
    @staticmethod
    def GetContentLength_By_BelongSessionID(dbConn, iBelongSessionID):
        strClause = 'belong_session_id=%d' % (iBelongSessionID)
        iRetContentLength = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause(dbConn, CTYLBDB_tpd_session_data.s_strTableName, 'content_length', strClause)
        if( not iRetContentLength):
            iRetContentLength = 0
        return iRetContentLength

    # 读取子index的记录
    # start by sk, 170202
    @staticmethod
    def GetSubIndex_RecID(dbConn, iBelongSessionID, iSubIndex):
        strClause = 'belong_session_id=%d and seq_index=%d' % (iBelongSessionID, iSubIndex)
        iRetRecID = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause(dbConn, CTYLBDB_tpd_session_data.s_strTableName, 'id', strClause)
        if( not iRetRecID):
            iRetRecID = 0
        return iRetRecID

    # 删除记录：根据记录ID，删除记录
    # start by sk, 161215
    @staticmethod
    def DeleteRec(dbConn, iRecID):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_session_data.s_strTableName, "id", str(iRecID))

    # 删除属于表的另外数据
    @staticmethod
    def DeleteRec_By_BelongSessionID_in_SendRecvSessionRec(dbConn, strSendRecvName):
        strSQL = "DELETE FROM %s where belong_session_id in (select id from %s where myname='%s' or destname='%s')" % (
            CTYLBDB_tpd_session_data.s_strTableName, CTYLBDB_tpd_send_recv_session.s_strTableName, strSendRecvName, strSendRecvName
        )
        updateCur = dbConn.cursor()
        updateCur.execute(strSQL)
        updateCur.close()
        dbConn.commit() #确认更新记录

    # 清除表的所有记录
    # start by sk, 180318
    @staticmethod
    def EmptyTable(dbConn):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_session_data.s_strTableName, '', '')

# #######################################################
# 实现 聊天内容数据 管理功能
#
# start by sk, 170128
# #######################################################
class CTYLBDB_tpd_inout_text:
    s_strTableName = "tpd_inout_text"
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 初始化创建表
    # start by sk, 170128
    @staticmethod
    def CreateNewTable(dbLiteConn):
        CTYLB_DB_Lite_CommFuncShare.CreateTable(dbLiteConn, CTYLBDB_tpd_inout_text.s_strTableName,
                                                '''
                                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                input_reply_type INTEGER,
                                                content TEXT,
                                                from_name TEXT,
                                                dest_name TEXT,
                                                peer_exec_status INTEGER,
                                                create_time DATETIME,
                                                reply_time DATETIME''',
                                                [['index_input_type', 'input_reply_type'],
                                                 ['index_self_name', 'from_name'],
                                                 ['index_dest_name', 'dest_name'],
                                                 ['index_peer_status', 'peer_exec_status'] ])

    # -增加一个记录：
    #  iInputReplyType = 0, 输入记录; ＝1， 回应的记录
    #  iPeerStatus = 0, 未读取; =1, 正在处理; =2, 处理完成
    # start by sk, 170128
    @staticmethod
    def AddNewdRec(dbConn, iInputReplyType, strContent, strSelfName, strDestName, iPeerStatus, createTime, replyTime):
        strContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strContent)
        strSelfName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strSelfName)
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        iRetNewRecID = CTYLB_DB_Lite_CommFuncShare.ExecInsertRecField5(dbConn, CTYLBDB_tpd_inout_text.s_strTableName,
                                                                       "input_reply_type", str(iInputReplyType),
                                                                       "content", strContent,
                                                                       "from_name", strSelfName,
                                                                       "dest_name", strDestName,
                                                                       "peer_exec_status", str(iPeerStatus))
        if( iRetNewRecID > 0):
            if( createTime):
                CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CTYLBDB_tpd_inout_text.s_strTableName,
                                                                            'create_time', createTime, 'id', str(iRetNewRecID))
            if (replyTime):
                CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CTYLBDB_tpd_inout_text.s_strTableName,
                                                                           'reply_time', replyTime, 'id',
                                                                           str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得记录内容
    # start by sk, 170128
    @staticmethod
    def ReadByRecID(dbConn, iRecID):
        iRetInputReplyType = 0
        strRetContent = ''
        strRetSelfName, strRetDestName = '', ''
        iRetPeerStatus = 0
        retCreateTime, retReplyTime = None, None

        strQueryReply = "select * from " + CTYLBDB_tpd_inout_text.s_strTableName + " where id=" + str(iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetInputReplyType = recFrameReply["input_reply_type"][0]
            strRetContent = recFrameReply["content"][0]
            strRetSelfName = recFrameReply["from_name"][0]
            strRetDestName = recFrameReply["dest_name"][0]
            iRetPeerStatus = recFrameReply["peer_exec_status"][0]
            retCreateTime = recFrameReply["create_time"][0]
            retReplyTime = recFrameReply["reply_time"][0]
        return iRetInputReplyType, strRetContent, strRetSelfName, strRetDestName, iRetPeerStatus, retCreateTime, retReplyTime

    # 删除记录：根据记录ID，删除记录
    # start by sk, 170128
    @staticmethod
    def DeleteRec(dbConn, iRecID):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_inout_text.s_strTableName, "id", str(iRecID))

    # 设置时间
    # start by sk, 170128
    @staticmethod
    def UpdateField_CreateTime(dbConn, iRecID, createTime):
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CTYLBDB_tpd_inout_text.s_strTableName,
                                                                   'create_time', createTime, 'id', str(iRecID))

    # 设置时间
    # start by sk, 170128
    @staticmethod
    def UpdateField_ReplyTime(dbConn, iRecID, createTime):
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CTYLBDB_tpd_inout_text.s_strTableName,
                                                                   'reply_time', createTime, 'id', str(iRecID))

    # 更新状态
    # start by sk, 170128
    @staticmethod
    def UpdateField_PeerStatus(dbConn, iRecID, iNewPeerStatus):
        strClause = 'id=%d' % (iRecID)
        CTYLB_DB_Lite_CommFuncShare.ExecUpdateRecField1(dbConn, CTYLBDB_tpd_inout_text.s_strTableName, strClause, 'peer_exec_status', str(iNewPeerStatus))

    # 读取下一个源用户的某状态条件的记录
    # start by sk, 170128
    @staticmethod
    def GetNextRec_By_FromName_Status(dbConn, strFromName, iExecStatus):
        strFromName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strFromName)
        iRetRecID = 0
        strQuery = "select id from %s where from_name='%s' and peer_exec_status=%d" % (CTYLBDB_tpd_inout_text.s_strTableName,
                                                                                       strFromName, iExecStatus)
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetRecID = recFrame["id"][0]
        return iRetRecID

    # 读取下一个对象用户的某条件的记录
    # start by sk, 170128
    @staticmethod
    def GetNextRec_By_DestName_Status(dbConn, strDestName, iExecStatus):
        strDestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDestName)
        iRetRecID = 0
        strQuery = "select id from %s where dest_name='%s' and peer_exec_status=%d" % (CTYLBDB_tpd_inout_text.s_strTableName,
                                                                                       strDestName, iExecStatus)
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetRecID = recFrame["id"][0]
        return iRetRecID

    # 获得某个状态的记录队列
    # start by sk, 170402
    @staticmethod
    def GetStatus_RecID_Array(dbConn, iStatus):
        strClause = "peer_exec_status=%d order by id" % (iStatus)
        retIDArray = CTYLB_DB_Lite_CommFuncShare.ReadField_Array_WithClause(dbConn, CTYLBDB_tpd_inout_text.s_strTableName, 'id', strClause, True)
        return retIDArray

    # 清除表的所有记录
    # start by sk, 180318
    @staticmethod
    def EmptyTable(dbConn):
        CTYLB_DB_Lite_CommFuncShare.ExecDeleteFrom(dbConn, CTYLBDB_tpd_inout_text.s_strTableName, '', '')

if __name__ == '__main__':
    # 登记异常处理函数
    myConn = CTYLB_SQLite_DB_Conn( 'db/first.db')

    iSetRecID = 3
    lastUpdateDate = datetime( 2017, 1, 15, 1,2,3)
    CTYLBDB_tpd_peek_ack.UpdateRec_LastRecvTime( myConn.s_dbConn, iSetRecID, lastUpdateDate)

    strClientName, iLastSessionID, lastRecvTime, reqTime1, reqTime2, reqTime3, iOrigRetryCount = \
        CTYLBDB_tpd_peek_ack.ReadByRecID(myConn.s_dbConn, iSetRecID)
    if( len(strClientName) > 0):
        if( lastRecvTime):
            print(lastRecvTime)

    print( ' ok ')

