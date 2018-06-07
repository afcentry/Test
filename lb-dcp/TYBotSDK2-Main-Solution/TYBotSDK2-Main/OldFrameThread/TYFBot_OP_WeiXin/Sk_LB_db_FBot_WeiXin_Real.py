# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_db_FBot_WeiXin_Real.py
# 极限天元机器人-功能机器人-操作微信相关功能数据库 实现
#
# restart by sk. 170407

import pandas as pd
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_CommFuncShare  # 数据库共享功能实现
from datetime import datetime
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc

# #######################################################
# 操作目标表实现 ow_bot_out_logincode 实现类 CSkLBDB_ow_bot_out_logincode
# start by sk, 170407
# #######################################################
class CSkLBDB_ow_bot_out_logincode:
    s_strTableName = u"ow_bot_out_logincode"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn):
        return 0

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        strRetURL, strRetQRCodeContent = '', ''
        retCreateTime = datetime.now()

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ow_bot_out_logincode.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetURL  = recFrameReply["url"][0]
            strRetQRCodeContent = recFrameReply["qrcodecontent"][0]
            retCreateTime = recFrameReply["create_time"][0]

        return strRetURL, strRetQRCodeContent, retCreateTime


# #######################################################
# 获得的聊天内容记录表实现 ow_bot_out_chatcontent 实现类 CSkLBDB_ow_bot_out_chatcontent
# start by sk, 170407
# #######################################################
class CSkLBDB_ow_bot_out_chatcontent:
    s_strTableName = u"ow_bot_out_chatcontent"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, ustrContent, iTypeS, ustrFromS, iFromType, ustrFromGroupName, iExecStatus):
        ustrContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrContent)
        ustrFromS = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrFromS)
        ustrFromGroupName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrFromGroupName)

        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField6(dbConn, CSkLBDB_ow_bot_out_chatcontent.s_strTableName,
                                                                 "content", ustrContent,
                                                                 "type_s", str(iTypeS),
                                                                 "from_s", ustrFromS,
                                                                 "fromtype", str(iFromType),
                                                                 "from_group_name", ustrFromGroupName,
                                                                 "ex_status", str(iExecStatus))
        if( iRetNewRecID > 0):
            createTime = datetime.now()
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_ow_bot_out_chatcontent.s_strTableName,
                                                                  "createtime", createTime, "id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        strRetContent, iRetTypeS, strRetFromS, iRetFromType, strRetFromGroupName, iRetExStatus = '', 0, '', 0, '', 0
        retCreateTime = datetime.now()

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ow_bot_out_chatcontent.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetContent = recFrameReply["content"][0]
            iRetTypeS = recFrameReply["type_s"][0]
            strRetFromS = recFrameReply["from_s"][0]
            iRetFromType = recFrameReply["fromtype"][0]
            strRetFromGroupName = recFrameReply["from_group_name"][0]
            retCreateTime = recFrameReply["createtime"][0]
            iRetExStatus = recFrameReply['ex_status'][0]

        return strRetContent, iRetTypeS, strRetFromS, iRetFromType, strRetFromGroupName, iRetExStatus, retCreateTime

    # 获得状态不等于某值的记录  -返回值： ID列表
    @staticmethod
    def GetRecList_By_StatusNotEquValue( dbConn, iCheckStatus):
        strClause = "ex_status is NULL or ex_status<>%d" % (iCheckStatus)
        iRetRecIDArray = CSkLBDB_CommFuncShare.ReadField_Array_WithClause( dbConn, CSkLBDB_ow_bot_out_chatcontent.s_strTableName,
                                                                           "id", strClause)
        return iRetRecIDArray

    # -更新记录的状态值
    @staticmethod
    def Update_ExStatus( dbConn, iRecID, iNewStatus):
        strClause = "id=%d" % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField1(dbConn, CSkLBDB_ow_bot_out_chatcontent.s_strTableName, strClause,
                                                  "ex_status", str(iNewStatus))


# #######################################################
# 输入发送聊天内容表实现 ow_bot_in_sendchatcontent 实现类 CSkLBDB_ow_bot_in_sendchatcontent
# start by sk, 170407
# #######################################################
class CSkLBDB_ow_bot_in_sendchatcontent:
    s_strTableName = "ow_bot_in_sendchatcontent"

    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加记录。输出：新记录ID
    @staticmethod
    def AddNewdRec( dbConn, ustrContent, ustrTypeS, ustrToS, ustrToType, ustrToGroupName, ustrStatusS, execSendTime=None):
        ustrContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrContent)
        ustrTypeS = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrTypeS)
        ustrToS = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrToS)
        ustrToType = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrToType)
        ustrToGroupName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrToGroupName)
        ustrStatusS = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrStatusS)

        iRetNewRecID = CSkLBDB_CommFuncShare.ExecInsertRecField6(dbConn, CSkLBDB_ow_bot_in_sendchatcontent.s_strTableName,
                                                                 "content", ustrContent,
                                                                 "type_s", ustrTypeS,
                                                                 "to_s", ustrToS,
                                                                 "to_type", ustrToType,
                                                                 "to_group_name", ustrToGroupName,
                                                                 "status_s", ustrStatusS)
        if( iRetNewRecID > 0):
            createTime = datetime.now()
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_ow_bot_in_sendchatcontent.s_strTableName,
                                                                  "createtime", createTime, "id", str(iRetNewRecID))
            if( execSendTime):
                CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime(dbConn, CSkLBDB_ow_bot_in_sendchatcontent.s_strTableName,
                                                                     "exec_send_time", execSendTime, "id", str(iRetNewRecID))
        return iRetNewRecID

    # 读取记录：根据记录ID，获得字段内容
    @staticmethod
    def ReadByRecID( dbConn, iRecID):
        strRetContent, strRetTypeS, strRetToS, strRetToType, strRetToGroupName, strRetStatusS = '', '', '', '', '', ''
        retCreateTime, retExecSendTime = datetime.now(), datetime.now()

        strQueryReply = "select * from %s where id=%d" % (CSkLBDB_ow_bot_in_sendchatcontent.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetContent = recFrameReply["content"][0]
            strRetTypeS = recFrameReply["type_s"][0]
            strRetToS = recFrameReply["to_s"][0]
            strRetToType = recFrameReply["to_type"][0]
            strRetToGroupName = recFrameReply["to_group_name"][0]
            strRetStatusS = recFrameReply["status_s"][0]
            retCreateTime = recFrameReply["createtime"][0]
            retExecSendTime = recFrameReply["exec_send_time"][0]
        return strRetContent, strRetTypeS, strRetToS, strRetToType, strRetToGroupName, strRetStatusS, retCreateTime, retExecSendTime
