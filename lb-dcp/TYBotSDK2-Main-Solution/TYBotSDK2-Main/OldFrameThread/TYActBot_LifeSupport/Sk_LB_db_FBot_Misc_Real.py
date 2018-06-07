# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_db_FBot_MultiMonitorCtrl_Real.py
# 极限天元机器人-功能机器人-操作 多显示器内容控制 相关功能数据库 实现
#
# restart by sk. 170408

import pandas as pd
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_CommFuncShare  # 数据库共享功能实现
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc
from datetime import datetime


# #######################################################
# 操作 功能机器人显示内容 表实现 funcbot_op_display 实现类 CSkLBDB_funcbot_op_display
# start by sk, 170408
# #######################################################
class CSkLBDB_funcbot_op_display:
    s_strTableName = u"funcbot_op_display"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, ustrMonitorID, ustrLastContent, iContentType, iExecStatus=0, showTime=None):
        ustrMonitorID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrMonitorID)
        ustrLastContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrLastContent)

        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField4(dbConn, CSkLBDB_funcbot_op_display.s_strTableName,
                                                                 u"monitor_id", ustrMonitorID,
                                                                 u"last_content", ustrLastContent,
                                                                 u"exec_status", str(iExecStatus),
                                                                 u'content_type', str(iContentType))
        if( iRetNewRecID > 0):
            createTime = datetime.now()
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_funcbot_op_display.s_strTableName,
                                                                  u"create_time", createTime, u"id", str(iRetNewRecID))
            if( showTime):
                CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_funcbot_op_display.s_strTableName,
                                                                     u"show_time", showTime, u"id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        strRetMonitorID, strRetLastContent, iRetContentType, iRetExecStatus = u'', u'', 0, 0
        retShowTime = datetime.now()
        retCreateTime = datetime.now()

        strQueryReply = u"select * from %s where id=%d" % (CSkLBDB_funcbot_op_display.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetMonitorID  = recFrameReply["monitor_id"][0]
            strRetLastContent  = recFrameReply["last_content"][0]
            iRetExecStatus  = recFrameReply["exec_status"][0]
            retShowTime = recFrameReply["show_time"][0]
            retCreateTime = recFrameReply["create_time"][0]
            iRetContentType = recFrameReply['content_type'][0]

        return strRetMonitorID, strRetLastContent, iRetContentType, iRetExecStatus, retShowTime, retCreateTime

    @staticmethod
    def Update_RecID_ShowContentStatus( dbConn, iRecID, ustrShowContent, iContentType, iExecStatus=0, createTime=None, showTime=None):
        ustrShowContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrShowContent)
        strClause = "id=%d" % (iRecID)

        CSkLBDB_CommFuncShare.ExecUpdateRecField3(dbConn, CSkLBDB_funcbot_op_display.s_strTableName, strClause,
                                                  "last_content", ustrShowContent,
                                                  'content_type', str(iContentType),
                                                  'exec_status', str(iExecStatus))

        if( not createTime):
            createTime = datetime.now()
        if( not showTime):
            showTime = datetime.now()
        CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_funcbot_op_display.s_strTableName,
                                                             "create_time", createTime, "id", str(iRecID))
        CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_funcbot_op_display.s_strTableName,
                                                             "show_time", showTime, "id", str(iRecID))

    # -搜索显示器ID的记录ID
    @staticmethod
    def GetRecID_By_MonitorID( dbConn, ustrMonitorID):
        ustrMonitorID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrMonitorID)
        strClause = "monitor_id='%s'" % (ustrMonitorID)
        iRetID = CSkLBDB_CommFuncShare.ReadField_Single_WithClause(dbConn, CSkLBDB_funcbot_op_display.s_strTableName,
                                                                   "id", strClause)
        if( not iRetID):
            iRetID = 0
        return iRetID

    # -更新记录的状态值
    @staticmethod
    def Update_ExStatus( dbConn, iRecID, iNewStatus):
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_funcbot_op_display.s_strTableName, strClause,
                                                  "exec_status", str(iNewStatus))

