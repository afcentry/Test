# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_db_funcbot_operate.py
# 极限天元机器人-功能机器人-操作数据库 实现
#
# restart by sk. 170403

import pandas as pd
from Sk_LB_db_main_share_cp import CSkLBDB_CommFuncShare  # 数据库共享功能实现
from datetime import datetime

# #######################################################
# 操作目标表实现 sk_dest_operate 实现类 CSkLBDB_dest_operate
# start by sk, 170403
# #######################################################
class CSkLBDB_dest_operate:
    s_strTableName = "sk_dest_operate"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn,  strObjName, strPwdHash, strDbName, strTableName, strFieldName, strSignIDField, iLastExID):
        iOrigRecID = CSkLBDB_dest_operate.GetRecID_By_Name( dbConn, strObjName)
        if( iOrigRecID == 0):
            iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField7(dbConn, CSkLBDB_dest_operate.s_strTableName,
                                                                     "obj_name", strObjName,
                                                                     "pwd_hash", strPwdHash,
                                                                     "database_name", strDbName,
                                                                     "table_name", strTableName,
                                                                     "read_field_name_array", strFieldName,
                                                                     "sign_field_id", strSignIDField,
                                                                     "last_ex_id_value", str(iLastExID) )
        else:
            iRetNewRecID = iOrigRecID
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        strRetObjName, strRetPwdHash, strRetDbName, strRetTableName = '', '', '', ''
        strRetFieldName, strRetSignIDField, iRetLastExID = '', '', 0

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_dest_operate.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetObjName = recFrameReply["obj_name"][0]
            strRetPwdHash = recFrameReply["pwd_hash"][0]
            strRetDbName = recFrameReply["database_name"][0]
            strRetTableName = recFrameReply["table_name"][0]
            strRetFieldName = recFrameReply["read_field_name_array"][0]
            strRetSignIDField = recFrameReply["sign_field_id"][0]
            iRetLastExID = recFrameReply["last_ex_id_value"][0]

        return strRetObjName, strRetPwdHash, strRetDbName, strRetTableName, strRetFieldName, strRetSignIDField, iRetLastExID

    # 搜索指定名字值的记录  -返回值： ID列表
    @staticmethod
    def GetRecID_By_Name(dbConn, strObjName):
        strClause = "obj_name='%s'" % (strObjName)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_dest_operate.s_strTableName,
                                                                          "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID

    # 读取记录：根据记录ID，获得某字段内容
    @staticmethod
    def ReadLastExecID_By_RecID( dbConn, iRecID):
        iRetLastExecID = 0

        strQueryReply = "select last_ex_id_value from %s where id=%d" % (CSkLBDB_dest_operate.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetLastExecID = recFrameReply["last_ex_id_value"][0]
        return iRetLastExecID

    # -更新记录的最后id值
    @staticmethod
    def Update_LastIDValue( dbConn, iRecID, iLastIDValue):
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_dest_operate.s_strTableName, strClause,
                                                  "last_ex_id_value", str(iLastIDValue))


# #######################################################
# 参数块表实现 sk_dest_param_status 实现类 CSkLBDB_dest_param_status
# start by sk, 170403
# #######################################################
class CSkLBDB_dest_param_status:
    s_strTableName = "sk_dest_param_status"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iBelongDestOPID, strSignIDFieldValue, strParamBlockID, iStatus, operateTime, createTime=None):
        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField4(dbConn, CSkLBDB_dest_param_status.s_strTableName,
                                                                 "belong_dest_operate_id", str(iBelongDestOPID),
                                                                 "sign_id_field_value", strSignIDFieldValue,
                                                                 "param_block_id", strParamBlockID,
                                                                 "status", str(iStatus))
        if( (iRetNewRecID > 0) and ( operateTime)):
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_dest_param_status.s_strTableName,
                                                                  "operate_time", operateTime, "id", str(iRetNewRecID) )
        if( not createTime):
            createTime = datetime.now()
        if( (iRetNewRecID > 0) and ( createTime)):
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_dest_param_status.s_strTableName,
                                                                  "create_time", createTime, "id", str(iRetNewRecID) )
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongDestOPID, strRetSignIDFieldValue, strRetParamBlockID, iRetStatus = 0, '', '', 0
        retOperateTime = datetime.now()
        retCreateTime = datetime.now()

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_dest_param_status.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongDestOPID = recFrameReply["belong_dest_operate_id"][0]
            strRetSignIDFieldValue = recFrameReply["sign_id_field_value"][0]
            strRetParamBlockID = recFrameReply["param_block_id"][0]
            iRetStatus = recFrameReply["status"][0]
            retOperateTime = recFrameReply["operate_time"][0]
            retCreateTime = recFrameReply["create_time"][0]

        return iRetBelongDestOPID, strRetSignIDFieldValue, strRetParamBlockID, iRetStatus, retOperateTime, retCreateTime

    # -获得操作对象ID和参数ID对应的记录id
    @staticmethod
    def GetRecID_By_OperateID_ParamBlockID( dbConn, iBelongOperateID, strParamBlockID):
        strClause = "belong_dest_operate_id=%d and param_block_id='%s'" % (iBelongOperateID, strParamBlockID)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_dest_param_status.s_strTableName,
                                                                   "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID

    # -更新记录内容
    @staticmethod
    def Update_Status_OpTime( dbConn, iRecID, iNewStatus, operateTime):
        strClause = 'id=%d' % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_dest_param_status.s_strTableName, strClause, "status", str(iNewStatus))
        CSkLBDB_dest_param_status.UpdateRecOperateTime( dbConn, iRecID, operateTime)

    # -更新记录内容
    @staticmethod
    def UpdateRecOperateTime( dbConn, iRecID, operateTime):
        CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_dest_param_status.s_strTableName,
                                                             "operate_time", operateTime, "id", str(iRecID))

# #######################################################
# 结果应用任务名表实现 sk_result_app_task_name 实现类 CSkLBDB_result_app_task_name
# start by sk, 170403
# #######################################################
class CSkLBDB_result_app_task_name:
    s_strTableName = "sk_result_app_task_name"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, strAppName, strSubTaskName):
        iRetNewRecID = CSkLBDB_result_app_task_name.GetRecID_By_App_SubTask_Name( dbConn, strAppName, strSubTaskName)
        if( iRetNewRecID == 0):
            iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField2(dbConn, CSkLBDB_result_app_task_name.s_strTableName,
                                                                     "app_name", strAppName,
                                                                     "sub_task_name", strSubTaskName)
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        strRetAppName, strRetSubTaskName = '', ''

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_result_app_task_name.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetAppName = recFrameReply["app_name"][0]
            strRetSubTaskName = recFrameReply["sub_task_name"][0]
        return strRetAppName, strRetSubTaskName

    # 搜索指定URL的记录
    @staticmethod
    def GetRecID_By_App_SubTask_Name( dbConn, strAppName, strSubTaskName):
        strClause = "app_name='%s' and sub_task_name='%s'" % (strAppName, strSubTaskName)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_result_app_task_name.s_strTableName,
                                                                   "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID


# #######################################################
# 结果内容表实现 sk_result_content 实现类 CSkLBDB_result_content
# start by sk, 170403
# #######################################################
class CSkLBDB_result_content:
    s_strTableName = "sk_result_content"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iBelongParamID, strTitleName, strResultContent, createTime=None):
        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField3(dbConn, CSkLBDB_result_content.s_strTableName,
                                                                 "belong_param_id", str(iBelongParamID),
                                                                 "title_name", strTitleName,
                                                                 "result_content", strResultContent)
        if( not createTime):
            createTime = datetime.now()
        if( (iRetNewRecID > 0) and (createTime)):
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_result_content.s_strTableName,
                                                       "create_time", createTime,
                                                       "id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongParamID, strRetTitleName, strRetResultContent = 0, '', ''
        retCreateTime = datetime.now()

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_result_content.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongParamID = recFrameReply["belong_param_id"][0]
            strRetTitleName = recFrameReply["title_name"][0]
            strRetResultContent = recFrameReply["result_content"][0]
            retCreateTime = recFrameReply["create_time"][0]

        return iRetBelongParamID, strRetTitleName, strRetResultContent, retCreateTime


# #######################################################
# 结果参数块表实现 sk_result_param_block 实现类 CSkLBDB_result_param_block
# start by sk, 170403
# #######################################################
class CSkLBDB_result_param_block:
    s_strTableName = "sk_result_param_block"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, iBelongAppTaskNameID, strParamID):
        iRetNewRecID = CSkLBDB_result_param_block.GetRecID_By_AppTaskNameID_ParamID( dbConn, iBelongAppTaskNameID, strParamID)
        if( iRetNewRecID == 0):
            iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField2(dbConn, CSkLBDB_result_param_block.s_strTableName,
                                                                     "belong_app_task_name_id", str(iBelongAppTaskNameID),
                                                                     "param_id", strParamID)
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        iRetBelongAppTaskNameID, strRetParamID = 0, ''

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_result_param_block.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            iRetBelongAppTaskNameID = recFrameReply["belong_app_task_name_id"][0]
            strRetParamID = recFrameReply["param_id"][0]
        return iRetBelongAppTaskNameID, strRetParamID

    # 搜索指定的记录
    @staticmethod
    def GetRecID_By_AppTaskNameID_ParamID( dbConn, iBelongAppTaskNameID, strParamID):
        strClause = "belong_app_task_name_id=%d and param_id='%s'" % (iBelongAppTaskNameID, strParamID)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_result_param_block.s_strTableName,
                                                                   "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID
