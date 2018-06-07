# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_db_main_share.py
# 极限大脑－数据库－主功能共享实现
#
# start by sk. 161118

from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc
import pymysql
import pandas as pd

# 主数据库连接实现类
# start by sk, 161118
class CSkLBDB_MainConn:
    def __init__(self):
        self.s_DbConn = None

    def __del__(self):
        self.CloseConnection()

    def ReConnect(self, strHost, iPort, strUserName, strPasswd, strDatabase):
        strHost = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strHost)
        strUserName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strUserName)
        strPasswd = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPasswd)
        strDatabase = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDatabase)

        self.CloseConnection()
        self.s_DbConn = CSkLBDB_MainConn.__ExecPyMysqlConnect(strHost, iPort, strUserName, strPasswd, strDatabase)

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
# #######################################################
class CSkLBDB_CommFuncShare:
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 获得字段最大值
    # start by sk. 161121
    @staticmethod
    def GetMaxValue( dbConn, strTable, strField):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)

        iRetValue = 0  # 初始化

        strMaxQueryField = "max(" + strField + ")"
        strQuery = "select "+strMaxQueryField+" from " + strTable
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
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
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        iRetValue = 0  # 初始化

        strMaxQueryField = "min(" + strField + ")"
        strQuery = "select "+strMaxQueryField+" from " + strTable
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
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
    def GetRecCount(dbConn, strTable, strClause=''):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)

        iRetCount = 0  # 初始化
        strQuery = "select count(*) from " + strTable
        if( strClause and ( len(strClause)> 0)):
            strQuery = strQuery + " where " + strClause
        recFrame = pd.read_sql_query(strQuery, dbConn)  # 转成DataFrame
        recCount = len(recFrame)  # 记录个数
        if (recCount > 0):
            iRetCount = recFrame["count(*)"][0]
        return iRetCount

    # 读取记录某个字段：根据输入条件，读取记录某个字段的值
    # start by sk, 161121
    @staticmethod
    def ReadField_Single_WithClause(dbConn, strTable, strField, strClause):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)

        objRetFieldValue = None

        strQueryReply = "select " + strField + " from " + strTable + " where " + strClause
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            objRetFieldValue = recFrameReply[strField][0]
        return objRetFieldValue

    # 读取记录某个字段多个值：根据输入条件
    # start by sk, 161121
    @staticmethod
    def ReadField_Array_WithClause(dbConn, strTable, strField, strClause, bExecCommit=True):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)

        objRetFieldArray = list()

        strQueryReply = "select " + strField + " from " + strTable + " where " + strClause
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
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
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)

        objRetFieldArray = list()

        strQueryReply = "select " + strField + " from " + strTable + " where " + strClause + " limit " + str(iLimitCount)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
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
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)

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
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
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
    def ExecDeleteFrom( dbConn, strTable, strField, strValue):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        strValue = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue)

        strClause = strField + "='" + strValue + "'"
        strModifySQL = "delete from "+ strTable + " where " + strClause
        deleteCur = dbConn.cursor()
        deleteCur.execute(strModifySQL)
        deleteCur.close()
        dbConn.commit()  # 确认更新记录

    # 执行修改时间类型的字段内容，条件参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField_To_DateTime( dbConn, strTable, strTimeField, dateTimeValue, strClauseField, strClauseValue):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strTimeField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTimeField)
        strClauseField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClauseField)
        strClauseValue = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClauseValue)

        strClause = strClauseField + "='" + strClauseValue + "'"
        strModifyRecSameID = "update " + strTable + " set " + strTimeField + "=CAST('" + dateTimeValue.strftime("%Y-%m-%d %H:%M:%S") \
                + "' as datetime) where " + strClause
        updateCur = dbConn.cursor()
        updateCur.execute( strModifyRecSameID)
        updateCur.close()
        dbConn.commit() #确认更新记录

    # 执行修改字段内容，一个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField1( dbConn, strTable, strClause, strField1, strValue1):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)

        strSetField = strField1 + "='" + strValue1 + "'"
        strModifySQL = "update " + strTable + " set " + strSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，两个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField2( dbConn, strTable, strClause, strField1, strValue1, strField2, strValue2):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)

        strSetField1 = strField1 + "='" + strValue1 + "'"
        strSetField2 = strField2 + "='" + strValue2 + "'"
        strTotalSetField = strSetField1 + "," + strSetField2
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，三个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField3( dbConn, strTable, strClause, strField1, strValue1, strField2, strValue2, strField3, strValue3):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)

        strSetField1 = strField1 + "='" + strValue1 + "'"
        strSetField2 = strField2 + "='" + strValue2 + "'"
        strSetField3 = strField3 + "='" + strValue3 + "'"
        strTotalSetField = strSetField1 + "," + strSetField2 + "," + strSetField3
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，4个字段参数
    # start by sk, 170111
    @staticmethod
    def ExecUpdateRecField4( dbConn, strTable, strClause, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4, strValue4):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strClause = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strClause)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)
        strField4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField4)
        strValue4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue4)

        strSetField1 = strField1 + "='" + strValue1 + "'"
        strSetField2 = strField2 + "='" + strValue2 + "'"
        strSetField3 = strField3 + "='" + strValue3 + "'"
        strSetField4 = strField4 + "='" + strValue4 + "'"
        strTotalSetField = strSetField1 + "," + strSetField2 + "," + strSetField3 + "," + strSetField4
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        CSkLBDB_CommFuncShare.__ExecUpdateSQL( dbConn, strModifySQL)

    # 执行修改字段内容，4个字段参数
    # start by sk, 170111
    @staticmethod
    def __ExecUpdateSQL( dbConn, strUpdateSQL):
        strUpdateSQL = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strUpdateSQL)

        updateCur = dbConn.cursor()
        try:
            updateCur.execute(strUpdateSQL)
        except Exception as e:
            pass
        updateCur.close()
        dbConn.commit()  # 确认更新记录


    # 执行插入记录，两个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField2( dbConn, strTable, strField1, strValue1, strField2, strValue2):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)

        strInsertSQL="insert into " + strTable + " (" + strField1 + "," + strField2 + ") values(%s,%s)"
        # insert into table (field) values(%s)
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 执行插入记录，三个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField3( dbConn, strTable, strField1, strValue1, strField2, strValue2, strField3, strValue3):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)

        strTotalFields = "%s,%s,%s" % ( strField1, strField2, strField3)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s)"
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2, strValue3))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 执行插入记录，四个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField4( dbConn, strTable, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4, strValue4):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)
        strField4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField4)
        strValue4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue4)

        strTotalFields = "%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s)"
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2, strValue3, strValue4))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 执行插入记录，五个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField5( dbConn, strTable, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4, strValue4, strField5, strValue5):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)
        strField4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField4)
        strValue4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue4)
        strField5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField5)
        strValue5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue5)

        strTotalFields = "%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s)"
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2, strValue3, strValue4, strValue5))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 执行插入记录，六个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField6( dbConn, strTable, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4,
                             strValue4, strField5, strValue5, strField6, strValue6):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)
        strField4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField4)
        strValue4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue4)
        strField5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField5)
        strValue5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue5)
        strField6 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField6)
        strValue6 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue6)

        strTotalFields = "%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s,%s)"
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2, strValue3, strValue4, strValue5,strValue6))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 执行插入记录，七个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField7( dbConn, strTable, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4,
                             strValue4, strField5, strValue5, strField6, strValue6, strField7, strValue7):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)
        strField4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField4)
        strValue4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue4)
        strField5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField5)
        strValue5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue5)
        strField6 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField6)
        strValue6 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue6)
        strField7 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField7)
        strValue7 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue7)

        strTotalFields = "%s,%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6,strField7)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s,%s,%s)"
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2, strValue3, strValue4, strValue5, strValue6, strValue7))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 执行插入记录，八个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField8( dbConn, strTable, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4,
                             strValue4, strField5, strValue5, strField6, strValue6, strField7, strValue7, strField8, strValue8):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField1)
        strValue1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue1)
        strField2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField2)
        strValue2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue2)
        strField3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField3)
        strValue3 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue3)
        strField4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField4)
        strValue4 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue4)
        strField5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField5)
        strValue5 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue5)
        strField6 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField6)
        strValue6 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue6)
        strField7 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField7)
        strValue7 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue7)
        strField8 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField8)
        strValue8 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue8)

        strTotalFields = "%s,%s,%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6,strField7,strField8)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(%s,%s,%s,%s,%s,%s,%s,%s)"
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue1, strValue2, strValue3, strValue4, strValue5, strValue6, strValue7,strValue8))
            iRetRecID = insertCur.lastrowid
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

    # 获得UID对应的ID
    # start by sk, 161215
    @staticmethod
    def GetUID_by_RecID(dbConn, strTable, iRecID):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)

        strClause = "id=%d" % (iRecID)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause( dbConn, strTable, "unique_id", strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID

    # 获得UID对应的ID
    # start by sk, 161215
    @staticmethod
    def GetRecID_by_UID(dbConn, strTable, iUID):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)

        strClause = "unique_id=%d" % (iUID)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause( dbConn, strTable, "id", strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID

    # 获得当前最大值的UID
    # start by sk, 161215
    @staticmethod
    def GetMaxUID(dbConn, strTable):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        return CSkLBDB_CommFuncShare.GetMaxValue(dbConn, strTable, "unique_id")

    # 执行插入记录，一个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField1( dbConn, strTable, strField, strValue):
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        strValue = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strValue)

        strInsertSQL="insert into " + strTable + " (" + strField + ") values(%s)" # insert into table (field) values(%s)
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue))
            iRetRecID = insertCur.lastrowid;
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID

