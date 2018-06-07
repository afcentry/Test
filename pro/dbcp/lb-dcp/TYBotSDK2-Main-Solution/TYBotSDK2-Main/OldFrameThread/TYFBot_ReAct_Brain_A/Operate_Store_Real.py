# -*- coding:UTF-8 -*- 放到第一行标记
# Operate_Store_Real.py 操作 行动存储实现
#
# start by sk. 170412

from datetime import datetime
from Sk_LB_db_FBot_ReactBrain_Real import CSkLBDB_ea_brain_chatcontent, CSkLBDB_ea_brain_envirument, CSkLBDB_ea_brain_usermang,\
    CSkLBDB_ea_brain_enviru_property

# #######################################################
# 行动大脑操作存储功能实现
# start by sk, 170412
# #######################################################
class CTYOp_ReActBrain_Store:
    s_g_iDirection_From_User_To_Brain = 0   # 用户发送给大脑
    s_g_iDirection_From_Brain_To_User = 1   # 大脑发送给用户
    s_g_iStatus_Free = 0     # 空闲，未运行
    s_g_iStatus_Running = 1  # 正在运行
    s_g_iStatus_Finish = 2   # 运行完成

    s_g_iUserNameType_User = 0
    s_g_iUserNameType_Group = 1

    s_g_iContentType_Text = 0   # 文字内容类型
    s_g_iContentType_Image = 1  # 图像内容类型

    def __init__(self):
        pass

    def __del__(self):
        pass

    # 获得下一条需要发送的消息
    # start by sk. 170412
    @staticmethod
    def PopNextNeedSendWeiXinMsg( dbConn):
        ustrRetMsgContent, ustrRetToUser, iRetUserType, iRetContentType, ustrRetGroupName = u'', u'', 0, 0, u''

        # 查找 brain_chatcontent表，可发送，状态=0的记录
        iRecNeedSendChatContentID = CSkLBDB_ea_brain_chatcontent.SearchNextRec_By_Direction_ExecStatus(dbConn,
                    CTYOp_ReActBrain_Store.s_g_iDirection_From_Brain_To_User, CTYOp_ReActBrain_Store.s_g_iStatus_Free)
        if( iRecNeedSendChatContentID):
            iBelongEnviruID, ustrChatContent, iContentType, iDirection, createTime, execTime, iExecStatus =\
                CSkLBDB_ea_brain_chatcontent.ReadByRecID(dbConn, iRecNeedSendChatContentID)

            ustrUserName = u''

            # 获得 envirument_id 对应的 usernameid, groupname
            iEnvBelongUserMangID, ustrEnvGroupName = CSkLBDB_ea_brain_envirument.ReadByRecID(dbConn, iBelongEnviruID)
            # 获得 usernameid 对应的 username
            if( iEnvBelongUserMangID):
                ustrUserName = CSkLBDB_ea_brain_usermang.ReadByRecID(dbConn, iEnvBelongUserMangID)

            ustrRetToUser = ustrUserName
            if( ustrEnvGroupName):
                strRetGroupName = ustrEnvGroupName
                iRetUserType = 1   # 群名
            else:
                iRetUserType = 0   # 用户名

            ustrRetMsgContent = ustrChatContent
            iRetContentType = iContentType

            # 输出后，设置记录状态
            CSkLBDB_ea_brain_chatcontent.Update_ExTime_Status(dbConn, iRecNeedSendChatContentID, datetime.now(), CTYOp_ReActBrain_Store.s_g_iStatus_Finish)

        return ustrRetMsgContent, ustrRetToUser, iRetUserType, iRetContentType, ustrRetGroupName

    # 获得用户对话的环境ID
    # start by sk. 170412
    @staticmethod
    def GetUserChatEnvirumentID(dbConn, ustrUserName, iUserGroupType, ustrFromGroupName):
        iRetEnvirumentRecID = 0
        # 首先获得用户id
        iUserRecID = CSkLBDB_ea_brain_usermang.AddNewdRec( dbConn, ustrUserName)
        if( iUserRecID):
            # 获得环境id
            ustrGroupName = u'' if( iUserGroupType == 0) else ustrFromGroupName
            iRetEnvirumentRecID = CSkLBDB_ea_brain_envirument.AddNewdRec( dbConn, iUserRecID, ustrGroupName)

        return iRetEnvirumentRecID

    # 获得用户对话的环境ID，对应的用户名和群名
    # start by sk. 170412
    @staticmethod
    def GetEnvirumentID_NameType(dbConn, iEnvRecID):
        iRetUserType, ustrRetUserName, ustrRetGroupName = 0, u'', u''

        iBelongUserMangID, ustrBelongGroupName = CSkLBDB_ea_brain_envirument.ReadByRecID( dbConn, iEnvRecID)
        if( iBelongUserMangID):
            ustrUserName = CSkLBDB_ea_brain_usermang.ReadByRecID( dbConn, iBelongUserMangID)

            ustrRetUserName = ustrUserName
            if( ustrBelongGroupName):
                ustrRetGroupName = ustrBelongGroupName
                iRetUserType = CTYOp_ReActBrain_Store.s_g_iUserNameType_Group
            else:
                iRetUserType = CTYOp_ReActBrain_Store.s_g_iUserNameType_User

        return iRetUserType, ustrRetUserName, ustrRetGroupName


# 大脑分析机器人 的 用户操作空间对象
# start by sk. 170412
class CTYOp_ReActBrain_UserEnviru:
    def __init__(self, dbConn, ustrUserName):
        self.s_ustrUserName = ustrUserName
        self.s_dbConn = dbConn
        self.s_iUserPureEnviruID = CTYOp_ReActBrain_Store.GetUserChatEnvirumentID( dbConn, ustrUserName,
                                                                CTYOp_ReActBrain_Store.s_g_iUserNameType_User, u'')
        pass

    def __del__(self):
        pass

    # 设置属性
    # start by sk. 170412
    def SetProp(self, ustrProp, ustrValue):
        iPropRecID = CSkLBDB_ea_brain_enviru_property.AddNewdRec( self.s_dbConn, self.s_iUserPureEnviruID, ustrProp, u'')
        if( iPropRecID):
            CSkLBDB_ea_brain_enviru_property.Update_PropValue( self.s_iUserPureEnviruID, iPropRecID, ustrValue)
        pass

    # 获取属性
    # start by sk. 170412
    def GetPropValue(self, ustrProp):
        ustrRetValue = u''
        iPropRecID = CSkLBDB_ea_brain_enviru_property.GetRecID_By_EnviruID_PropName( self.s_dbConn, self.s_iUserPureEnviruID, ustrProp)
        if( iPropRecID):
            ustrRetValue = CSkLBDB_ea_brain_enviru_property.ReadValueField_By_RecID( self.s_dbConn, iPropRecID)
        return ustrRetValue
