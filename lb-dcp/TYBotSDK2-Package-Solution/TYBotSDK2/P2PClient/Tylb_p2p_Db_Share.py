# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_p2p_DB_Share.py 数据库功能共享实现
#
# start by sk. 170128
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式

import sqlite3
import pandas as pd

# tylb的数据库功能实现，基本连接对象
# start by sk. 170128
class CTYLB_SQLite_DB_Conn:

    def __init__(self, strFileName):
        self.s_dbConn = None
        self.s_dbConn = sqlite3.connect( strFileName, check_same_thread=False)
        pass

    def __del__(self):
        self.close()
        pass

    def close(self):
        if( self.s_dbConn):
            self.s_dbConn.close()
            self.s_dbConn = None

    # 执行sql语句
    # start by sk. 170128
    def ExecSingleSQL(self, strSQL, bCommit=True):
        execCursor = self.s_dbConn.cursor()
        execCursor.execute(strSQL)

# #######################################################
# 数据库共享功能实现 CSkLBDB_CommFuncShare
#   执行插入的功能  ExecInsertRecField1,2,3,4,5
#   执行修改字段内容 ExecUpdateRecField1,2,3,4,5
# start by sk, 161121
# copy into tylb_p2p. by sk. 170128
# #######################################################
class CTYLB_DB_Lite_CommFuncShare:
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 创建表
    #  sample :
    #  code
    # start by sk. 170128
    @staticmethod
    def CreateTable( dbConn, strTableName, strFields, indexArray):
        strTablePart = 'create table if not exists %s' % (strTableName)
        strFull = '%s (%s);' % (strTablePart, strFields)
        execCursor = dbConn.cursor()
        execCursor.execute( strFull)

        for eachIndexComb in indexArray:
            strIndex = 'CREATE INDEX if not exists %s ON %s (%s);' % (eachIndexComb[0], strTableName, eachIndexComb[1])
            execCursor.execute( strIndex)
        iIndexCount = len(indexArray)

        dbConn.commit()

    # 获得字段最大值
    # start by sk. 161121
    @staticmethod
    def GetMaxValue( dbConn, strTable, strField):
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
    def GetRecCount(dbConn, strTable, strClause=None):
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
    # 增加通用的删除执行
    @staticmethod
    def ExecDeleteFrom( dbConn, strTable, strField, strValue):
        if( strField or strValue):
            strClause = " where %s='%s'" % (strField, strValue)
        else:
            strClause = ''
        strModifySQL = "delete from "+ strTable + strClause
        deleteCur = dbConn.cursor()
        deleteCur.execute(strModifySQL)
        deleteCur.close()
        dbConn.commit()  # 确认更新记录

    # 执行修改时间类型的字段内容，条件参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField_To_DateTime( dbConn, strTable, strTimeField, dateTimeValue, strClauseField, strClauseValue):
        strClause = strClauseField + "='" + strClauseValue + "'"
        # strModifyRecSameID = "update " + strTable + " set " + strTimeField + "=CAST('" + dateTimeValue.strftime("%Y-%m-%d %H:%M:%S") \
        #         + "' as datetime) where " + strClause
        strDateTime = dateTimeValue.strftime('%Y-%m-%dT%H:%M:%SZ')
        strModifyRecSameID = "update %s set %s=datetime('%s') where %s" % (strTable, strTimeField, strDateTime, strClause)
        updateCur = dbConn.cursor()
        updateCur.execute(strModifyRecSameID)
        # updateCur.execute( strModifyRecSameID, dateTimeValue)
        updateCur.close()
        dbConn.commit() #确认更新记录

    # 执行修改字段内容，一个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField1( dbConn, strTable, strClause, strField1, strValue1):
        strSetField = strField1 + "='" + strValue1 + "'"
        strModifySQL = "update " + strTable + " set " + strSetField + "  where " + strClause
        updateCur = dbConn.cursor()
        updateCur.execute(strModifySQL)
        updateCur.close()
        dbConn.commit()  # 确认更新记录

    # 执行修改字段内容，两个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField2( dbConn, strTable, strClause, strField1, strValue1, strField2, strValue2):
        strSetField1 = strField1 + "='" + strValue1 + "'"
        strSetField2 = strField2 + "='" + strValue2 + "'"
        strTotalSetField = strSetField1 + "," + strSetField2
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        updateCur = dbConn.cursor()
        updateCur.execute(strModifySQL)
        updateCur.close()
        dbConn.commit()  # 确认更新记录

    # 执行修改字段内容，三个字段参数
    # start by sk, 161121
    @staticmethod
    def ExecUpdateRecField3( dbConn, strTable, strClause, strField1, strValue1, strField2, strValue2, strField3, strValue3):
        strSetField1 = strField1 + "='" + strValue1 + "'"
        strSetField2 = strField2 + "='" + strValue2 + "'"
        strSetField3 = strField3 + "='" + strValue3 + "'"
        strTotalSetField = strSetField1 + "," + strSetField2 + "," + strSetField3
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        updateCur = dbConn.cursor()
        updateCur.execute(strModifySQL)
        updateCur.close()
        dbConn.commit()  # 确认更新记录

    # 执行修改字段内容，4个字段参数
    # start by sk, 170111
    @staticmethod
    def ExecUpdateRecField4( dbConn, strTable, strClause, strField1, strValue1, strField2, strValue2, strField3, strValue3, strField4, strValue4):
        strSetField1 = strField1 + "='" + strValue1 + "'"
        strSetField2 = strField2 + "='" + strValue2 + "'"
        strSetField3 = strField3 + "='" + strValue3 + "'"
        strSetField4 = strField4 + "='" + strValue4 + "'"
        strTotalSetField = strSetField1 + "," + strSetField2 + "," + strSetField3 + "," + strSetField4
        strModifySQL = "update " + strTable + " set " + strTotalSetField + "  where " + strClause
        updateCur = dbConn.cursor()
        updateCur.execute(strModifySQL)
        updateCur.close()
        dbConn.commit()  # 确认更新记录

    # 执行插入记录，两个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField2( dbConn, strTable, strField1, strValue1, strField2, strValue2):
        strInsertSQL="insert into " + strTable + " (" + strField1 + "," + strField2 + ") values(?,?)"
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
        strTotalFields = "%s,%s,%s" % ( strField1, strField2, strField3)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(?,?,?)"
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
        strTotalFields = "%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(?,?,?,?)"
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
        strTotalFields = "%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(?,?,?,?,?)"
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
        strTotalFields = "%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(?,?,?,?,?,?)"
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
        strTotalFields = "%s,%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6,strField7)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(?,?,?,?,?,?,?)"
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
        strTotalFields = "%s,%s,%s,%s,%s,%s,%s,%s" % ( strField1, strField2, strField3, strField4, strField5,strField6,strField7,strField8)
        strInsertSQL="insert into " + strTable + " (" + strTotalFields + ") values(?,?,?,?,?,?,?,?)"
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
        strClause = "id=%d" % (iRecID)
        iRetID = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause( dbConn, strTable, "unique_id", strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID

    # 获得UID对应的ID
    # start by sk, 161215
    @staticmethod
    def GetRecID_by_UID(dbConn, strTable, iUID):
        strClause = "unique_id=%d" % (iUID)
        iRetID = CTYLB_DB_Lite_CommFuncShare.ReadField_Single_WithClause( dbConn, strTable, "id", strClause)
        if (not iRetID):
            iRetID = 0
        return iRetID

    # 获得当前最大值的UID
    # start by sk, 161215
    @staticmethod
    def GetMaxUID(dbConn, strTable):
        return CTYLB_DB_Lite_CommFuncShare.GetMaxValue(dbConn, strTable, "unique_id")

    # 执行插入记录，一个字段参数
    #       -返回值： 新的记录ID
    # start by sk, 161121
    @staticmethod
    def ExecInsertRecField1( dbConn, strTable, strField, strValue):
        strInsertSQL="insert into " + strTable + " (" + strField + ") values(?)" # insert into table (field) values(%s)
        insertCur = dbConn.cursor()
        try:
            insertCur.execute(strInsertSQL, (strValue))
            iRetRecID = insertCur.lastrowid
            dbConn.commit()
        except Exception as e:
            iRetRecID = 0
        insertCur.close()
        return iRetRecID


if __name__ == '__main__':
    # 登记异常处理函数
    myConn = CTYLB_SQLite_DB_Conn( 'db/first.db')
    CTYLB_DB_Lite_CommFuncShare.CreateTable( myConn.s_dbConn, 'tpd_peer_ack', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        peer_client_name TEXT,
        last_valid_session_id INTEGER,
        last_recv_time datetime,
        retry_req_time1 datetime,
        retry_req_time2 datetime,
        retry_req_time3 datetime,
        retry_count INTEGER''' ,
        [ ['index_name', 'peer_client_name'],
          ['index_valid_session_id', 'last_valid_session_id'] ])

    print(' ')

