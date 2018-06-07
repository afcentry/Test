# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_p2p_ExCall_SubClient.py 外部调用，tylb-p2p子客户端实现
#
# start by sk. 170205
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# 制定一个规则，当数据库和配置读出来后的内容，包括名字，命令内容，是unicode，整合成传输包时，是bytes。中间格式如何确定？
# 此处明确，只有在数据包的单元里面，才是bytes，其他地方一律unicode。
# start by sk. 180315. 升级到V3，采用json方式处理

from .Tylb_p2p_Db_console import CTYLBDB_tpd_inout_text
from .Tylb_p2p_Db_Share import CTYLB_SQLite_DB_Conn  # 数据库共享功能实现
from .Tylb_Support_Client import CTYLB_Client_Config
from .Tylb_p2p_share import CTYLB_Log, CTYLB_SvClt_Cmd_Base_bytes, CTYLB_MainSys_MiscFunc
from datetime import datetime
# from .g_charset_func import g_C_SkCharset
import struct
import base64
import json
from .Tylb_Support_Client_sub_peer_2 import CTYLB_Trans_Exec_StoreUser_Unit, CTYLB_Client_RemoteClientNotifyUnit,\
    CTYLB_Client_Config, CTYLB_Ct_Mang_NeedIdentify, CTYLB_MidBalance_InOutBuffMang, CTYLB_OnLineClient_Mang

s_g_iDataType_SimuSystemNotify = 106  # 模拟系统通知
s_g_iMainCmd_SimuSystemNotify = 0  # 主命令，暂时未用
s_g_iSubCmd_SimuSystemNotify = 0  # 子命令，暂时未用


# tylb－p2p的 内部调用，需要配置的，新建实际使用的P2P内容单元
# start by sk. 170205
def sample_TYLB_P2P_Call_CreateNew_P2PContentUnit():
    newContentUnit = CTYLB_P2P_ContentUnit_Base()
    return newContentUnit

# tylb－p2p的 内容单元基类。存储中间传输和发送的内容
# 需要外部开发者，继承子类后，重写 内容变量，重写 CombPacket, ExactPacket 函数
# start by sk. 170205
class CTYLB_P2P_ContentUnit_Base:
    s_g_str_chCmdPackSign = 'WaX'  # 命令包的标志
    s_g_str_chCmdPackSeperate = '_#xW1D9_@'  # 命令包封装后，格式化标志和内容的间隔
    s_g_strTimeTransFormat = '%y-%m-%d %H:%M:%S.%f'  # 时间字符串格式
    s_g_strEmpty = '_@#_x1fV'

    def __init__(self, iDataType=0):
        self.s_iMyDataType = iDataType
        self.s_strExternalContent = ''
        self.s_unitUTCTime = datetime.utcnow()  # 本数据包生成时候的utc时间

        import time
        import random
        iRand1 = random.randint(10000, 1000000)
        iRand2 = random.randint(1000, 1000000)
        strRetUnique = '%s_%d_%d' % ( str(time.time()), iRand1, iRand2 )
        self.s_strUniqueSign = strRetUnique   # 全局唯一标记

        self.s_iBotCmd_Main = 0  # 主命令
        self.s_iBotCmd_Sub = 0  # 子命令
        self.s_strMySampDataStr = 'hello'

    # 根据UTC时间内容，获得和现在对应的时间
    def GetUnitRelativeTime(self):
        nowTime = datetime.now()
        curUTCTime = datetime.utcnow()
        utcDiff = curUTCTime - self.s_unitUTCTime
        retUnitTime = nowTime - utcDiff
        return retUnitTime

    # 把字符串转成安全UTF8, 再转成Base64
    # start by sk. 170301
    @staticmethod
    def SafeConvertStrToUTF8_Base64(strInputAnyStr):
        bstrFix = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strInputAnyStr)
        bstrFixBase64 = base64.encodebytes(bstrFix)
        return bstrFixBase64

    # 把字符串 由base64, 转成安全UTF8
    # start by sk. 170301
    @staticmethod
    def SafeConvertBase64Str_ToUTF8(bstrInputBase64):
        try:
            bstrFixBase64 = base64.decodebytes(bstrInputBase64)
        except Exception as e:
            bstrFixBase64 = bstrInputBase64

        bstrOrigText = CTYLB_MainSys_MiscFunc.SafeGetUTF8(bstrFixBase64)
        return bstrOrigText


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        self.s_strExternalContent = ''


    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        pass

    s_g_Key_strMySign = 'str_mysign'
    s_g_Key_strExContent = 'str_excontent'
    s_g_Key_iDataType = 'iDatatype'
    s_g_Key_iMainBotCmd = 'iMainBotCmd'
    s_g_Key_iSubBotCmd = 'iSubBotCmd'
    s_g_Key_strUTCTime = 'str_utctime'
    s_g_Key_strExternalContent = 'str_externalContent'
    s_g_Key_strUniqueSign = 'str_uniqueSign'

    # 外部调用－ 综合数据包，输出字符串
    def EX_CombPacket(self):
        # 我自身的格式(Format)
        # 我自身的分割符号(split)
        # 我自身的数据内容(content)--如下
        #   我自身的标记(Sign)
        #   我的内部变量
        #   我扩展的数据格式
        #   我扩展格式化后的数据

        # 构建自身数据内容
        exJsonDict = {}
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strMySign] = CTYLB_P2P_ContentUnit_Base.s_g_str_chCmdPackSign
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_iDataType] = self.s_iMyDataType
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_iMainBotCmd] = self.s_iBotCmd_Main
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_iSubBotCmd] = self.s_iBotCmd_Sub
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strUTCTime] = self.s_unitUTCTime.strftime( self.s_g_strTimeTransFormat)
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strUniqueSign] = self.s_strUniqueSign

        self.subClass_Call_BuildExWriteContent()   # 构建外部内容
        exJsonDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strExContent] = self.s_strExternalContent

        strRetTotal = json.dumps(exJsonDict, ensure_ascii=False)
        return strRetTotal

    # 外部调用－ 从字符串中提取数据包
    def EX_ExactFromPacket(self, strContentBuff):
        bRetValue = False

        strFixContent = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strContentBuff)

        try:
            exOrigDict = json.loads(strFixContent)

            if(exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strMySign] == CTYLB_P2P_ContentUnit_Base.s_g_str_chCmdPackSign):
                self.s_iMyDataType = int(exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_iDataType])
                self.s_iBotCmd_Main = int(exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_iMainBotCmd])
                self.s_iBotCmd_Sub = int(exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_iSubBotCmd])
                self.s_unitUTCTime = datetime.strptime(exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strUTCTime], self.s_g_strTimeTransFormat)
                strExternalContent = exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strExContent]
                self.s_strUniqueSign = exOrigDict[CTYLB_P2P_ContentUnit_Base.s_g_Key_strUniqueSign]

                try:
                    if(strExternalContent):
                        self.subClassReWrite_Call_FillContent(strExternalContent)
                except Exception as e:
                    CTYLB_Log.ShowLog(1, 'P2P_Content_Unit_Base', 'Ignore, new version CTUnit, format error [%s]' % (str(e)))
                    pass

                bRetValue = True

        except:
            pass

        return bRetValue

    # 内部调用－ 设置命令类型。
    # start by sk. 170214
    def self_SetCmd(self, iMainCmd, iSubCmd):
        self.s_iBotCmd_Main = iMainCmd
        self.s_iBotCmd_Sub = iSubCmd

    # 外部获取大小。
    # start by sk. 170312
    def GetTotalSize(self):
        strExBuff = self.EX_CombPacket()
        iRetLen = len(strExBuff)
        return iRetLen

# 回调定义单元
# start by sk. 170213
class CTYLB_Bot_G_CallBack_DefUnit:
    # s_func_CallBack = None   # 回调函数。CallBack ( strFromSender, param1, param2, tylbContentUnit, origCallBackDefUnit)
    s_g_iSubRange_ALL_Valid = -1

    def __init__(self, iDataType, iMainCmd, iSubCmd, param1, param2, funcCreateNewUnit, funcCallBack):
        self.s_bSubCmdRange = False        # 是否子命令范围回调
        self.s_iSubCmd_Range_Start = 0      # 子命令范围，开始值
        self.s_iSubCmd_Range_End = 0      # 子命令范围，结束
        self.s_iRecv_DataType = iDataType  # 接收到的数据类型
        self.s_iRecv_MainCmd = iMainCmd  # 接收到的主命令
        self.s_iRecv_SubCmd = iSubCmd  # 接收到的子命令
        self.s_CallBack_Param1 = param1  # 回调参数1
        self.s_CallBack_Param2 = param2  # 回调参数2
        self.s_func_Create_NewUnit = funcCreateNewUnit  # 创建新单元的功能函数 newUnit = CreateNewUnit()
        self.s_func_CallBack = funcCallBack  # 回调函数。CallBack (...)

    # 设置命令范围
    # start by sk. 170223
    def SetCompareTypeRange(self, iRangeStart, iRangeEnd=s_g_iSubRange_ALL_Valid):
        self.s_bSubCmdRange = True        # 是否子命令范围回调
        self.s_iSubCmd_Range_Start = iRangeStart      # 子命令范围，开始值
        self.s_iSubCmd_Range_End = iRangeEnd      # 子命令范围，结束

    # 判断单元条件是否和我的相同, 是否我自己定义触发条件
    # start by sk. 170213
    def CompareCmdValueFitMe(self, tylbCTUnit):
        bRetValue = False
        if( tylbCTUnit.s_iMyDataType == self.s_iRecv_DataType):
            if (tylbCTUnit.s_iBotCmd_Main == self.s_iRecv_MainCmd):
                if( self.s_bSubCmdRange):
                    if( self.s_iSubCmd_Range_Start <= tylbCTUnit.s_iBotCmd_Sub):
                        # 是否开始到所有末尾？
                        if( self.s_iSubCmd_Range_End == CTYLB_Bot_G_CallBack_DefUnit.s_g_iSubRange_ALL_Valid):
                            bRetValue = True
                        else:
                            if( self.s_iSubCmd_Range_End >= tylbCTUnit.s_iBotCmd_Sub):
                                bRetValue = True
                    pass
                else:
                    if (tylbCTUnit.s_iBotCmd_Sub == self.s_iRecv_SubCmd):
                        bRetValue = True
        return bRetValue

    # 判断内容单元，是否和我的相同或者交互重合？
    # start by sk. 161118
    def IsValueSameAsMe(self, tylbContentUnit):
        bRetValue = False
        if( tylbContentUnit.s_iRecv_DataType == self.s_iRecv_DataType):
            if (tylbContentUnit.s_iRecv_MainCmd == self.s_iRecv_MainCmd):
                if( self.s_bSubCmdRange == tylbContentUnit.s_bSubCmdRange):
                    if( self.s_bSubCmdRange):
                        if( self.s_iSubCmd_Range_Start <= tylbContentUnit.s_iRecv_SubCmd):
                            # 是否开始到所有末尾？
                            bRetValue = True
                            pass
                    else:
                        if (tylbContentUnit.s_iRecv_SubCmd == self.s_iRecv_SubCmd):
                            bRetValue = True
        return bRetValue

# tylb－p2p的 外部调用，子客户端实现
#  通过调用 CheckRecv 检查是否有数据单元到达， 调用 SendContent 来发送数据单元
# start by sk. 170205
class CTYLB_P2P_ExCall_SubClient_Realize:
    def __init__(self, strMyName, strClientDbFilePath, func_CreateNew_P2PContentUnit):
        self.s_botCallBackFuncArray = []   # 回调单元队列 CTYLB_Bot_G_CallBack_DefUnit
        self.s_strSelfName = strMyName
        self.s_opSQLiteDB = CTYLB_SQLite_DB_Conn(strClientDbFilePath)
        self.s_func_CreateNew_P2PContentUnit = func_CreateNew_P2PContentUnit

        # 初始化表
        try:
            CTYLBDB_tpd_inout_text.CreateNewTable(self.s_opSQLiteDB.s_dbConn)
        except Exception as e:
            # 有时候会表锁定，导致出错异常。可以忽略
            pass
        pass

    # 外部功能调用 － 根据现有基本单元，创建实际的实现单元
    # start by sk. 170304
    def ExCall_CreateNewRealCTUnit_FromBaseCTUnit(self, strDataBuff, baseUnit):
        newExecContentUnit = None
        # 是否已经注册的回调功能?
        execCallBackUnit = None
        for eachUnit in self.s_botCallBackFuncArray:
            if (eachUnit.CompareCmdValueFitMe(baseUnit)):
                execCallBackUnit = eachUnit
                break
        if (execCallBackUnit):
            # 采用注册回调函数实现
            if (execCallBackUnit.s_func_Create_NewUnit):
                newExecContentUnit = execCallBackUnit.s_func_Create_NewUnit()
                newExecContentUnit.EX_ExactFromPacket(strDataBuff)
        return execCallBackUnit, newExecContentUnit

    # 外部功能调用 － 增加回调单元. 如果相同条件的回调单元已经存在，则返回False
    # start by sk. 170213
    def ExCall_AddCallBackUnit(self, callBackUnit):
        bAddSucc = False

        bOldExist = False
        for eachUnit in self.s_botCallBackFuncArray:
            if( eachUnit.IsValueSameAsMe(callBackUnit)):
                bOldExist = True
                break
        if( not bOldExist):
            self.s_botCallBackFuncArray.append( callBackUnit)
            bAddSucc = True
        return bAddSucc

    # 检查新的到达的数据单元
    # start by sk. 170205
    def ExCall_Timer_CheckRecv(self):
        bRetResult = False
        strRetFrom = ''
        retRecvTime = None
        retTylbP2PContUnit = None

        if(self.s_func_CreateNew_P2PContentUnit):
            # 查询，并读取数据库回复的记录
            iFreeRecID = CTYLBDB_tpd_inout_text.GetNextRec_By_DestName_Status(self.s_opSQLiteDB.s_dbConn, self.s_strSelfName, 0)
        else:
            iFreeRecID = 0

        if (iFreeRecID > 0):
            strRetFrom = 'from'
            # 读取数据库内容
            iInputReplyType, strContent, strFromName, strDestName, iPeerStatus, createTime, replyTime = \
                CTYLBDB_tpd_inout_text.ReadByRecID(self.s_opSQLiteDB.s_dbConn, iFreeRecID)
            if (createTime):
                retRecvTime = createTime  # .strftime('%m-%d %H:%M:%S')
            else:
                retRecvTime = datetime.now()
            # 对数据包进行解码
            tryDecodeUnit = CTYLB_P2P_ContentUnit_Base()
            bUnitDecodeSucc = False

            # 根据内容进行封装
            if( iInputReplyType == CTYLB_SvClt_Cmd_Base_bytes.s_g_iInOutType_SystemNotify):
                # 填充接收到的系统命令单元。
                simuNotifyCTUnit = CTYBot_CTUnit_SimuSystemNotify()
                origCollect = json.loads(strContent)
                iStatus = origCollect['status']
                strFromName = origCollect['from']

                iType = 0
                if( iStatus == CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Restart):
                    iType = CTYBot_CTUnit_SimuSystemNotify.s_g_iType_Notify_Peer_Online
                elif(iStatus == CTYLB_MidBalance_InOutBuffMang.s_g_iPeerServer_Restart):
                    iType = CTYBot_CTUnit_SimuSystemNotify.s_g_iType_Notify_PeerServer_Restart
                simuNotifyCTUnit.SetNotifyTypeData( iType, iStatus, strFromName)
                # 生成模拟缓冲，实现传递。
                strContent = simuNotifyCTUnit.EX_CombPacket()
                tryDecodeUnit.EX_ExactFromPacket( strContent)
                bUnitDecodeSucc = True
            else:
                if( tryDecodeUnit.EX_ExactFromPacket( strContent)):
                    bUnitDecodeSucc = True

            if( bUnitDecodeSucc):
                bRetValue = True
                execCallBackUnit, newExecContentUnit = self.ExCall_CreateNewRealCTUnit_FromBaseCTUnit( strContent, tryDecodeUnit)
                # 是否已经注册的回调功能?
                if( execCallBackUnit and newExecContentUnit and execCallBackUnit.s_func_CallBack):
                    execCallBackUnit.s_func_CallBack( strFromName, execCallBackUnit.s_CallBack_Param1, execCallBackUnit.s_CallBack_Param2,
                                                     newExecContentUnit, execCallBackUnit)
                else:
                    # 非注册形式
                    bRetResult = True
                    strRetFrom = strFromName

            # 更新数据记录的状态
            CTYLBDB_tpd_inout_text.UpdateField_PeerStatus(self.s_opSQLiteDB.s_dbConn, iFreeRecID, 2)
            CTYLBDB_tpd_inout_text.UpdateField_ReplyTime(self.s_opSQLiteDB.s_dbConn, iFreeRecID, datetime.now())

        return bRetResult, strRetFrom, retRecvTime, retTylbP2PContUnit

    # 提交发送数据单元
    # start by sk. 170205
    def ExCall_SendContent(self, strDestUser, tylbP2PContUnit):
        bRetValue = False
        if( tylbP2PContUnit and self.s_opSQLiteDB and self.s_opSQLiteDB.s_dbConn):
            bRetValue = True
            strSendBuff = tylbP2PContUnit.EX_CombPacket()
            bstrSendBuffUTF8 = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strSendBuff)
            # 写入db
            iInputype = 0
            iPeerStatus = 0
            timeCreate = datetime.now()
            CTYLBDB_tpd_inout_text.AddNewdRec(self.s_opSQLiteDB.s_dbConn, iInputype, bstrSendBuffUTF8, self.s_strSelfName,
                                              strDestUser, iPeerStatus, timeCreate, None)
        return bRetValue

# 主执行运行类
# start by sk. 161118
# update to p2p tylb chat. by sk. 170128
# dev into sample-excall-subclient. by sk. 170205
class CTYLB_Bot_Sk_Entry_Main:
    # s_strMyName = 'name_modify_from_config'
    # s_p2p_ChatMain_SubUnitReal = None    # 客户端通信操作实现单元对象

    def __init__(self, ustrConfigName, ustrDbFileName):
        clientConfig = CTYLB_Client_Config()
        clientConfig.ReadFromConfigFile( ustrConfigName)
        self.s_strMyName = clientConfig.s_strMyID
        self.s_p2p_ChatMain_SubUnitReal = CTYLB_P2P_ExCall_SubClient_Realize( self.s_strMyName, ustrDbFileName, sample_TYLB_P2P_Call_CreateNew_P2PContentUnit)
        pass

    # 运行前的准备工作，可以继承
    # start by sk. 170213
    def Vil_Run_Prepare(self):
        pass

    # 运行调用。不断调用，可以继承
    # start by sk. 170213
    def Vil_Run_TimeCheck(self):
        bRetValue = False

        # check msg
        bRetResult, strRetFrom, retRecvTime, retTylbP2PContUnit = self.s_p2p_ChatMain_SubUnitReal.ExCall_Timer_CheckRecv()
        if (bRetResult):
            # strTime = datetime.now().strftime('%H:%M:%S')
            # print u'  <<<[%s] [%s] Msg [%s]' % (strTime, strRetFrom, retTylbP2PContUnit.s_strMyChatText)
            pass

        return bRetValue

    # 停止运行。，可以继承
    # start by sk. 170213
    def Vil_Run_Stop(self):
        pass

    # 外部功能调用 － 增加回调单元. 如果相同条件的回调单元已经存在，则返回False
    # start by sk. 170213
    def ExCall_Register_CallBackFunc(self, iDataType, iMainCmd, iSubCmd, param1, param2, funcCreateNewUnit, funcCallBack):
        reportStatusCallBack = CTYLB_Bot_G_CallBack_DefUnit(iDataType, iMainCmd, iSubCmd, param1, param2, funcCreateNewUnit, funcCallBack)
        self.s_p2p_ChatMain_SubUnitReal.ExCall_AddCallBackUnit( reportStatusCallBack)

    # 外部功能调用 － 增加回调单元. 如果相同条件的回调单元已经存在，则返回False
    # start by sk. 170213
    def ExCall_Register_SubCmd_Range_CallBackFunc(self, iDataType, iMainCmd, iSubCmdStart, iSubCmdEnd, param1, param2, funcCreateNewUnit, funcCallBack):
        reportStatusCallBack = CTYLB_Bot_G_CallBack_DefUnit(iDataType, iMainCmd, 0, param1, param2, funcCreateNewUnit, funcCallBack)
        reportStatusCallBack.SetCompareTypeRange( iSubCmdStart, iSubCmdEnd)
        self.s_p2p_ChatMain_SubUnitReal.ExCall_AddCallBackUnit( reportStatusCallBack)


    # 外部功能调用 － 提交单元进行发送
    # start by sk. 170213
    def ExCall_Prompt_Unit_To_Send(self, strDestUser, newContentUnit):
        # newContentUnit = CChat_P2P_SkTest_ContentUnit()
        # newContentUnit.s_strMyChatText = 'input content'
        # print 'prompt_send to %s [%d %d-%d] [%s]' % (strDestUser, newContentUnit.s_iMyDataType, newContentUnit.s_iBotCmd_Main,
        #                                             newContentUnit.s_iBotCmd_Sub, newContentUnit.s_strUniqueSign)
        self.s_p2p_ChatMain_SubUnitReal.ExCall_SendContent( strDestUser, newContentUnit)



# ################################################################################################
#   实现 模拟系统命令到达通知的途径 通信单元实现
# ################################################################################################
# start by sk. 170505
def CTYBot_CTUnit_CreateNewUnit_SimuSystemNotify():
    newContentUnit = CTYBot_CTUnit_SimuSystemNotify()
    return newContentUnit


# ################################################################################################
#   重写 内容单元类，系统通知数据包格式
#    通用的数据格式,  主命令，s_g_iDataType_SimuSystemNotify
#           s_g_iSubCmd_SimuSystemNotify # 子命令。
#   命令包含：来源用户，数据类型，参数类型
# start by sk. 170505
# ################################################################################################
class CTYBot_CTUnit_SimuSystemNotify(CTYLB_P2P_ContentUnit_Base):
    s_g_iType_Notify_Peer_Online = 0   # 通知对方在线类型
    s_g_iType_Notify_PeerServer_Restart = 1   # 通知对方在线类型

    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, s_g_iDataType_SimuSystemNotify)
        self.self_SetCmd(s_g_iMainCmd_SimuSystemNotify, s_g_iSubCmd_SimuSystemNotify)
        self.s_iNotifyParam = 0  # 通知int参数。类型=0时，为状态
        self.s_iNotifyType = 0   # 通知类型, 0 -- 通知伙伴系统连接状态
        self.s_strNotifyParam = ''  # 通知参数。类型=0时，为来源用户
        pass

    # 子类必须重写，被基类调用 － 设置数据格式
    def SetNotifyTypeData(self, iType, iParam, strParam):
        self.s_iNotifyParam = iParam
        self.s_iNotifyType = iType
        self.s_strNotifyParam = strParam

    s_g_Key_iNotifyParam = 'iNotifyParam'
    s_g_Key_iNotifyType = 'iNotifyType'
    s_g_Key_strNotifyParam = 'strNotifyParam'

    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[CTYBot_CTUnit_SimuSystemNotify.s_g_Key_iNotifyParam] = self.s_iNotifyParam
        exDict[CTYBot_CTUnit_SimuSystemNotify.s_g_Key_iNotifyType] = self.s_iNotifyType
        exDict[CTYBot_CTUnit_SimuSystemNotify.s_g_Key_strNotifyParam] = self.s_strNotifyParam

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)


    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            curDict = json.loads(strExJsonContent)

            self.s_iNotifyParam = int(curDict[CTYBot_CTUnit_SimuSystemNotify.s_g_Key_iNotifyParam])
            self.s_iNotifyType = int(curDict[CTYBot_CTUnit_SimuSystemNotify.s_g_Key_iNotifyType])
            self.s_strNotifyParam = curDict[CTYBot_CTUnit_SimuSystemNotify.s_g_Key_strNotifyParam]
        except:
            pass
        pass

