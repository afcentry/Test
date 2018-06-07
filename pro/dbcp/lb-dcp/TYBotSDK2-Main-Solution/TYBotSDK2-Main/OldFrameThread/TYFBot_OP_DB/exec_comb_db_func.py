# -*- coding:UTF-8 -*- 放到第一行标记
# exec_comb_db_func.py
# 执行综合数据库功能 实现
#
# restart by sk. 170403

from Sk_LB_db_funcbot_operate import CSkLBDB_dest_operate, CSkLBDB_dest_param_status, CSkLBDB_result_app_task_name,\
    CSkLBDB_result_param_block, CSkLBDB_result_content
from Sk_LB_db_main_share_cp import CSkLBDB_CommFuncShare, CSkLBDB_MainConn
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc
from datetime import datetime

'''
	Get-db-operate-name: 申请，数据库操作名字，
    	输入 objname, dbname，tablename，need_field_name，sign_id_field_name，last_ex_id,
    	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 501，strValue = 输入内容，以;分隔
    	返回: int_operate_db_id。iValue=502，strValue=字符串值
	Get_unhandle_rec_count: 获得未处理的记录个数。
    	输入：objname, 上次rec_id_value，
    	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 503，strParam1= objname，strValue =上次 rec_id_value
    	返回: iValue=504, strValue =未处理个数，strParam2=总记录个数
	Get_next_param_block: 获得下部分参数块
    	输入: objname, need_param_coun, eachCount。
    	输入的单元为：CTYBot_CTUnit_CommonData，iValue = 505，strParam1= objname，strValue =need_param_count, strParam2 = eachCount
    	返回：多个参数块单元，每个单元为：CTYBot_CTUnit_CommonData，iValue = 506，strParam1= objname，strValue =paramValueArray: 以’\r\n’分割, strParam2=paramBlockID

'''

def ConnectToMidExecExecDb( strDbName):
    retExecDbConn = CSkLBDB_MainConn()
    # retExecDbConn.ReConnectTo_F1_13_21( strDbName)
    # retExecDbConn.ReConnect(u"172.16.56.130", 3306, u"testzhuangshiqi", u"abc888+222@@@", strDbName)
    retExecDbConn.ReConnect(u"192.168.13.21", 3306, u"brain2017", u"11plm**2017$#", strDbName)
    return retExecDbConn

# #######################################################
# 对参数目标进行操作
# start by sk, 170403
# #######################################################
class CTYF_OpDB_OperateParamBlock:
    def __init__(self):
        pass

    def __del__(self):
        pass

    # -申请，数据库操作名字。输出：新记录ID
    @staticmethod
    def RequestDbOperate( dbConn, strObjName, strDatabase, strTable, strField, strIDField, iLastExecID):
        strObjName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strObjName)
        strDatabase = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strDatabase)
        strTable = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strTable)
        strField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strField)
        strIDField = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strIDField)
        iNewRecID = CSkLBDB_dest_operate.AddNewdRec( dbConn, strObjName, '', strDatabase, strTable, strField, strIDField, iLastExecID)
        return iNewRecID

    # -获得未处理的记录个数。输出：rec_id_value
    @staticmethod
    def GetUnHandleRecID( dbConn, strObjName):
        strObjName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strObjName)
        iRetNotExecedRecCount, iRetTotalRecCount = 0, 0
        iObjRecID = CSkLBDB_dest_operate.GetRecID_By_Name( dbConn, strObjName)
        if( iObjRecID > 0):
            strExecObjName, strExecPwdHash, strExecDbName, strExecTableName, strExecFieldName, strExecSignIDField, \
                iExecLastExID = CSkLBDB_dest_operate.ReadByRecID( dbConn, iObjRecID)
            # 此处读完记录个数后，commit确认一下，确保外部修改了记录数，而本连接未更新。by sk. 170505
            dbConn.commit()
            dbExecConn = ConnectToMidExecExecDb(strExecDbName)
            if( dbExecConn and dbExecConn.s_DbConn):
                strNotExecClause = '%s>%d' % (strExecSignIDField, iExecLastExID)
                iRetNotExecedRecCount = CSkLBDB_CommFuncShare.GetRecCount( dbExecConn.s_DbConn, strExecTableName, strNotExecClause)
                iRetTotalRecCount = CSkLBDB_CommFuncShare.GetRecCount( dbExecConn.s_DbConn, strExecTableName)

        return iRetNotExecedRecCount, iRetTotalRecCount

    # -获得可用的参数块。输出：参数块id, 参数内容队列
    @staticmethod
    def RequestParamBlockContent( dbConn, strObjName, iEachBlockCount):
        strObjName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strObjName)
        retParamContentArray = []
        strRetParamSignID = ''
        iObjRecID = CSkLBDB_dest_operate.GetRecID_By_Name( dbConn, strObjName)
        if( iObjRecID > 0):
            strExecObjName, strExecPwdHash, strExecDbName, strExecTableName, strExecFieldName, strExecSignIDField, \
                iExecLastExID = CSkLBDB_dest_operate.ReadByRecID( dbConn, iObjRecID)
            dbExecConn = ConnectToMidExecExecDb(strExecDbName)

            if( dbExecConn and dbExecConn.s_DbConn):
                strReqClause = '%s>%d' % (strExecSignIDField, iExecLastExID)
                retParamContentArray, idSignFieldArray, tmpArray  = CSkLBDB_CommFuncShare.Read3Fields_Array_WithClause_limit( dbExecConn.s_DbConn,
                            strExecTableName, strExecFieldName, strExecSignIDField, '', strReqClause, iEachBlockCount)
                # 将id格式化，写入内容。
                if( len(idSignFieldArray) > 0):
                    strIDValueArray = []
                    for iEachID in idSignFieldArray:
                        strIDValueArray.append( str(iEachID))
                    strIDCollectTotal = ' '.join(strIDValueArray)
                    # 将本记录写入表 sk_dest_param_status
                    iLastID = CSkLBDB_CommFuncShare.GetRecCount( dbConn, CSkLBDB_dest_param_status.s_strTableName)
                    strRetParamSignID = '%s_%d' % (strObjName, iLastID)
                    CSkLBDB_dest_param_status.AddNewdRec( dbConn, iObjRecID, strIDCollectTotal, strRetParamSignID, 0, datetime.now())
                    # 更新最大的id值
                    iMaxIDValue = max(idSignFieldArray)
                    CSkLBDB_dest_operate.Update_LastIDValue( dbConn, iObjRecID, iMaxIDValue)

        return strRetParamSignID, retParamContentArray

    # -设置参数块完成状态
    @staticmethod
    def SetParamBlockStatus( dbConn, strObjName, strParamBlockSign, iStatus):
        strObjName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strObjName)
        strParamBlockSign = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strParamBlockSign)
        iObjRecID = CSkLBDB_dest_operate.GetRecID_By_Name(dbConn, strObjName)
        if( iObjRecID > 0):
            iParamRecID = CSkLBDB_dest_param_status.GetRecID_By_OperateID_ParamBlockID( dbConn, iObjRecID, strParamBlockSign)
            if( iParamRecID > 0):
                CSkLBDB_dest_param_status.Update_Status_OpTime( dbConn, iParamRecID, iStatus, datetime.now())
        pass

# #######################################################
# 对结果进行操作
# start by sk, 170403
# #######################################################
class CTYF_OpDB_OperateResult:
    def __init__(self):
        pass

    def __del__(self):
        pass

    # -增加结果值
    @staticmethod
    def AddRecord(dbConn, strAppName, strSubTaskName, strParamBlockID, strRunTitleDomain, strResultContent):
        strAppName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strAppName)
        strSubTaskName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strSubTaskName)
        strParamBlockID = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strParamBlockID)
        strRunTitleDomain = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRunTitleDomain)
        strResultContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strResultContent)
        iRetResultID = 0

        iAppTaskID = CSkLBDB_result_app_task_name.AddNewdRec( dbConn, strAppName, strSubTaskName)
        if(iAppTaskID):
            iParamRecID = CSkLBDB_result_param_block.AddNewdRec( dbConn, iAppTaskID, strParamBlockID)
            if( iParamRecID):
                iRetResultID = CSkLBDB_result_content.AddNewdRec( dbConn, iParamRecID, strRunTitleDomain, strResultContent)

        return iRetResultID
    pass
