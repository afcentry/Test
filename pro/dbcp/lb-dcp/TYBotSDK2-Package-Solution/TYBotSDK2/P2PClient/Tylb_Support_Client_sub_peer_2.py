# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Support_Client_sub_peer_2.py support client realize function 主文件部分功能转移的并行子文件
#
# copy & start by sk. 170601
# update by sk. to V3. 修改通信数据格式为json内容

from datetime import datetime
from .Tylb_p2p_share import CTY_YamlFile, \
    CTYLB_Ct_NetBase_bytes, CTYLB_Mang_BusisUnit_Base_bytes, CTYLB_ShakeHand_NetBase_bytes, CTYLB_SvClt_Cmd_Base_bytes,\
    CTYLB_Busis_Packet, CTYLB_Comb_PackArray, CTYLB_Log, CTYLB_MainSys_MiscFunc
from .Tylb_p2p_Busines_func import CT2P_SHand_Ct_Srv
from .Tylb_p2p_Db_console import CTYLBDB_tpd_peek_ack, CTYLBDB_tpd_send_recv_session, CTYLBDB_tpd_session_data,\
    CTYLBDB_tpd_inout_text
import struct
import json


# 客户端配置内容读取类
# start by sk. 170123
class CTYLB_Client_Config:
    s_iMaxSrvCount = 128

    def __init__(self):
        self.s_strSrvAddrArray = []
        self.s_strMyID = None
        self.s_iClientListenPort = 88

    # Service run main.
    # start by sk. 170116
    def ReadFromConfigFile(self, strCfgFileName):
        self.s_strSrvAddrArray = []

        yamlClientRead = CTY_YamlFile( strCfgFileName)
        yamlClientRead.load_configs()

        self.s_strMyID = yamlClientRead.get_config("client.myid", 'notinput')
        self.s_iClientListenPort = yamlClientRead.get_config("client.client_listen_port", 0)

        for server in yamlClientRead.get_config('client.servers'):
            strSrvAddr = server['addr']
            iSrvPort = server['port']


            if strSrvAddr == ''  or  strSrvAddr == '0'  or  iSrvPort == 0 :
                continue
            self.s_strSrvAddrArray.append( (strSrvAddr, iSrvPort) )



# 用户信息存储执行传输管理单元
# start by sk. 170129
class CTYLB_Trans_Exec_StoreUser_Unit:
    def __init__(self, strFromUser, strDestUser):
        self.s_strFromUser = strFromUser
        self.s_strDestUser = strDestUser
        self.s_needSendBusisPackArray = []  # CTYLB_Busis_Packet 单元队列

    def __del__(self):
        del self.s_needSendBusisPackArray
        self.s_needSendBusisPackArray = None

    def __cmp__(self, other):
        iRetValue = 0
        if( self.s_strFromUser > other.s_strFromUser):
            iRetValue = 1
        elif( self.s_strFromUser < other.s_strFromUser):
            iRetValue = -1
        else:
            if( self.s_strDestUser > other.s_strDestUser):
                iRetValue = 1
            elif( self.s_strDestUser < other.s_strDestUser):
                iRetValue = -1
        return iRetValue

    def AddPacket(self, busisPacketUnit):
        if( not isinstance(busisPacketUnit.s_iBusiCmdID, int)):
            CTYLB_Log.ShowLog(1, 'error', 'int64???')
        iPacketLength = len(busisPacketUnit.s_strContent)
        if( iPacketLength >100000):
            CTYLB_Log.ShowLog(0, 'add huge packet', 'len:%d'%(iPacketLength))
        self.s_needSendBusisPackArray.append( busisPacketUnit)

    # 转换，综合成可发送的数据包队列，返回string
    #  iMaxBuffSize --- 最大的缓冲大小
    # start by sk. 170128
    def Convert_Pop_Comb_SendPacketArray(self, iMaxBuffSize = 0):
        # 每次调度发送16个数据包过去
        iCurPackSize = 0
        eachSendUnitArray = []
        strRetSendTotalPacket = ''

        while( True):
            if( len(self.s_needSendBusisPackArray) == 0):
                break
            curNextPackUnit = self.s_needSendBusisPackArray.pop(0)
            iCurPackSize += curNextPackUnit.NearCalcTransLength()
            eachSendUnitArray.append(curNextPackUnit)

            # 达到了单元大小，调度，发送
            if( iMaxBuffSize > 0):
                if( iCurPackSize >= iMaxBuffSize):
                    strRetSendTotalPacket = CTYLB_Comb_PackArray.GetCombindData(eachSendUnitArray)
                    eachSendUnitArray = []
                    break
        if( len(eachSendUnitArray) > 0):
            strRetSendTotalPacket = CTYLB_Comb_PackArray.GetCombindData(eachSendUnitArray)
        return strRetSendTotalPacket


# 客户端使用，远程客户端通知信息记录单元
# start by sk. 170128
class CTYLB_Client_RemoteClientNotifyUnit:
    s_g_iMaxSessIDCacheTime = 10  # 存储10秒内发送记录
    def __init__(self, strName):
        self.s_strClientName = strName
        self.s_lastActiveTime = datetime(2017,1,1)
        self.s_lastSendSessionIDValueArray = []    # 已经发送的ID记录和时间队列
        self.s_lastSendTimeArray = []   # send time

    def GetLastIdleTimeSeconds(self):
        iRetSeconds = 1000000   # 假定开始很长时间
        if( self.s_lastActiveTime):
            diffTime = datetime.now() - self.s_lastActiveTime
            iRetSeconds = diffTime.seconds
        return iRetSeconds

    # 增加发送的会话ID缓冲记录
    def AddSendSessionIDCache(self, iRecSessionIDValue):
        if( iRecSessionIDValue in self.s_lastSendSessionIDValueArray):
            # 以前存在，更新
            iOldIndex = self.s_lastSendSessionIDValueArray.index(iRecSessionIDValue)
            self.s_lastSendTimeArray[iOldIndex] = datetime.now()
        else:
            # 不存在，增加
            self.s_lastSendSessionIDValueArray.append(iRecSessionIDValue)
            self.s_lastSendTimeArray.append(datetime.now())

    # 判断会话ID是否存在
    def IsSessionIDExist(self, iRecSessionIDValue):
        bRetValue = False
        if( iRecSessionIDValue in self.s_lastSendSessionIDValueArray):
            bRetValue = True
        return bRetValue

    # 检查时间 执行
    def TimerCheck(self):
        lenCount = len(self.s_lastSendSessionIDValueArray)
        for i in range(lenCount):
            # 将超过10秒的记录删除
            iRevIndex = lenCount - i -1
            curTime = self.s_lastSendTimeArray[iRevIndex]
            if( CTYLB_MainSys_MiscFunc.CheckIdleTime(curTime, self.s_g_iMaxSessIDCacheTime)):
                self.s_lastSendTimeArray.pop(iRevIndex)
                self.s_lastSendSessionIDValueArray.pop(iRevIndex)
        pass

    # 重新初始化
    # start by sk. 180318
    def Reset(self):
        self.s_lastActiveTime = datetime(2017,1,1)
        self.s_lastSendSessionIDValueArray = []    # 已经发送的ID记录和时间队列
        self.s_lastSendTimeArray = []   # send time

# 需要辨别的管套单元
# start by sk. 170124
class CTYLB_Ct_NeedIdentifyNetUnit(CTYLB_ShakeHand_NetBase_bytes):
    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_ShakeHand_NetBase_bytes.__init__(self, socketValue, iSockType, peerNetAddr)
        pass

# 管理辨别单元队列
# start by sk. 170124
class CTYLB_Ct_Mang_NeedIdentify(CTYLB_Mang_BusisUnit_Base_bytes):

    def __init__(self, strClientName):
        CTYLB_Mang_BusisUnit_Base_bytes.__init__(self, strClientName)

    def __del__(self):
        pass

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        newServerUnit = CTYLB_Ct_NeedIdentifyNetUnit(socketValue, iSockType, peerAddress)
        return newServerUnit

    # 管套接收数据调度
    # modify by sk. 170217, 传入管理资源参数队列 CTYLB_Global_UnivTrans_Param
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, strRecvData_tbytes):
        CTYLB_Mang_BusisUnit_Base_bytes._Viul_HandleSockRecvPacket( self, mangClientUnivealParam, socketValue, strRecvData_tbytes)
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol
        strReplyContent_bytes = b''

        identifyUnit = self.SearchUnitBySockValue( socketValue)
        if ( not identifyUnit):
            iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock
        else:
            bProtocolOK = False

            # 是accept对象
            if (identifyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                # 解包对方发送的post内容，如果正确，我回应 http结果
                bExactResult, strFromUniqueSign, tyCmdUnit, strFromUser, strDestUser, buildTime, strUnHandleBuff_tbytes =\
                    CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket( strRecvData_tbytes, True)
                if (bExactResult and tyCmdUnit):
                    # 我是accept，对方主动连接，对方是服务端，我是client，所以，对方先发一个pass包过来。
                    if( identifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None):
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_7_Connect_SendCheck):
                            if( tyCmdUnit.s_iSubCmd == CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Ct_7_None):
                                # 我构建汇报包进行发送
                                strReplyContent_tbytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                                    strFromUniqueSign, CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_1_ReportName,
                                    CT2P_SHand_Ct_Srv.s_iSubCmd_Ct_Sv_1_None, '', '', self.s_strMySelfName, False)
                                identifyUnit.TempShort_ExecSendPacket( strReplyContent_tbytes)
                                identifyUnit.SetShakeHandResult( True)
                                iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData
                                bProtocolOK = True
                pass
            # 是connect对象
            elif (identifyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 我已经发送了post内容，对方回应 http结果，此处进行分析解包
                bExactResult, strReplyTransUniqueSign, tyCmdUnit, strFromUser, strDestUser, buildTime,\
                    strUnHandleBuff_tbytes = CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket( strRecvData_tbytes, False)
                if (bExactResult and tyCmdUnit):
                    identifyUnit.GiveBack_SessionUniqueSign( strReplyTransUniqueSign)   # 归还释放会话占用标识符
                    # 我已经发送了握手包－告诉对方我的名字， 等待对方回应
                    if( identifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1):
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_2_ReplySrvName):
                            if (tyCmdUnit.s_iSubCmd == CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Ct_2_None):
                                iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply
                                bProtocolOK = True
                                # 握手成功
                                identifyUnit.SetShakeHandResult( True)
                pass
            if( not bProtocolOK):
                identifyUnit.SetShakeHandResult( False)
        return iReplyCode

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False

        for eachUnit in self.s_mangUnitArray:
            # 是否主动连接？
            if (eachUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 状态是否在等待未执行
                if( eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None):
                    if (eachUnit.Is_LastSend_IdleTime_LargeThan(3)):
                        # 构建握手包，进行发送
                        strTransUniqueSign = eachUnit.Request_Free_SessionUniqueSign()  # 申请会话占用标识符
                        strSendPacket_tbytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit( strTransUniqueSign,
                            CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_1_ReportName,
                            CT2P_SHand_Ct_Srv.s_iSubCmd_Ct_Sv_1_None, '', '', self.s_strMySelfName, True)
                        bRetSucc = eachUnit.TempShort_ExecSendPacket( strSendPacket_tbytes)

                        eachUnit.s_iShakeHandStepStatus = CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1 if bRetSucc else \
                            CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_PeerClose
                        bRetValue = True
                    pass
                elif( eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1):
                    # 已经发送了第一个包，等待时间判断
                    if( eachUnit.Is_LastSend_IdleTime_LargeThan(CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxWaitHandSecond)):
                        eachUnit.SetShakeHandResult( False)
            # 如果是被动连接，是否长时间无内容接收，如果是，则关闭
            elif( eachUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                if (eachUnit.Is_LastSend_IdleTime_LargeThan(CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxWaitHandSecond)):
                    eachUnit.SetShakeHandResult(False)
                pass

        return bRetValue

    # 判断是否有对象成功完成辨别
    def Pop_Finish_Identify_Server(self):
        retUnit = None
        for eachUnit in self.s_mangUnitArray:
            if( (eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_OK) or
                    (eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_Fail)):
                self.s_mangUnitArray.remove( eachUnit)
                retUnit = eachUnit
                break
        return retUnit


# 平衡单元实现, iIndex＝-1，表示最后一个数据包到达
# start by sk. 170312
class CTYLB_MidBalance_SubUnit:
    s_g_bCmdPackSign = '_@#7jx$!A'

    def __init__(self, iBelongID=0, iIndex=0, iOrigSubCmd=0, strContent=''):
        self.s_iBelongID = iBelongID
        self.s_iIndex = iIndex
        self.s_iOrigSubCmd = iOrigSubCmd
        self.s_strContent = strContent
        pass

    s_g_Key_strFormat = 'strFormat'
    s_g_Key_iBelongID = 'iBelongid'
    s_g_Key_iIndex = 'iIndex'
    s_g_Key_iOrigSubCmd = 'iOrigSubCmd'
    s_g_Key_strContent = 'strContent'

    # 将内容输出成缓冲
    def CombBuffer(self):
        exDict = {}

        exDict[CTYLB_MidBalance_SubUnit.s_g_Key_strFormat] = self.s_g_bCmdPackSign
        exDict[CTYLB_MidBalance_SubUnit.s_g_Key_iBelongID] = self.s_iBelongID
        exDict[CTYLB_MidBalance_SubUnit.s_g_Key_iIndex] = self.s_iIndex
        exDict[CTYLB_MidBalance_SubUnit.s_g_Key_iOrigSubCmd] = self.s_iOrigSubCmd
        exDict[CTYLB_MidBalance_SubUnit.s_g_Key_strContent] = self.s_strContent

        strTotal = json.dumps(exDict, ensure_ascii=False)
        return strTotal

    # 将内容还原
    def ReadFromBuffer(self, strBuffer):
        self.s_iBelongID = 0
        self.s_iIndex = 0
        self.s_iOrigSubCmd = 0
        self.s_strContent = ''

        strOrigBuffer = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strBuffer)

        try:
            exDict = json.loads(strOrigBuffer)

            if( exDict[CTYLB_MidBalance_SubUnit.s_g_Key_strFormat] == self.s_g_bCmdPackSign):
                self.s_iBelongID = int(exDict[CTYLB_MidBalance_SubUnit.s_g_Key_iBelongID])
                self.s_iIndex = int(exDict[CTYLB_MidBalance_SubUnit.s_g_Key_iIndex])
                self.s_iOrigSubCmd = int(exDict[CTYLB_MidBalance_SubUnit.s_g_Key_iOrigSubCmd])
                self.s_strContent = exDict[CTYLB_MidBalance_SubUnit.s_g_Key_strContent]
        except:
            pass
        pass


# 平衡单元 通信存储单元 实现
# start by sk. 170312
class CTYLB_MidBalance_CommuStoreUnit:
    s_g_iEndIndex = -1

    def __init__(self, strFromUser, strDestUser, iBelongID):
        self.s_strFromUser = strFromUser
        self.s_strDestUser = strDestUser
        self.s_iBelongID = iBelongID
        self.s_balanceSubUnitArray = []  # 中间存储的子单元队列
        pass

    # 是否为空
    def IsEmpty(self):
        bRetValue = False
        if (len(self.s_balanceSubUnitArray) == 0):
            bRetValue = True
        return bRetValue

    # 是否完整，以－1结尾
    # start by sk. 170322
    def IsPacketComplete(self):
        bRetValue = False
        iUnitCount = len(self.s_balanceSubUnitArray)
        if (iUnitCount > 0):
            lastUnit = self.s_balanceSubUnitArray[iUnitCount - 1]
            if (lastUnit.s_iIndex == CTYLB_MidBalance_CommuStoreUnit.s_g_iEndIndex):
                bRetValue = True
        return bRetValue

    # 获得完成的内容，如果没有完成包接收到，那么，返回空
    def RetriveFinishBuff(self):
        bRetPacketError = False
        iRetOrigSubCmd = 0
        strRetOrigBuff = ''

        iLen = len(self.s_balanceSubUnitArray)
        if (iLen > 0):
            lastUnit = self.s_balanceSubUnitArray[iLen - 1]
            # 最后一个结尾已经到达？
            if (lastUnit.s_iIndex == CTYLB_MidBalance_CommuStoreUnit.s_g_iEndIndex):
                iNextCheckIndex = 0
                ustrSeq = ''
                for eachItem in self.s_balanceSubUnitArray:
                    if (eachItem.s_iIndex == CTYLB_MidBalance_CommuStoreUnit.s_g_iEndIndex):
                        iNextCheckIndex = CTYLB_MidBalance_CommuStoreUnit.s_g_iEndIndex
                    elif (iNextCheckIndex == eachItem.s_iIndex):
                        ustrSeq += '-%d ' % (eachItem.s_iIndex)
                        iNextCheckIndex += 1
                    else:
                        ustrSeq += '-%d ' % (eachItem.s_iIndex)
                        bRetPacketError = True
                        strRetOrigBuff = ''
                        # 出错了。次序接收错误，丢弃此包
                        CTYLB_Log.ShowLog(1, 'Mid_Balance', "Packet Sequence Error.%d: count:%d [%s]" % (
                            self.s_iBelongID, len(self.s_balanceSubUnitArray), ustrSeq))
                        break
                    strRetOrigBuff += eachItem.s_strContent
                iRetOrigSubCmd = lastUnit.s_iOrigSubCmd
        return bRetPacketError, self.s_strFromUser, self.s_strDestUser, iRetOrigSubCmd, strRetOrigBuff

    # 增加中间子单元
    def AddSubUnit(self, iIndex, iOrigCmd, strSubContent):
        # 如果此单元已经存在，不确定为何会重发，此处如果重复则丢弃
        bAddNew = True
        iLen = len(self.s_balanceSubUnitArray)
        if (iLen > 0):
            lastUnit = self.s_balanceSubUnitArray[iLen - 1]
            if (lastUnit.s_iIndex == iIndex):
                bAddNew = False
                CTYLB_Log.ShowLog(1, 'Mid_Balance', "  [%s->%s] %d  repeat,ignore %d,  len:%d" % (
                    self.s_strFromUser, self.s_strDestUser, self.s_iBelongID, iIndex, len(strSubContent)))
        if (bAddNew):
            newMidSubUnit = CTYLB_MidBalance_SubUnit(self.s_iBelongID, iIndex, iOrigCmd, strSubContent)
            self.s_balanceSubUnitArray.append(newMidSubUnit)

    # 获得下一个可发送的数据包
    def PopNextSendAbleBuff(self):
        strRetFromUser = ''
        strRetDestUser = ''
        iRetSubCmd = CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans
        strRetBuff = ''
        if (len(self.s_balanceSubUnitArray) > 0):
            nextSendUnit = self.s_balanceSubUnitArray.pop(0)
            strRetBuff = nextSendUnit.CombBuffer()
            strRetFromUser = self.s_strFromUser
            strRetDestUser = self.s_strDestUser

        return strRetFromUser, strRetDestUser, iRetSubCmd, strRetBuff


# 每个用户接收到的平衡单元队列
# start by sk. 170322
# add by sk。170502 修复中间线路断开，发送端重新置0，而接收端未置0，出现无法同步接收的状况。
#   如下： ... seq error. discard the unit [b'xxx1' -> b'xxx2'] last:168 recv:20
#    修改方法如下：增加错误连续变量。当正常接收，设置错误连续变量0，当达到多次持续连续错误时，重置系统数据值
class CTYLB_MidBala_UserRecv_BuffArray:
    s_g_iMaxErrorRepeatCount = 3  # 最大错误重试计数。达到后，重新清0

    def __init__(self, strFromUser, strDestUser):
        self.s_strFromUser = strFromUser
        self.s_strDestUser = strDestUser
        self.s_iLastParamIndex = 0  # 最后可用的索引参数
        self.s_bala_Fix_RecvUnitArray = []  # 接收到的队列  CTYLB_MidBalance_CommuStoreUnit
        self.s_iLastRetriveRecvBelongIndex = 0  # 最后获取的索引参数
        self.s_iErrorRepeatCount = 0  # 错误连续计数

    # 获得，并且自增，唯一索引参数
    # start by sk. 170323
    def GetIncLastIndex(self):
        iRet = self.s_iLastParamIndex
        self.s_iLastParamIndex += 1
        return iRet

    # 根据单元ID，搜索中间存储单元
    def Search_Add_MidStoreUnit_in_RecvArray_By_BelongID(self, iBelongID, bAddNew=True):
        retFoundItem = None
        for eachItem in self.s_bala_Fix_RecvUnitArray:
            if (eachItem.s_iBelongID == iBelongID):
                retFoundItem = eachItem
                break
        if ((not retFoundItem) and bAddNew):
            self.__Check_NotFinish_MidUnit(u'add-stor-unit')
            bAddNewUnitToLink = True

            iRecvUnitLen = len(self.s_bala_Fix_RecvUnitArray)
            if (iRecvUnitLen > 0):
                lastPackUnit = self.s_bala_Fix_RecvUnitArray[iRecvUnitLen - 1]
                iLastBelongID = lastPackUnit.s_iBelongID
                if (iBelongID <= iLastBelongID):
                    if (iBelongID < 2):
                        # 对方重新连接。以前全部未完成的作废。
                        CTYLB_Log.ShowLog(1, 'user mid balan',
                                          'seq error. maybe peer[%s] re-connect' % (self.s_strFromUser))
                        self.s_bala_Fix_RecvUnitArray = []
                    else:
                        CTYLB_Log.ShowLog(1, 'user mid balan',
                                          'seq error. discard the unit [%s -> %s] last:%d recv:%d' % (
                                              self.s_strFromUser, self.s_strDestUser, iLastBelongID, iBelongID))
                        bAddNewUnitToLink = False
                        self.s_iErrorRepeatCount += 1  # 增加错误计数
                elif (iBelongID > iLastBelongID + 1):
                    CTYLB_Log.ShowLog(1, 'user mid balan',
                                      '[%s -> %s] seq error. still add to link, unContinue Seq: last:%d recv:%d'
                                      % (self.s_strFromUser, self.s_strDestUser, iLastBelongID, iBelongID))
                else:
                    # 此处正常。可以增加到队列
                    pass

            if (bAddNewUnitToLink):
                self.s_iErrorRepeatCount = 0  # 正确，错误计数清0
                retFoundItem = CTYLB_MidBalance_CommuStoreUnit(self.s_strFromUser, self.s_strDestUser, iBelongID)
                self.s_bala_Fix_RecvUnitArray.append(retFoundItem)
            else:
                # 检查是否错误次数超过足够次数？
                if (self.s_iErrorRepeatCount >= self.s_g_iMaxErrorRepeatCount):
                    CTYLB_Log.ShowLog(1, 'user mid balan', 'seq error max count. reset recv buff')
                    self.s_bala_Fix_RecvUnitArray = []
                    self.s_iErrorRepeatCount = 0
        return retFoundItem

    # 增加的时候，进行已经存在检查，判断是否有未完成的数据单元。如果有，则告警
    def __Check_NotFinish_MidUnit(self, ustrPrefix):
        if (len(self.s_bala_Fix_RecvUnitArray) > 0):
            firstUnit = self.s_bala_Fix_RecvUnitArray[0]
            if (firstUnit.IsPacketComplete()):
                pass
            else:
                # CTYLB_Log.ShowLog(1, 'user mid balan', '%s -- old not finish unit exist. not valid [%s->%s : %d]' % (
                #     strPrefix, self.s_strFromUser, self.s_strDestUser, firstUnit.s_iBelongID))
                pass
        pass

    # 把接收到的数据，传入，如果是分割的，则需要加入队列，直到最后一个完成整合输出
    def Trans_OrigRecv_Data_Into_MidBalance_Buff(self, iOrigSubCmd, strOrigContent):
        if (strOrigContent):
            if (iOrigSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans):
                newMidSubUnit = CTYLB_MidBalance_SubUnit()
                newMidSubUnit.ReadFromBuffer(strOrigContent)

                bAddNewUnit = True if ((newMidSubUnit.s_iIndex == 0) or (newMidSubUnit.s_iIndex == -1)) else False
                midRecvComuUnit = self.Search_Add_MidStoreUnit_in_RecvArray_By_BelongID(newMidSubUnit.s_iBelongID,
                                                                                        bAddNewUnit)
                if (midRecvComuUnit):
                    midRecvComuUnit.AddSubUnit(newMidSubUnit.s_iIndex, newMidSubUnit.s_iOrigSubCmd,
                                               newMidSubUnit.s_strContent)
                else:
                    CTYLB_Log.ShowLog(1, 'trans add midbala', 'not know how to add packet unit.')
            else:
                CTYLB_Log.ShowLog(0, 'trans add midbala', 'direct-data %s->%s %d [%d].' % (
                    self.s_strFromUser, self.s_strDestUser, iOrigSubCmd, len(strOrigContent)))
                # 直接数据包
                newBalRecvUnit = CTYLB_MidBalance_CommuStoreUnit(self.s_strFromUser, self.s_strDestUser, 0)
                newBalRecvUnit.AddSubUnit(-1, iOrigSubCmd, strOrigContent)
                self.__Check_NotFinish_MidUnit(u'add-non-cmd-direct-unit')
                self.s_bala_Fix_RecvUnitArray.append(newBalRecvUnit)
        pass

    # 获得经过还原的平衡接收数据包
    def Retrive_Pop_Sub_Next_Balaned_RecvOrigPacket(self):
        bRetHaveContent, strRetFromUser, strRetDestUser = False, '', ''
        iRetOrigSubCmd, strRetOrigBuff, iRetBelongID = 0, '', 0
        # 当前数据包有否接收完成。如果没有，并且下一个已经接收到，那么，丢弃当前未完的数据包
        iRecvLen = len(self.s_bala_Fix_RecvUnitArray)
        if (iRecvLen > 0):
            firstRecvStorUnit = self.s_bala_Fix_RecvUnitArray[0]
            bRetPacketError, strExeFromUser, strExeDestUser, iExecOrigSubCmd, strExecOrigBuff = firstRecvStorUnit.RetriveFinishBuff()
            iRetBelongID = firstRecvStorUnit.s_iBelongID
            # 如果第一个没有完成，并且存在第二个，那么，标记此单元失败，丢弃
            if ((not strExecOrigBuff) and (iRecvLen > 1)):
                bRetPacketError = True  # 直接设置数据包错误

            bPopPacket = False
            if (bRetPacketError):
                bPopPacket = True
                # 数据错误，丢弃此包
            elif (strExecOrigBuff):
                strRetFromUser = strExeFromUser
                strRetDestUser = strExeDestUser
                iRetOrigSubCmd = iExecOrigSubCmd
                strRetOrigBuff = strExecOrigBuff
                bPopPacket = True
                bRetHaveContent = True
            else:
                pass

            if (bPopPacket):
                self.s_bala_Fix_RecvUnitArray.pop(0)
        return bRetHaveContent, strRetFromUser, strRetDestUser, iRetOrigSubCmd, strRetOrigBuff, iRetBelongID

    pass


# 平衡缓冲功能管理实现.输入为：
# start by sk. 170312
# 增加获得还原输出数据包时，的返回客户端状态值。by sk. 170505
class CTYLB_MidBalance_InOutBuffMang:
    s_g_iPeerClient_Restart = 0  # 对方Client以前有会话，但是刚重启了
    s_g_iPeerClient_Normal_StartUp = 1  # 对方Client以前没有会话，刚启动
    s_g_iPeerClient_Normal_Recv = 2  # 对方Client正常接收
    s_g_iPeerClient_Normal_NoData = 3  # 对方Client正常，但还没有数据到达
    s_g_iPeerServer_Restart = 4  # 对方服务器重启了

    def __init__(self, iEachUnitMaxSize=20480):
        self.s_iEachUnitMaxSize = iEachUnitMaxSize
        self.s_userLastIndexArray = []  # 存储用户最后的索引值 CTYLB_MidBala_UserRecv_BuffArray
        self.s_bala_Fix_ToBe_SendUnitArray = []  # 已经平衡过的，等待发送单元队列。
        self.s_bala_Fix_User_RecvUnitArray = []  # 接收到的用户队列 CTYLB_MidBala_UserRecv_BuffArray

    # 获得可用的 唯一ID
    def GetUserLastIndex(self, strFromUser, strDestUser):
        retFoundUserItem = None
        for eachUserItem in self.s_userLastIndexArray:
            if ((eachUserItem.s_strFromUser == strFromUser) and (eachUserItem.s_strDestUser == strDestUser)):
                retFoundUserItem = eachUserItem
                break
        if (not retFoundUserItem):
            retFoundUserItem = CTYLB_MidBala_UserRecv_BuffArray(strFromUser, strDestUser)
            self.s_userLastIndexArray.append(retFoundUserItem)
        iRetValue = retFoundUserItem.GetIncLastIndex()
        return iRetValue

    # 根据单元ID，搜索中间存储单元
    def Search_Add_UserUnit_in_RecvArray(self, strFromUser, strDestUser, bAddUserNew=True):
        retFoundUserItem = None
        for eachUserItem in self.s_bala_Fix_User_RecvUnitArray:
            if ((eachUserItem.s_strFromUser == strFromUser) and (eachUserItem.s_strDestUser == strDestUser)):
                retFoundUserItem = eachUserItem
                break
        if ((not retFoundUserItem) and bAddUserNew):
            retFoundUserItem = CTYLB_MidBala_UserRecv_BuffArray(strFromUser, strDestUser)
            self.s_bala_Fix_User_RecvUnitArray.append(retFoundUserItem)

        return retFoundUserItem

    # 把接收到的数据，传入，如果是分割的，则需要加入队列，直到最后一个完成整合输出
    def Trans_OrigRecv_Data_Into_MidBalance_Buff(self, strFromUser, strDestUser, iOrigSubCmd, strOrigContent):
        if (strOrigContent):
            destOpUserItem = self.Search_Add_UserUnit_in_RecvArray(strFromUser, strDestUser, True)
            if (destOpUserItem):
                destOpUserItem.Trans_OrigRecv_Data_Into_MidBalance_Buff(iOrigSubCmd, strOrigContent)
            else:
                CTYLB_Log.ShowLog(1, 'trans-data', 'not found valid user unit to add %s->%s :%d' % (
                    strFromUser, strDestUser, iOrigSubCmd))
        pass

    # 获得经过还原的平衡接收数据包
    def Retrive_Pop_Next_Balaned_RecvOrigPacket(self):
        iRetPeerClientStatus = CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Normal_NoData
        strRetFromUser, strRetDestUser, iRetOrigSubCmd, strRetOrigBuff = '', '', 0, ''

        # 当前数据包有否接收完成。如果没有，并且下一个已经接收到，那么，丢弃当前未完的数据包
        for eachUserItem in self.s_bala_Fix_User_RecvUnitArray:
            bHaveContent, strExeFromUser, strExeDestUser, iExecOrigSubCmd, strExecOrigBuff, iExecBelongID = \
                eachUserItem.Retrive_Pop_Sub_Next_Balaned_RecvOrigPacket()
            if (bHaveContent):
                if (strExeFromUser and strExeDestUser and strExecOrigBuff):
                    strRetFromUser = strExeFromUser
                    strRetDestUser = strExeDestUser
                    iRetOrigSubCmd = iExecOrigSubCmd
                    strRetOrigBuff = strExecOrigBuff

                    if (iExecBelongID != eachUserItem.s_iLastRetriveRecvBelongIndex):
                        if (iExecBelongID == 0):
                            # 对方Client以前有会话，但是刚重启了
                            CTYLB_Log.ShowLog(0, 'mid-trans-data',
                                              'PeerClient %s Restart' % (eachUserItem.s_strFromUser))
                            iRetPeerClientStatus = CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Restart
                        else:
                            if (eachUserItem.s_iLastRetriveRecvBelongIndex == 0):
                                CTYLB_Log.ShowLog(0, 'trans-data', 'I restart, Reset peer session. %s ~ %d' % (
                                    eachUserItem.s_strFromUser, iExecBelongID))
                            else:
                                CTYLB_Log.ShowLog(1, 'trans-data', 'retrive balan unit. %s->%s need:%d, actual:%d' % (
                                    eachUserItem.s_strFromUser, eachUserItem.s_strDestUser,
                                    eachUserItem.s_iLastRetriveRecvBelongIndex, iExecBelongID))
                    else:
                        if (iExecBelongID == 0):
                            # 对方Client以前没有会话，刚启动
                            CTYLB_Log.ShowLog(0, 'mid-trans-data',
                                              'PeerClient %s StartUP' % (eachUserItem.s_strFromUser))
                            iRetPeerClientStatus = CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Normal_StartUp
                        else:
                            # 对方Client正常接收
                            iRetPeerClientStatus = CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Normal_Recv
                    eachUserItem.s_iLastRetriveRecvBelongIndex = iExecBelongID + 1
                    break
        return iRetPeerClientStatus, strRetFromUser, strRetDestUser, iRetOrigSubCmd, strRetOrigBuff

    # 把原始需要发送的数据读入。如果超过大小，进行分割提交发送
    def Trans_OrigNeedSend_Data_Into_MidBalance_Buff(self, strFromUser, strDestUser, iOrigSubCmd, strOrigContent):
        iTotalSize = len(strOrigContent)
        if(iTotalSize > 10000):
            iCurSize = 0
        iLastBelongIndex = self.GetUserLastIndex(strFromUser, strDestUser)
        newBalSendUnit = CTYLB_MidBalance_CommuStoreUnit(strFromUser, strDestUser, iLastBelongIndex)
        iSendIndex = 0
        if (iTotalSize > self.s_iEachUnitMaxSize):
            iCurSize = 0
            while (iCurSize < iTotalSize):
                iEndSize = iCurSize + self.s_iEachUnitMaxSize
                if (iEndSize > iTotalSize):
                    iEndSize = iTotalSize
                    iParamSendIndex = -1
                else:
                    iParamSendIndex = iSendIndex
                strMidContent = strOrigContent[iCurSize:iEndSize]
                newBalSendUnit.AddSubUnit(iParamSendIndex, iOrigSubCmd, strMidContent)
                iCurSize = iEndSize
                iSendIndex += 1
            pass
        else:
            # 直接存储成标准数据
            newBalSendUnit.AddSubUnit(-1, iOrigSubCmd, strOrigContent)
        self.s_bala_Fix_ToBe_SendUnitArray.append(newBalSendUnit)

    # 是否发送缓冲已经空了
    def IsSendBuffEmpty(self):
        bRetValue = False
        if (len(self.s_bala_Fix_ToBe_SendUnitArray) == 0):
            bRetValue = True
        return bRetValue

    # 是否接收缓冲已经空了
    def IsRecvBuffEmpty(self):
        bRetValue = True
        for eachUserItem in self.s_bala_Fix_User_RecvUnitArray:
            if (eachUserItem.s_bala_Fix_RecvUnitArray):
                bRetValue = False
                break
        return bRetValue

    # 获得下一个 经过平衡的，可发送的数据包.
    def Retrive_Pop_Next_Balaned_SendAblePacket(self):
        strRetFromUser = ''
        strRetDestUser = ''
        iRetCmd = 0
        strRetBuff = ''
        if (len(self.s_bala_Fix_ToBe_SendUnitArray) > 0):
            nextBalaExecUnit = self.s_bala_Fix_ToBe_SendUnitArray[0]
            strRetFromUser, strRetDestUser, iRetCmd, strRetBuff = nextBalaExecUnit.PopNextSendAbleBuff()
            # 本单元是否已经完成，如果已经空了，就删除
            if (nextBalaExecUnit.IsEmpty()):
                self.s_bala_Fix_ToBe_SendUnitArray.pop(0)
        return strRetFromUser, strRetDestUser, iRetCmd, strRetBuff

# 伙伴客户单元，业务单元
# start by sk. 170217
class CTYLB_Client_BusiUnit:
    s_g_iPeerAck_IdleSecond = 1   # 每1秒空闲检测一次
    s_g_iPeerAck_JustNowRecvNewData_Second = 5   # 5秒内接收到上次最新的数据?超过5秒再进行检查
    s_g_iReSendRec_IdleSecond = 30  # 每半分钟重新检查一次

    def __init__(self, strClientName):
        self.s_strClientName = strClientName
        self.s_lastCheckPeerAckTime = datetime.now()  # 上次检查peer_ack请求更多数据包的时间
        self.s_lastRecvUpdatePeerAckTime = datetime.now()  # 上次接收到新数据包，更新peer_ack的时间
        self.s_reSendRec_Exist_CheckTime = datetime.now()   # 重新发送数据包已经存在的检查时间

    # 更新 接收到数据包和peer_ack的时间
    def UpdateRecvSeqAckSession(self):
        self.s_lastRecvUpdatePeerAckTime = datetime.now()
        pass

    # 更新 上次执行发送 请求不存在记录的时间
    def Update_ReSend_Req_NonExistSession_RecTime(self):
        self.s_reSendRec_Exist_CheckTime = datetime.now()
        pass

    # 更新 接收到数据包和peer_ack的时间
    def Check_NeedRequest_UnSendPacket(self, mangClientUnivealParam):
        bExecCheck = False

        dbExecConn = mangClientUnivealParam.s_u_DbConn
        srvUnitMang = mangClientUnivealParam.s_u_SrvUnitMang
        strSelfName = mangClientUnivealParam.s_u_strMySelfIDName

        curTime = datetime.now()
        if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_lastCheckPeerAckTime, self.s_g_iPeerAck_IdleSecond)):
            self.s_lastCheckPeerAckTime = curTime

            # 是否刚收到连续数据？如果还在连续接收数据过程中，也继续等待，不用检查。否则可能造成数据正在接收，却不断发送请求要求继续发的冲突
            if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_lastRecvUpdatePeerAckTime, self.s_g_iPeerAck_JustNowRecvNewData_Second)):
                self.s_lastRecvUpdatePeerAckTime = curTime
                bExecCheck = True
                # 可以进行检查了
                # 是否数据库存在已经检查了的最后数据请求包？

                iLastMaxSessionID = CTYLBDB_tpd_peek_ack.GetMax_PeerName_SessionID(dbExecConn, self.s_strClientName)
                iSendRecvTypeArray = [CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeerReSend,
                                      CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeer_ReSend_Range]
                iLastMaxSessionID += 1
                iSessionRecID = 0

                for iEachType in iSendRecvTypeArray:
                    iSessionRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID(
                        dbExecConn, iEachType, strSelfName, self.s_strClientName, iLastMaxSessionID)
                    if( iSessionRecID > 0):
                        break
                if( iSessionRecID > 0):
                    # 记录已经存在。更新，请求进行重新发送
                    if(CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_reSendRec_Exist_CheckTime, self.s_g_iReSendRec_IdleSecond)):
                        # 设置状态＝0，重新发送
                        self.s_reSendRec_Exist_CheckTime = curTime
                        iOrigStatus = CTYLBDB_tpd_send_recv_session.ReadRec_Status( dbExecConn, iSessionRecID)
                        CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus(
                            dbExecConn, iSessionRecID, CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free)
                else:
                    self.s_reSendRec_Exist_CheckTime = curTime
                    # 记录不存在，增加, 执行检查
                    srvUnitArray = srvUnitMang.Get_ReachSendList_SrvUnit_By_RemotePeerName(self.s_strClientName)
                    if (len(srvUnitArray) > 0):
                        srvUnit = srvUnitArray[0]
                        srvUnit.Exec_Check_Request_ReSend_BetweenSessionStart(mangClientUnivealParam, strSelfName,
                                                                              self.s_strClientName, iLastMaxSessionID)
        return bExecCheck

# 管理在线的客户单元
# start by sk. 170217
class CTYLB_OnLineClient_Mang:
    s_g_iCheckTimeDiff = 2  # 查队列的时间，每2秒检查一次

    def __init__(self):
        self.s_clientUnitDict = {}
        self.s_lastCheckArrayTime = datetime.now()

    # 单位时间检查
    def TimerCheck(self, mangClientUnivealParam):
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        srvUnitMang = mangClientUnivealParam.s_u_SrvUnitMang

        bRetValue = False
        curTime = datetime.now()
        timeDiff = curTime - self.s_lastCheckArrayTime
        if( timeDiff.seconds >= CTYLB_OnLineClient_Mang.s_g_iCheckTimeDiff):
            bRetValue = True
            self.s_lastCheckArrayTime = curTime
            self.__RefreshFromSrvUnitMang( srvUnitMang)

        if( self.__ExecCheck_NeedRequest_Client_UnSendPacket( mangClientUnivealParam)):
            bRetValue = True

        return bRetValue

    # 对客户端进行检查，看是否有需要重新发送的数据包
    def __ExecCheck_NeedRequest_Client_UnSendPacket(self, mangClientUnivealParam):
        bRetValue = False
        for eachClient in self.s_clientUnitDict.values():
            if( eachClient.Check_NeedRequest_UnSendPacket( mangClientUnivealParam)):
                bRetValue = True
        return bRetValue

    # 从服务端管理对象，刷新在线客户单元列表
    def __RefreshFromSrvUnitMang(self, srvUnitMang):
        strOnLineClientNameArray = []
        for eachSrvUnit in srvUnitMang.s_mangUnitArray:
            strOnLineClientNameArray.extend(set(eachSrvUnit.s_peerRemoteClientList.keys()))
        # 去除重复
        strOnLineClientNameArray = list(set(strOnLineClientNameArray))

        # 更新我的客户端单元队列

        # 将所有的初始化为要删除
        strNeedRemoveArray = []
        for eachClient in self.s_clientUnitDict.values():
            strNeedRemoveArray.append( eachClient.s_strClientName)
        # 去除每个在线的
        for strEachOnlineName in strOnLineClientNameArray:
            if( strEachOnlineName in strNeedRemoveArray):
                strNeedRemoveArray.remove( strEachOnlineName)
            else:
                # 在线的单元，不在我的队列。
                self.__CheckAddClientUnit( strEachOnlineName)
        # 剩下就是不在线的
        for strEachOffLine in strNeedRemoveArray:
            self.Remove_ClientUnit_By_Name( strEachOffLine)
        pass

    # 检查，增加新的客户端单元
    def __CheckAddClientUnit(self, strClientName):
        existClientUnit = self.Search_ClientUnit_By_Name( strClientName)
        if( not existClientUnit):
            existClientUnit = CTYLB_Client_BusiUnit( strClientName)
            self.s_clientUnitDict[strClientName] = existClientUnit
        return existClientUnit

    # 根据客户名字，搜索客户单元
    def Search_ClientUnit_By_Name(self, strClientName):
        retClientUnit = None

        if( strClientName in self.s_clientUnitDict.keys()):
            retClientUnit = self.s_clientUnitDict[strClientName]

        return retClientUnit

    # 根据客户名字，删除该单元
    def Remove_ClientUnit_By_Name(self, strClientName):
        if( strClientName in self.s_clientUnitDict.keys()):
            self.s_clientUnitDict.pop(strClientName)

    # 更新伙伴客户端单元，顺序应答会话
    def UpdatePeerClientRecvSeqAckSession(self, strClientName):
        clientUnit = self.__CheckAddClientUnit( strClientName)
        if( clientUnit):
            clientUnit.UpdateRecvSeqAckSession()

    # 更新伙伴客户端单元，自己发送 请求不存在记录的时间
    def Update_SelfReSend_ReqNonExistSession_Time(self, strClientName):
        clientUnit = self.__CheckAddClientUnit( strClientName)
        if( clientUnit):
            clientUnit.Update_ReSend_Req_NonExistSession_RecTime()

    pass
