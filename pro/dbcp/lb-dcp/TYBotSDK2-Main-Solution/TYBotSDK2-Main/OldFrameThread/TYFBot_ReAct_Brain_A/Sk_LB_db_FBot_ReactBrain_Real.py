# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_db_FBot_ReactBrain_Real.py
# 极限天元机器人-功能机器人-行动大脑功能数据库 实现
#
# restart by sk. 170407
# update by sk. 170412

import pandas as pd
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_CommFuncShare  # 数据库共享功能实现
from datetime import datetime
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc

# #######################################################
# 操作用户名表 ea_brain_usermang 实现类 CSkLBDB_ea_brain_usermang
# start by sk, 170412
# #######################################################
class CSkLBDB_ea_brain_usermang:
    s_strTableName = u"ea_brain_usermang"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, ustrUserName):
        ustrUserName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrUserName)
        iOrigRecID = CSkLBDB_ea_brain_usermang.GetRecID_By_UserName( dbConn, ustrUserName)
        if( not iOrigRecID):
            iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField1(dbConn, CSkLBDB_ea_brain_usermang.s_strTableName,
                                                                     "username", ustrUserName)
        else:
            iRetNewRecID = iOrigRecID
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        ustrRetName = u''

        strQueryReply = u"select * from %s where id=%d" % (CSkLBDB_ea_brain_usermang.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            ustrRetName  = recFrameReply["username"][0]

        return ustrRetName

    # 搜索指定的记录
    @staticmethod
    def GetRecID_By_UserName( dbConn, ustrUserName):
        ustrUserName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrUserName)
        strClause = "username='%s'" % ( ustrUserName)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_ea_brain_usermang.s_strTableName,
                                                                   "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID


# #######################################################
# 操作用户环境表 ea_brain_envirument 实现类 CSkLBDB_ea_brain_envirument
# start by sk, 170412
# #######################################################
class CSkLBDB_ea_brain_envirument:
    s_strTableName = u"ea_brain_envirument"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iUserNameID, ustrBelongGroupName):
        ustrBelongGroupName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrBelongGroupName)
        iOrigRecID = CSkLBDB_ea_brain_envirument.GetRecID_By_UserID_GroupName( dbConn, iUserNameID, ustrBelongGroupName)
        if( not iOrigRecID):
            iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField2(dbConn, CSkLBDB_ea_brain_envirument.s_strTableName,
                                                                     "belong_usermang_id", str(iUserNameID),
                                                                     'belong_group_name', ustrBelongGroupName)
        else:
            iRetNewRecID = iOrigRecID
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongUserMangID, strRetGroupName = 0, ''

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ea_brain_envirument.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongUserMangID = recFrameReply["belong_usermang_id"][0]
            strRetGroupName = recFrameReply["belong_group_name"][0]

        return iRetBelongUserMangID, strRetGroupName

    # 搜索指定的记录
    @staticmethod
    def GetRecID_By_UserID_GroupName( dbConn, iUserNameID, ustrBelongGroupName):
        ustrBelongGroupName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrBelongGroupName)
        strClause = "belong_usermang_id=%d and belong_group_name='%s'" % ( iUserNameID, ustrBelongGroupName)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_ea_brain_envirument.s_strTableName,
                                                                   "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID

    # 获得 某个群里用户对话过的 环境id列表
    # start by sk, 170413
    @staticmethod
    def GetRecList_By_GroupName( dbConn, ustrGroupName):
        ustrGroupName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrGroupName)
        strClause = "belong_group_name='%s'" % (ustrGroupName)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause( dbConn, CSkLBDB_ea_brain_envirument.s_strTableName,
                                                                           "id", strClause)
        return iRetRecIDArray


# #######################################################
# 操作用户聊天内容表 ea_brain_chatcontent 实现类 CSkLBDB_ea_brain_chatcontent
# start by sk, 170412
# #######################################################
class CSkLBDB_ea_brain_chatcontent:
    s_strTableName = u"ea_brain_chatcontent"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iBelongEnviruID, ustrChatContent, iContentType, iDirection, createTime=None, execTime=None, iExecStatus=0):
        ustrChatContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrChatContent)

        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField5(dbConn, CSkLBDB_ea_brain_chatcontent.s_strTableName,
                                                                 "chat_content", ustrChatContent,
                                                                 'belong_envirument_id', str(iBelongEnviruID),
                                                                 'chat_content_type', str(iContentType),
                                                                 'chat_direction', str(iDirection),
                                                                 'exec_status', str(iExecStatus))
        if( iRetNewRecID):
            if( not createTime):
                createTime = datetime.now()
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_ea_brain_chatcontent.s_strTableName,
                                                                  "create_time", createTime, "id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongEnviruID, strRetChatContent, iRetContentType, iRetDirection = 0, '', 0, 0
        retCreateTime = datetime.now()
        retExecTime = datetime.now()
        iRetExecStatus = 0

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ea_brain_chatcontent.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongEnviruID = recFrameReply["belong_envirument_id"][0]
            strRetChatContent = recFrameReply["chat_content"][0]
            iRetContentType = recFrameReply["chat_content_type"][0]
            iRetDirection = recFrameReply["chat_direction"][0]
            retCreateTime = recFrameReply["create_time"][0]
            retExecTime = recFrameReply["exec_time"][0]
            iRetExecStatus = recFrameReply["exec_status"][0]

        return iRetBelongEnviruID, strRetChatContent, iRetContentType, iRetDirection, retCreateTime, retExecTime, iRetExecStatus


    # 获得 任务类型，和状态值 的记录  -返回值： ID列表
    @staticmethod
    def SearchNextRec_By_Direction_ExecStatus( dbConn, iDirection, iExecStatus):
        strClause = "chat_direction=%d and exec_status=%d" % ( iDirection, iExecStatus)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause_limit( dbConn, CSkLBDB_ea_brain_chatcontent.s_strTableName,
                                                                           "id", strClause, 1)

        iRetExecRecID = 0
        if( iRetRecIDArray):
            iRetExecRecID = iRetRecIDArray[0]
        return iRetExecRecID

    # -更新记录的状态值
    @staticmethod
    def Update_ExTime_Status( dbConn, iRecID, execTime, iNewStatus):
        CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_ea_brain_chatcontent.s_strTableName,
                                                             "exec_time", execTime, "id", str(iRecID))
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ea_brain_chatcontent.s_strTableName, strClause,
                                                  "exec_status", str(iNewStatus))

    # 获得 所属环境id，对话方向，执行状态 的记录  -返回值： ID列表
    @staticmethod
    def GetRecList_By_BelongEnvID_Direction_ExecStatus( dbConn, iBelongEnvID, iDirection, iExecStatius):
        strClause = "belong_envirument_id=%d and chat_direction=%d and exec_status=%d" % (iBelongEnvID, iDirection, iExecStatius)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause( dbConn, CSkLBDB_ea_brain_chatcontent.s_strTableName,
                                                                           "id", strClause)
        return iRetRecIDArray

# #######################################################
# 操作任务行动表 ea_brain_exec_task 实现类 CSkLBDB_ea_brain_exec_task
# start by sk, 170412
# #######################################################
class CSkLBDB_ea_brain_exec_task:
    s_strTableName = u"ea_brain_exec_task"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iBelongEnviruID, iTaskTypeID, ustrContent, ustrParam, ustrWhoRequestName, iTaskRunAlways, createTime=None, requestExecTime=None, iRequestExecStatus=0):
        ustrContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrContent)
        ustrParam = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrParam)
        ustrWhoRequestName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrWhoRequestName)

        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField7(dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                                 'belong_envirument_id', str(iBelongEnviruID),
                                                                 "task_type_id", str(iTaskTypeID),
                                                                 'content', ustrContent,
                                                                 'param', ustrParam,
                                                                 'request_exec_status', str(iRequestExecStatus),
                                                                 'who_request_name', ustrWhoRequestName,
                                                                 'task_run_always', str(iTaskRunAlways))
        if( iRetNewRecID):
            if( not createTime):
                createTime = datetime.now()
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                                  "create_time", createTime, "id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongEnviruID, iRetTaskTypeID, strRetContent, strRetParam, strRetWhoRequestName = 0, 0, '', '', ''
        retCreateTime, retRequestExecTime, iRetRequestExecStatus = datetime.now(), datetime.now(), 0
        iRetTaskRunAlways, retLastCheckTime, strRetTaskRunParam = 0, datetime.now(), ''

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ea_brain_exec_task.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongEnviruID = recFrameReply["belong_envirument_id"][0]
            iRetTaskTypeID = recFrameReply["task_type_id"][0]
            strRetContent = recFrameReply["content"][0]
            strRetParam = recFrameReply["param"][0]
            strRetWhoRequestName = recFrameReply["who_request_name"][0]
            retCreateTime = recFrameReply["create_time"][0]
            retRequestExecTime = recFrameReply["request_exec_time"][0]
            iRetRequestExecStatus = recFrameReply["request_exec_status"][0]
            iRetTaskRunAlways = recFrameReply['task_run_always'][0]
            retLastCheckTime = recFrameReply['last_check_time'][0]
            strRetTaskRunParam = recFrameReply['task_run_param'][0]

        return iRetBelongEnviruID, iRetTaskTypeID, strRetContent, strRetParam, strRetWhoRequestName, retCreateTime,\
               retRequestExecTime, iRetRequestExecStatus, iRetTaskRunAlways, retLastCheckTime, strRetTaskRunParam


    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def Read_EnvID_LastCheckTIme_By_RecID( dbConn, iRecID):
        iRetBelongEnviruID, retLastCheckTime = 0, None

        strQueryReply = "select belong_envirument_id, last_check_time from %s where id=%d" % (CSkLBDB_ea_brain_exec_task.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongEnviruID = recFrameReply["belong_envirument_id"][0]
            retLastCheckTime = recFrameReply['last_check_time'][0]

        if( not retLastCheckTime):
            retLastCheckTime = datetime(2017,1,1)

        return iRetBelongEnviruID, retLastCheckTime

    # 读取记录：根据记录ID，获得字段内容
    # start by sk. 170413
    @staticmethod
    def Read_RequestExecTime_By_RecID(dbConn, iRecID):
        strClause = "id=%d" % (iRecID)
        retRequestExecTime = CSkLBDB_CommFuncShare.ReadField_Single_WithClause( dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                                                'request_exec_time', strClause)

        return retRequestExecTime

    # -更新记录的状态值
    @staticmethod
    def Update_LastCheckTime( dbConn, iRecID, lastCheckTime=None):
        strClause = "id=%d" % (iRecID)
        if (not lastCheckTime):
            lastCheckTime = datetime.now()
        CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                             "last_check_time", lastCheckTime, "id", str(iRecID))

    # -更新记录的状态值
    @staticmethod
    def Update_RequestExecTime( dbConn, iRecID, requestExecTime):
        strClause = "id=%d" % (iRecID)
        if (not requestExecTime):
            requestExecTime = datetime.now()
        CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                             "request_exec_time", requestExecTime, "id", str(iRecID))

    # 获得 任务类型，和状态值 的记录  -返回值： ID列表
    @staticmethod
    def GetRecList_By_TaskTypeID_ExecStatus( dbConn, iTaskTypeID, iExecStatus):
        strClause = "task_type_id=%d and request_exec_status=%d" % (iTaskTypeID, iExecStatus)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause_limit( dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                                           "id", strClause, 1)
        return iRetRecIDArray

    # -更新记录的状态值
    @staticmethod
    def Update_ExStatus( dbConn, iRecID, iNewStatus):
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName, strClause,
                                                  "request_exec_status", str(iNewStatus))

    # -更新记录的请求者
    @staticmethod
    def Update_RequestName( dbConn, iRecID, ustrRequestorName):
        ustrRequestorName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrRequestorName)
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName, strClause,
                                                  "who_request_name", ustrRequestorName)

    # -更新记录的运行参数
    @staticmethod
    def Update_RunParam( dbConn, iRecID, ustrRunParam):
        ustrRunParam = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrRunParam)
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName, strClause,
                                                  "task_run_param", ustrRunParam)

    # 获得 完成，而且又要持续运行的 的记录  -返回值： ID列表
    @staticmethod
    def GetRecList_By_Status_AlwaysValue( dbConn, iExecStatus, iAlwaysRun):
        strClause = "request_exec_status=%d and task_run_always=%d" % (iExecStatus, iAlwaysRun)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause( dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                                           "id", strClause)
        return iRetRecIDArray

    # 获得 某状态值 的记录  -返回值： ID列表
    @staticmethod
    def GetRecList_By_Status( dbConn, iExecStatus):
        strClause = "request_exec_status=%d" % (iExecStatus)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause( dbConn, CSkLBDB_ea_brain_exec_task.s_strTableName,
                                                                           "id", strClause)
        return iRetRecIDArray


# #######################################################
# 执行结果 表 ea_brain_exec_result 实现类 CSkLBDB_ea_brain_exec_result
# start by sk, 170412
# #######################################################
class CSkLBDB_ea_brain_exec_result:
    s_strTableName = u"ea_brain_exec_result"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iExecTaskID, ustrReplyContent, ustrReplyParam, ustrWhoExec, execStartTime=None, execFinishTime=None, iExecStatus=0):
        ustrReplyContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrReplyContent)
        ustrReplyParam = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrReplyParam)
        ustrWhoExec = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrWhoExec)

        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField5(dbConn, CSkLBDB_ea_brain_exec_result.s_strTableName,
                                                                 'exec_task_id', str(iExecTaskID),
                                                                 "reply_content", ustrReplyContent,
                                                                 'reply_param', ustrReplyParam,
                                                                 'exec_status', str(iExecStatus),
                                                                 'who_exec_name', ustrWhoExec)
        if( iRetNewRecID):
            if( not execStartTime):
                createTime = datetime.now()
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_ea_brain_exec_result.s_strTableName,
                                                                  "exec_start_time", execStartTime, "id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iExecTaskID, strReplyContent, strReplyParam, strWhoExec = 0, '', '', ''
        execStartTime, execFinishTime, iExecStatus = datetime.now(), datetime.now(), 0

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ea_brain_exec_result.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iExecTaskID = recFrameReply["exec_task_id"][0]
            strReplyContent = recFrameReply["reply_content"][0]
            strReplyParam = recFrameReply["reply_param"][0]
            strWhoExec = recFrameReply["who_exec_name"][0]
            execStartTime = recFrameReply["exec_start_time"][0]
            execFinishTime = recFrameReply["exec_finish_time"][0]
            iExecStatus = recFrameReply["exec_status"][0]

        return iExecTaskID, strReplyContent, strReplyParam, strWhoExec, execStartTime, execFinishTime, iExecStatus

    # -更新记录的状态值
    @staticmethod
    def Update_ExStatus( dbConn, iRecID, iNewStatus):
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ea_brain_exec_result.s_strTableName, strClause,
                                                  "exec_status", str(iNewStatus))


# #######################################################
# 环境会话对象 属性 表 ea_brain_enviru_property 实现类 CSkLBDB_ea_brain_enviru_property
# start by sk, 170412
# #######################################################
class CSkLBDB_ea_brain_enviru_property:
    s_strTableName = u"ea_brain_enviru_property"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iBelongEnviruID, ustrPropName, ustrPropValue):
        ustrPropName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrPropName)
        ustrPropValue = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrPropValue)

        iRetNewRecID = CSkLBDB_ea_brain_enviru_property.GetRecID_By_EnviruID_PropName( dbConn, iBelongEnviruID, ustrPropName)
        if( not iRetNewRecID):
            iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField3(dbConn, CSkLBDB_ea_brain_enviru_property.s_strTableName,
                                                                     'belong_envirument_id', str(iBelongEnviruID),
                                                                     "prop_name", ustrPropName,
                                                                     'prop_value', ustrPropValue)
        else:
            CSkLBDB_ea_brain_enviru_property.Update_PropValue( dbConn, iRetNewRecID, ustrPropValue)
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongEnviruID, strRetPropName, strRetPropValue = 0, '', ''

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ea_brain_enviru_property.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongEnviruID = recFrameReply["belong_envirument_id"][0]
            strRetPropName = recFrameReply["prop_name"][0]
            strRetPropValue = recFrameReply["prop_value"][0]

        return iRetBelongEnviruID, strRetPropName, strRetPropValue

    # -更新记录的状态值
    @staticmethod
    def Update_PropValue( dbConn, iRecID, ustrPropValue):
        ustrPropValue = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrPropValue)
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ea_brain_enviru_property.s_strTableName, strClause,
                                                  "prop_value", ustrPropValue)


    # 搜索指定的记录
    @staticmethod
    def GetRecID_By_EnviruID_PropName(dbConn, iBelongEnviruID, ustrPropName):
        ustrPropName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrPropName)
        strClause = "belong_envirument_id=%d and prop_name='%s'" % (iBelongEnviruID, ustrPropName)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_ea_brain_enviru_property.s_strTableName,
                                                                   "id", strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID

    # 读取值字段
    @staticmethod
    def ReadValueField_By_RecID(dbConn, iRecID):
        strClause = "id=%d" % (iRecID)
        strPropValue = CSkLBDB_CommFuncShare.ReadField_Single_WithClause( dbConn, CSkLBDB_ea_brain_enviru_property.s_strTableName,
                                                                          'prop_value', strClause)
        return strPropValue

