# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_db_FBot_OPWXExWeb_Real.py
# 极限天元机器人-功能机器人-操作微信对外对接Web相关功能数据库 实现
#
# restart by sk. 170407
# update by sk. 170411

import pandas as pd
from TYBotSDK2.FBotSubFunc.FBot_db_main_share import CSkLBDB_CommFuncShare  # 数据库共享功能实现
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc
from datetime import datetime

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

        strQueryReply = u"select * from %s where id=%d" % (CSkLBDB_ow_bot_out_logincode.s_strTableName, iRecID)
        recFrameReply = pd.read_sql_query(strQueryReply, dbConn)  # 转成DataFrame
        recCount = len(recFrameReply)  # 记录个数
        if( recCount > 0):
            strRetURL  = recFrameReply["url"][0]
            strRetQRCodeContent = recFrameReply["qrcodecontent"][0]
            retCreateTime = recFrameReply["create_time"][0]

        return strRetURL, strRetQRCodeContent, retCreateTime

    # 更新记录内容
    @staticmethod
    def UpdateRecordContent(dbConn, iRecID, ustrURL, ustrImage, execDateTime):
        ustrURL = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrURL)
        ustrImage = CTYLB_MainSys_MiscFunc.SafeGetUnicode(ustrImage)

        strClause = 'id=%d' % (iRecID)
        CSkLBDB_CommFuncShare.ExecUpdateRecField2( dbConn, CSkLBDB_ow_bot_out_logincode.s_strTableName, strClause,
                                                   'url', ustrURL,
                                                   'qrcodecontent', ustrImage)
        if( execDateTime):
            CSkLBDB_CommFuncShare.ExecUpdateRecField_To_DateTime( dbConn, CSkLBDB_ow_bot_out_logincode.s_strTableName,
                                                                  'create_time', execDateTime, 'id', str(iRecID))
        pass
