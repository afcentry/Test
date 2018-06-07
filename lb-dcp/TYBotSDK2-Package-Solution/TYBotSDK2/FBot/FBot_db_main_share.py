# -*- coding:UTF-8 -*- 放到第一行标记
# FBot_db_main_share.py
# 极限大脑－天元功能机器人 - 数据库－主功能共享实现
#
# start by sk. 161118
# recopy & move to TYBotSDK2\FBotSubFunc by sk. 170407
# add GetMaxValue_Clause func by sk. 170928
# add: 更新 CSkLBDB_CommFuncShare update, insert 功能，值转换为根据实际类型进行构建合适的sql语句。极大提高查询和执行的速度
#   by sk. 171002
# 增加数据缓冲功能。 by sk. 171016
# 增加 更新，插入，查询的 批执行。 by sk. 180311

import pymysql
import pandas as pd
import numpy as np

g_lastSqlConnErrorDict={}   # 保存上次错误连接信息

class CDbConnOpBuffDict:
    def __init__(self):
        self.s_DbConn_Dict = {}  # 每个数据库链接的字典。dbconn -- 单元
        pass

    # 数据库操作的缓冲
    # start by sk. 171016
    class CDbOpBuffDict:

        # 每个表的操作单元
        class COpUnit:

            # 存储每个字段缓冲的操作类
            class CEachFieldClauseUnit:
                def __init__(self):
                    self.s_Clause_Value_Dict = {}  # 条件，值对应的字典
                    pass

                # 查询缓冲值
                def QueryValue(self, strClause):
                    retValue = None
                    bValueExist = False
                    if (strClause in self.s_Clause_Value_Dict.keys()):
                        bValueExist = True
                        retValue = self.s_Clause_Value_Dict[strClause]
                    return bValueExist, retValue

                # 设置缓冲值
                def SetValue(self, strClause, getValue):
                    iMaxCountValue = 100000
                    # 如果值超过10万个，重新设置
                    if( len(self.s_Clause_Value_Dict) > iMaxCountValue):
                        self.s_Clause_Value_Dict = {}

                    if (strClause not in self.s_Clause_Value_Dict.keys()):
                        self.s_Clause_Value_Dict[strClause] = getValue
                    else:
                        oldValue = self.s_Clause_Value_Dict[strClause]
                        if( oldValue != getValue):
                            self.s_Clause_Value_Dict[strClause] = getValue
                    pass

            # #########################
            # #########################
            def __init__(self):
                self.s_FieldBuffDict = {}  # 条件 = 值
                pass

            # 查询缓冲值
            def QueryValue(self, strField, strClause):
                bValueExist, retValue = False, None

                if (strField in self.s_FieldBuffDict.keys()):
                    fieldUnit = self.s_FieldBuffDict[strField]
                    bValueExist, retValue = fieldUnit.QueryValue(strClause)

                return bValueExist, retValue

            # 设置缓冲值
            def SetValue(self, strField, strClause, getValue):
                if (strField not in self.s_FieldBuffDict.keys()):
                    newUnit = CDbConnOpBuffDict.CDbOpBuffDict.COpUnit.CEachFieldClauseUnit()
                    self.s_FieldBuffDict[strField] = newUnit
                else:
                    newUnit = self.s_FieldBuffDict[strField]

                if(newUnit):
                    newUnit.SetValue(strClause, getValue)
                pass


        # #########################
        # #########################
        # 初始化
        def __init__(self):
            self.s_TableDict = {}  # 每个表的字典。表名 -- 单元
            pass

        # 查询缓冲值
        def QueryValue(self, strTable, strField, strClause):
            bValueExist, retValue = False, None
            if( strTable in self.s_TableDict.keys()):
                tableUnit = self.s_TableDict[strTable]
                bValueExist, retValue = tableUnit.QueryValue(strField, strClause)

            return bValueExist, retValue

        # 设置缓冲值
        def SetValue(self, strTable, strField, strClause, getValue):
            if (strTable not in self.s_TableDict.keys()):
                newUnit = CDbConnOpBuffDict.CDbOpBuffDict.COpUnit()
                self.s_TableDict[strTable] = newUnit
            else:
                newUnit = self.s_TableDict[strTable]

            if( newUnit):
                newUnit.SetValue(strField, strClause, getValue)
            pass

    # 查询缓冲值
    def QueryValue(self, dbConn, strTable, strField, strClause):
        bValueExist, retValue = False, None
        if (dbConn in self.s_DbConn_Dict.keys()):
            tableUnit = self.s_DbConn_Dict[dbConn]
            bValueExist, retValue = tableUnit.QueryValue(strTable, strField, strClause)

        return bValueExist, retValue

    # 设置缓冲值
    def SetValue(self, dbConn, strTable, strField, strClause, getValue):
        if (dbConn not in self.s_DbConn_Dict.keys()):
            newUnit = CDbConnOpBuffDict.CDbOpBuffDict()
            self.s_DbConn_Dict[dbConn] = newUnit
        else:
            newUnit = self.s_DbConn_Dict[dbConn]

        if (newUnit):
            newUnit.SetValue(strTable, strField, strClause, getValue)
        pass


g_OpDbQuery_Buff_Mang = CDbConnOpBuffDict()   # 操作缓冲管理


# 主数据库连接实现类
# start by sk, 161118
class CSkLBDB_MainConn:
    s_iExecDbType = 0
    s_iDbType_SkBotDB = 1
    s_iDbType_Orig_10_29 = 2
    s_iDbType_Dest_ty2_lb1_d2 = 3
    s_iDbType_Orig_16_11_d1 = 4
    s_iDbType_Orig_real_host_16_11_d1 = 5
    s_iDbType_Orig_real_host_16_12_d2 = 6
    s_iDbType_Orig_real_host_16_13_d3 = 7
    s_iDbType_Orig_real_host_16_122_d22 = 8
    s_iDbType_Orig_Local_test = 9
    s_iDbType_Orig_Local_vm_166_130 = 10
    s_iDbType_152_21_Ali_Mid_DB = 11
    s_iDbType_13_159_equ_153_21_Ali_Mid_DB = 12
    s_iDbType_F1_13_21 = 13

    def __init__(self, iType=0):
        self.s_DbConn = None
        self.s_iExecDbType = iType

    def __del__(self):
        self.CloseConnection()

    def ReConnect(self, ustrHost, iPort, ustrUser, ustrPass, ustrDatabase):
        self.CloseConnection()

        self.s_DbConn = CSkLBDB_MainConn.__ExecPyMysqlConnect(ustrHost, iPort, ustrUser, ustrPass, ustrDatabase)

    def CloseConnection(self):
        if (self.s_DbConn != None):
            self.s_DbConn.close()
            self.s_DbConn = None

    @staticmethod
    def __ExecPyMysqlConnect(strHost, iPort, strUser, strPasswd, strDatabase):
        retDbConn = pymysql.connect(host=strHost, port=iPort, user=strUser, passwd=strPasswd, db=strDatabase, charset="utf8")
        return retDbConn

# #######################################################
# 数据库共享功能实现
#   执行插入的功能  ExecInsertRecField1,2,3,4,5
#   执行修改字段内容 ExecUpdateRecField1,2,3,4,5
# start by sk, 161121
# 更新 update, insert 功能，值转换为根据实际类型进行构建合适的sql语句。极大提高查询和执行的速度
#   by sk. 171002
# 增加 更新，插入，查询的 批执行。 by sk. 180311
# #######################################################
class CSkLBDB_CommFuncShare:
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 数据库缓冲-查询值
    # start by sk. 171016
    @staticmethod
    def DbQueryBuff_QueryValue(dbConn, strTable, strField, strClause):
        bValueExist, getValue = g_OpDbQuery_Buff_Mang.QueryValue(dbConn, strTable, strField, strClause)
        return bValueExist, getValue
        pass

    # 数据库缓冲-设置值
    # start by sk. 171016
    @staticmethod
    def DbQueryBuff_SetValue(dbConn, strTable, strField, strClause, getValue):
        g_OpDbQuery_Buff_Mang.SetValue(dbConn, strTable, strField, strClause, getValue)
        pass

    # 获得上次数据库错误的dict
    # start by sk. 170904
    @staticmethod
    def RetriveLastDbConnErrorDict():
        global g_lastSqlConnErrorDict
        retValue = g_lastSqlConnErrorDict
        g_lastSqlConnErrorDict = {}
        return retValue

    # 统一执行命令，以便可以捕获错误
    # start by sk. 170904
    @staticmethod
    def SafeExecPandaSQLQuery( dbConn, strQuery):
        recFrame = {}
        try:
            dbConn.ping()
            recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
        except Exception as e:
            global g_lastSqlConnErrorDict
            print('db reqd-sql-query [%s] error. msg:[%s]'%(strQuery, str(e)))
            g_lastSqlConnErrorDict[dbConn] = e
        return recFrame

    # 执行修改字段内容，4个字段参数
    # start by sk, 170111
    # deveLop by sk. 170904
    @staticmethod
    def __ExecUpdateSQL( dbConn, strUpdateSQL):
        try:
            dbConn.ping()
            updateCur = dbConn.cursor()
            updateCur.execute(strUpdateSQL)
            updateCur.close()
            dbConn.commit()  # 确认更新记录
        except Exception as e:
            global g_lastSqlConnErrorDict
            print('db exec-update-sql [%s] error. msg:[%s]'%(strUpdateSQL, str(e)))
            g_lastSqlConnErrorDict[dbConn] = e
            pass

    # 安全执行sql命令
    # start by sk, 170904
    @staticmethod
    def __SafeExecInsertSQL(dbConn, strInsertSQL, *args):
        iExecRetRecID = 0
        try:
            dbConn.ping()
            insertCur = dbConn.cursor()
            insertCur.execute(strInsertSQL, (args))
            iExecRetRecID = insertCur.lastrowid;
            dbConn.commit()
            insertCur.close()
        except Exception as e:
            global g_lastSqlConnErrorDict
            print('db exec-insert-sql [%s] error. msg:[%s]'%(strInsertSQL, str(e)))
            iExecRetRecID = 0
            g_lastSqlConnErrorDict[dbConn] = e
        return iExecRetRecID

    # 获得字段最大值
    # start by sk. 161121
    @staticmethod
    def GetMaxValue( dbConn, strTable, strField):
        iRetValue = 0  # 初始化

        strMaxQueryField = "max(" + strField + ")"
        strQuery = "select "+strMaxQueryField+" from " + strTable
        recFrame = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQuery)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetValue = recFrame[strMaxQueryField][0]
            if( not iRetValue):
                iRetValue = 0
        else:
            iRetValue = 0
        return iRetValue


    # 根据条件，获得字段最大值
    # start by sk. 170928
    @staticmethod
    def GetMaxValue_Clause( dbConn, strTable, strField, strClause):
        iRetValue = 0  # 初始化

        strMaxQueryField = "max(" + strField + ")"
        strQuery = "select "+strMaxQueryField+" from " + strTable + ' where ' + strClause
        recFrame = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQuery)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetValue = recFrame[strMaxQueryField][0]
            if( not iRetValue):
                iRetValue = 0
        else:
            iRetValue = 0
        return iRetValue

    # 获得字段最大值
    # start by sk. 161121
    @staticmethod
    def GetMinValue( dbConn, strTable, strField):
        iRetValue = 0  # 初始化

        strMaxQueryField = "min(" + strField + ")"
        strQuery = "select "+strMaxQueryField+" from " + strTable
        recFrame = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQuery)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetValue = recFrame[strMaxQueryField][0]
            if( not iRetValue):
                iRetValue = 0
        else:
            iRetValue = 0
        return iRetValue

    # 获得问候字符串记录数量
    # start by sk. 161118
    @staticmethod
    def GetRecCount(dbConn, strTable, strClause=None):
        iRetCount = 0  # 初始化
        strQuery = "select count(*) from " + strTable
        if( strClause and ( len(strClause)> 0)):
            strQuery = strQuery + " where " + strClause
        recFrame = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQuery)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetCount = recFrame["count(*)"][0]
        return iRetCount

    # 读取记录某个字段：根据输入条件，读取记录某个字段的值
    # start by sk, 161121
    @staticmethod
    def ReadField_Single_WithClause(dbConn, strTable, strField, strClause, bUseDbOpBuff=False):
        objRetFieldValue = None

        strQueryReply = "select " + strField + " from " + strTable + " where " + strClause

        bExecSQLQuery = True
        if( bUseDbOpBuff):
            bValueExist, getValue = CSkLBDB_CommFuncShare.DbQueryBuff_QueryValue(dbConn, strTable, strField,
                                                                                 strClause)
            if (bValueExist):
                objRetFieldValue = getValue
                bExecSQLQuery = False

        if( bExecSQLQuery):
            recFrameReply = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQueryReply)  # 转成DataFrame
            recCount = len(recFrameReply)  # 记录个数
            if( recCount > 0):
                objRetFieldValue = recFrameReply[strField][0]

            if( objRetFieldValue):
                # 存放到数据库缓冲
                if (bUseDbOpBuff):
                    CSkLBDB_CommFuncShare.DbQueryBuff_SetValue(dbConn, strTable, strField, strClause, objRetFieldValue)

        return objRetFieldValue

    # 读取记录某个字段多个值：根据输入条件
    # start by sk, 161121
    @staticmethod
    def ReadField_Array_WithClause(dbConn, strTable, strField, strClause, bExecCommit=True):
        objRetFieldArray = list()

        strQueryReply = "select " + strField + " from " + strTable + " where " + strClause
        recFrameReply = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQueryReply)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        for iIndex in range(recCount):
            objFieldValue = recFrameReply[strField][iIndex]
            objRetFieldArray.append( objFieldValue)
        if( bExecCommit):
            dbConn.commit()
        return objRetFieldArray

    # 读取记录某个字段多个值：根据输入条件，和最大输出数
    # start by sk, 161124
    @staticmethod
    def ReadField_Array_WithClause_limit(dbConn, strTable, strField, strClause, iLimitCount, bExecCommit=True):
        objRetFieldArray = list()

        strQueryReply = "select " + strField + " from " + strTable + " where " + strClause + " limit " + str(iLimitCount)
        recFrameReply = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQueryReply)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        for iIndex in range(recCount):
            objFieldValue = recFrameReply[strField][iIndex]
            objRetFieldArray.append( objFieldValue)
        if( bExecCommit):
            dbConn.commit()
        return objRetFieldArray

    # 读取记录多个字段多个值：根据输入条件，和最大输出数
    # start by sk, 161124
    @staticmethod
    def Read3Fields_Array_WithClause_limit(dbConn, strTable, strField1, strField2, strField3, strClause, iLimitCount, bExecCommit=True):
        objRetField1Array = []
        objRetField2Array = []
        objRetField3Array = []
        strCombFields = strField1
        if( len(strField2)> 0):
            strCombFields += "," + strField2
        if( len(strField3)> 0):
            strCombFields += "," + strField3

        strLimitClause = ""
        if( iLimitCount > 0):
            strLimitClause = " limit %d" % (iLimitCount)

        strQueryReply = "select " + strCombFields + " from " + strTable + " where " + strClause + strLimitClause
        recFrameReply = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strQueryReply)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        for iIndex in range(recCount):
            objFieldValue = recFrameReply[strField1][iIndex]
            objRetField1Array.append( objFieldValue)
            if (len(strField2) > 0):
                objFieldValue = recFrameReply[strField2][iIndex]
                objRetField2Array.append(objFieldValue)
            if (len(strField3) > 0):
                objFieldValue = recFrameReply[strField3][iIndex]
                objRetField3Array.append(objFieldValue)
        if( bExecCommit):
            dbConn.commit()
        return objRetField1Array, objRetField2Array, objRetField3Array

    # 执行删除的记录命令
    # start by sk, 161121
    @staticmethod
    def ExecDeleteFrom( dbConn, strTable, strField, pValue):
        strValue = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue)
        strClause = '%s=%s' %(strField, strValue)

        strModifySQL = "delete from "+ strTable + " where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL(dbConn, strModifySQL)
        '''
        deleteCur = dbConn.cursor()
        deleteCur.execute(strModifySQL)
        deleteCur.close()
        dbConn.commit()  # 确认更新记录
        '''

    # 执行修改时间类型的字段内容，条件参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField_To_DateTime( dbConn, strTable, strTimeField, dateTimeValue, strClauseField, pClauseValue):
        strValue = CSkLBDB_CommFuncShare.__ClauseValueStr(pClauseValue)
        strClause = '%s=%s' %(strClauseField, strValue)

        strModifyRecSameID = "update " + strTable + " set " + strTimeField + "=CAST('" + dateTimeValue.strftime("%Y-%m-%d %H:%M:%S") \
                + "' as datetime) where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL(dbConn, strModifyRecSameID)
        '''
        updateCur = dbConn.cursor()
        updateCur.execute( strModifyRecSameID)
        updateCur.close()
        dbConn.commit() #确认更新记录
        '''

    # 执行修改字段内容，一个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField1( dbConn, strTable, strClause, strField1, pValue1):
        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1)
        strSetField1 = '%s=%s' %(strField1, strValue1)

        strTotalSetField = strSetField1

        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，两个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField2( dbConn, strTable, strClause, strField1, pValue1, strField2, pValue2):
        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1)
        strSetField1 = '%s=%s' %(strField1, strValue1)

        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2)
        strSetField2 = '%s=%s' %(strField2, strValue2)

        strTotalSetField = strSetField1 + "," + strSetField2
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，三个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField3( dbConn, strTable, strClause, strField1, pValue1, strField2, pValue2, strField3, pValue3):
        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1)
        strSetField1 = '%s=%s' %(strField1, strValue1)

        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2)
        strSetField2 = '%s=%s' %(strField2, strValue2)

        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3)
        strSetField3 = '%s=%s' %(strField3, strValue3)

        strTotalSetField = strSetField1 + "," + strSetField2 + "," + strSetField3
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，4个字段参数
    # start by sk, 170111
    @staticmethod
    def ExecUpdateRecField4( dbConn, strTable, strClause, strField1, pValue1, strField2, pValue2, strField3, pValue3, strField4, pValue4):
        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1)
        strSetField1 = '%s=%s' %(strField1, strValue1)

        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2)
        strSetField2 = '%s=%s' %(strField2, strValue2)

        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3)
        strSetField3 = '%s=%s' %(strField3, strValue3)

        strValue4 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue4)
        strSetField4 = '%s=%s' %(strField4, strValue4)

        strTotalSetField = strSetField1 + "," + strSetField2 + "," + strSetField3 + "," + strSetField4
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)


    # 执行查询，返回DATAFrame
    #  strTable --- 表名
    #  strNeedQueryFields --- 需要查询的字段名，例如： * 或者 field1, field2
    #  strFieldsNameArray --- 字段名字队列，如：['field1', 'field2']
    #  strValuesLineArray --- 每一行都是格式化好的值字符串队列，需要包括括号，例如 ["('field_value1', 1)", "('field_value2', 2)"]
    #       -返回值： DataFrame
    #  for example: ExecBatchInsertRecFieldArray(dbConn, 'table', '*', ['field1','field2'], ["('strFieldValue1', 1)", "('strFieldValue2', 2)"]
    # start by sk, 180311
    @staticmethod
    def ExecBatchQueryRecFieldArray( dbConn, strTable, strNeedQueryFields, strFieldsNameArray, strValuesLineArray, iLimitCount):
        strFullFieldValue = ','.join(strValuesLineArray)
        strFieldsName = ','.join(strFieldsNameArray)
        strLimit = ''
        if(iLimitCount > 0):
            strLimit = ' limit %d' % (iLimitCount)

        strFullQuery = "select %s from %s where (%s) in (%s)%s" % (strNeedQueryFields, strTable, strFieldsName,
                                                                           strFullFieldValue, strLimit)

        recFrameReply = CSkLBDB_CommFuncShare.SafeExecPandaSQLQuery(dbConn, strFullQuery)
        return recFrameReply

    # 执行批量插入
    #  strTable --- 表名
    #  strFieldsNameArray --- 字段名字队列，如：['field1', 'field2']
    #  strValuesLineArray --- 每一行都是格式化好的值字符串队列，需要包括括号，例如 ["('field_value1', 1)", "('field_value2', 2)"]
    #       -返回值： 无
    #  for example: ExecBatchInsertRecFieldArray(dbConn, 'table', ['field1','field2'], ["('strFieldValue1', 1)", "('strFieldValue2', 2)"]
    # start by sk, 180311
    @staticmethod
    def ExecBatchInsertRecFieldArray( dbConn, strTable, strFieldsNameArray, strValuesLineArray):
        strFullFieldValue = ','.join(strValuesLineArray)
        strFieldsName = ','.join(strFieldsNameArray)

        strFullInsert = "insert into %s (%s) VALUES %s;" % (strTable, strFieldsName, strFullFieldValue)
        CSkLBDB_CommFuncShare.__ExecUpdateSQL(dbConn, strFullInsert)

    # 执行插入记录，两个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField2( dbConn, strTable, strField1, pValue1, strField2, pValue2):
        strInsertSQL="insert into " + strTable + " (" + strField1 + "," + strField2 + ") values(%s,%s)"
        # insert into table (field) values(%s)
        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2)
        return iRetRecID

    # 执行插入记录，三个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField3( dbConn, strTable, strField1, pValue1, strField2, pValue2, strField3, pValue3):
        strTotalFields = "%s,%s,%s" % ( strField1, strField2, strField3)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s)"

        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)
        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2, strValue3)
        return iRetRecID

    # 执行插入记录，四个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField4( dbConn, strTable, strField1, pValue1, strField2, pValue2, strField3, pValue3, strField4,
                             pValue4):
        strTotalFields = "%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s)"

        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)
        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3,False)
        strValue4 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue4,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2, strValue3, strValue4)
        return iRetRecID

    # 执行插入记录，五个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField5( dbConn, strTable, strField1, pValue1, strField2, pValue2, strField3, pValue3, strField4,
                             pValue4, strField5, pValue5):
        strTotalFields = "%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s)"

        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)
        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3,False)
        strValue4 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue4,False)
        strValue5 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue5,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2, strValue3, strValue4, strValue5)
        return iRetRecID

    # 执行插入记录，六个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField6( dbConn, strTable, strField1, pValue1, strField2, pValue2, strField3, pValue3, strField4,
                             pValue4, strField5, pValue5, strField6, pValue6):
        strTotalFields = "%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s,%s)"

        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)
        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3,False)
        strValue4 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue4,False)
        strValue5 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue5,False)
        strValue6 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue6,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2, strValue3,
                                                              strValue4, strValue5, strValue6)
        return iRetRecID

    # 执行插入记录，七个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField7( dbConn, strTable, strField1, pValue1, strField2, pValue2, strField3, pValue3, strField4,
                             pValue4, strField5, pValue5, strField6, pValue6, strField7, pValue7):
        strTotalFields = "%s,%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6,strField7)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s,%s,%s)"

        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)
        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3,False)
        strValue4 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue4,False)
        strValue5 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue5,False)
        strValue6 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue6,False)
        strValue7 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue7,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2, strValue3,
                                                              strValue4, strValue5, strValue6, strValue7)
        return iRetRecID

    # 执行插入记录，八个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField8( dbConn, strTable, strField1, pValue1, strField2, pValue2, strField3, pValue3, strField4,
                             pValue4, strField5, pValue5, strField6, pValue6, strField7, pValue7, strField8, pValue8):
        strTotalFields = "%s,%s,%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6,strField7,strField8)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s,%s,%s,%s)"

        strValue1 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue1,False)
        strValue2 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue2,False)
        strValue3 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue3,False)
        strValue4 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue4,False)
        strValue5 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue5,False)
        strValue6 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue6,False)
        strValue7 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue7,False)
        strValue8 = CSkLBDB_CommFuncShare.__ClauseValueStr(pValue8,False)

        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue1, strValue2, strValue3,
                                                              strValue4, strValue5, strValue6, strValue7,strValue8)
        return iRetRecID

    # 获得UID对应的ID
    # start by sk, 161215
    # 增加数据缓冲功能。 by sk. 171016
    @staticmethod
    def GetUID_by_RecID(dbConn, strTable, iRecID, bUseDbOpBuff=False):
        strClause = "id=%d" % (iRecID)

        strFieldUniqueID = 'unique_id'
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, strTable, strFieldUniqueID, strClause,
                                                                   bUseDbOpBuff=bUseDbOpBuff)
        if (not iRetID):
            iRetID = 0

        '''        
        bExecSQLQuery = True
        if( bUseDbOpBuff):
            bValueExist, getValue = CSkLBDB_CommFuncShare.DbQueryBuff_QueryValue( strTable, strFieldUniqueID, strClause)
            if( bValueExist):
                iRetID = getValue
                bExecSQLQuery = False
            
        if( bExecSQLQuery):
            iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause( dbConn, strTable, strFieldUniqueID, strClause)
            if (not iRetID):
                iRetID = 0
                
            # 存放到数据库缓冲
            if( bUseDbOpBuff):
                if( iRetID):
                    CSkLBDB_CommFuncShare.DbQueryBuff_SetValue(strTable, strFieldUniqueID, strClause, iRetID)
        '''
        return iRetID

    # 获得UID对应的ID
    # start by sk, 161215
    @staticmethod
    def GetRecID_by_UID(dbConn, strTable, iUID, bUseDbOpBuff=False):
        strClause = "unique_id=%d" % (iUID)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause( dbConn, strTable, "id", strClause, bUseDbOpBuff=bUseDbOpBuff)
        if (not iRetID):
            iRetID = 0
        return iRetID

    # 获得当前最大值的UID
    # start by sk, 161215
    @staticmethod
    def GetMaxUID(dbConn, strTable):
        return CSkLBDB_CommFuncShare.GetMaxValue(dbConn, strTable, "unique_id")

    # 执行插入记录，一个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField1( dbConn, strTable, strField, strValue):
        strInsertSQL="insert into " + strTable + " (" + strField + ") values(%s)" # insert into table (field) values(%s)
        iRetRecID = CSkLBDB_CommFuncShare.__SafeExecInsertSQL(dbConn, strInsertSQL, strValue)
        return iRetRecID

    # 构建条件字符串. 根据值类型，自动加引号或者int值
    #  如果需要字符串引号，则bStrQuota=True，这个需要用在update等的条件查询中。而insert不用，因为是值变量绑定
    # start by sk. 170102
    @staticmethod
    def __ClauseValueStr(fieldValue, bStrQuota=True):
        vluType = type(fieldValue)
        if( vluType == str):
            if( bStrQuota):
                strFieldValue = "'%s'" % (fieldValue)
            else:
                strFieldValue = fieldValue

        elif( vluType == bytes):
            strUnicodeFieldValue = fieldValue
            if isinstance(strUnicodeFieldValue,bytes):
                strUnicodeFieldValue=strUnicodeFieldValue.decode()
            if( bStrQuota):
                strFieldValue = "'%s'" % (strUnicodeFieldValue)
            else:
                strFieldValue = strUnicodeFieldValue

        elif( (vluType == int) or (vluType == np.int64) or (vluType == np.int32) or (vluType == np.int16) or
                  (vluType == np.int) or (vluType == np.int8)):
            strFieldValue = "%d" % (fieldValue)
        elif ( (vluType == np.uint64) or (vluType == np.uint32) or (vluType == np.uint16) or
                  (vluType == np.uint) or (vluType == np.uint8)):
            strFieldValue = "%d" % (fieldValue)
        else:
            strFieldValue = ''
            print('cannot convert type into express!!!')
        return strFieldValue