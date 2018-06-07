# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Support_Client.py support client realize function
#
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# update by sk. to V3. 修改通信数据格式为json内容

from .Tylb_p2p_share import CTYLB_Global_UnivTrans_Param
from datetime import datetime
import signal
from .Tylb_p2p_share import CTCPAcceptConnectMangClient_bytes, CExecConnectSockMang_bytes, CTCPListenSock, \
    CTYLB_Ct_NetBase_bytes, CTYLB_Mang_BusisUnit_Base_bytes, CTYLB_ShakeHand_NetBase_bytes, CTYLB_SvClt_Cmd_Base_bytes,\
    CTYLB_Busis_Packet, CTYLB_Comb_PackArray, CTYLB_Log, CTYLB_MainSys_MiscFunc
from .Tylb_p2p_Busines_func import CT2P_SHand_Ct_Srv
import queue
from .Tylb_p2p_Db_console import CTYLBDB_tpd_peek_ack, CTYLBDB_tpd_send_recv_session, CTYLBDB_tpd_session_data,\
    CTYLBDB_tpd_inout_text
from .Tylb_p2p_Db_Share import CTYLB_SQLite_DB_Conn  # 数据库共享功能实现
import struct
import json
from .Tylb_Support_Client_sub_peer_2 import CTYLB_Trans_Exec_StoreUser_Unit, CTYLB_Client_RemoteClientNotifyUnit,\
    CTYLB_Client_Config, CTYLB_Ct_Mang_NeedIdentify, CTYLB_MidBalance_InOutBuffMang, CTYLB_OnLineClient_Mang

# 服务端单元
# start by sk. 170124
class CTYLB_Ct_ServerUnit(CTYLB_Ct_NetBase_bytes):
    s_g_iRequestClientListTimeCheck = 5  # 等待10秒
    s_g_iRequestOffLineUserTimeCheck = 5  # 等待10秒
    s_g_iMaxReSendOneRecCount = 100  # 最多重发的记录个数

    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_Ct_NetBase_bytes.__init__(self, socketValue, iSockType, peerNetAddr)
        self.s_bDataFormatBadClose = False
        self.s_peerRemoteClientList = {}   # 我的客户端单元队列 CTYLB_Client_RemoteClientNotifyUnit, key=名字
        self.s_toServerStoreUnit = CTYLB_Trans_Exec_StoreUser_Unit('self', 'server')  # 到服务端的存储单元 CTYLB_Trans_Exec_StoreUser_Unit
        self.s_lastRequestClientListTime = datetime.now()
        self.s_midBalanceInOutBuffMang = CTYLB_MidBalance_InOutBuffMang()  # 中间平衡队列管理
        pass

    def __del__(self):
        pass

    # 检查上次发送请求客户端列表的时间
    # start by sk. 170129
    def ExecTimerCheck(self, mangClientUnivealParam):
        timeDiff = datetime.now() - self.s_lastRequestClientListTime
        if( timeDiff.seconds >= CTYLB_Ct_ServerUnit.s_g_iRequestClientListTimeCheck):
            self.s_lastRequestClientListTime = datetime.now()
        # 每个客户端进行时间检查
        for eachClientUnit in self.s_peerRemoteClientList.values():
            eachClientUnit.TimerCheck()

    # 直接提交命令数据包，发送到服务端队列
    # start by sk. 170128
    def DirectPromptCmdSendToSrv(self, iBusisCmdType, strPacketContent=''):
        newExecBusisPacket = CTYLB_Busis_Packet(iBusisCmdType, 0, 0, 0, strPacketContent)
        self.s_toServerStoreUnit.AddPacket(newExecBusisPacket)

    def IsClientInMyArray(self, strRemoteName):
        clientUnit = self.__GetCLientNameUnit( strRemoteName)
        bExist = True if clientUnit else False
        return bExist

    def __GetCLientNameUnit(self, strRemoteClientName):
        retClientUnit = None

        if( strRemoteClientName in self.s_peerRemoteClientList.keys()):
            retClientUnit = self.s_peerRemoteClientList[strRemoteClientName]
        return retClientUnit

    # 处理，通知用户到达
    # start by sk. 170128
    def __Handle_NotifyUserArrive(self, strRemoteUser):
        if( self.IsClientInMyArray( strRemoteUser)):
            pass
        else:
            newClient = CTYLB_Client_RemoteClientNotifyUnit( strRemoteUser)
            self.s_peerRemoteClientList[strRemoteUser] = newClient

    # 处理接收到的，可到达的客户端列表
    # start by sk. 170128
    def __HandleRecv_RearchAbleClientList(self, dbConn, strRecvPackContent):
        strClientArray = CTYLB_SvClt_Cmd_Base_bytes.Exact_MultiClientNameList_Packet( strRecvPackContent)
        # 清除旧单元列表中，不存在的单元
        for strEachOldClientName in self.s_peerRemoteClientList.keys():
            if(strEachOldClientName not in strClientArray):
                self.s_peerRemoteClientList.pop(strEachOldClientName)
        # 增加新出现的单元
        for strEachClient in strClientArray:
            if(strEachClient not in self.s_peerRemoteClientList.keys()):
                newClient = CTYLB_Client_RemoteClientNotifyUnit( strEachClient)
                self.s_peerRemoteClientList[strEachClient] = newClient
        pass

    # 处理接收到的，上线客户列表名字
    # start by sk. 170204
    def __HandleRecv_OnLineReachClientList(self, dbConn, strRecvPackContent):
        strClientArray = CTYLB_SvClt_Cmd_Base_bytes.Exact_MultiClientNameList_Packet( strRecvPackContent)
        # 增加新出现的单元
        for strEachClient in strClientArray:
            if( strEachClient not in self.s_peerRemoteClientList.keys()):
                newClient = CTYLB_Client_RemoteClientNotifyUnit( strEachClient)
                self.s_peerRemoteClientList[strEachClient] = newClient
        pass

    # 虚函数 － 获得下一步可以立刻发送的所需条件, 包括 标识符.
    # start by sk. 170313
    def Viul_GetNextSendResource(self, iMaxIdleTime, iMaxSignBusyStillCheckTime):
        bCanExecSend = False
        strRetTransUniqueSign = ''

        bExecReqSend = False
        bExecTimerCheck = False
        # 缓冲平衡是否有需要发送的单元？ 或者要持续接收的单元?
        if( self.s_midBalanceInOutBuffMang.IsSendBuffEmpty() and self.s_midBalanceInOutBuffMang.IsRecvBuffEmpty()):
            # 没有需要立即调度发送，那么，按照老流程走
            bExecTimerCheck = True
        else:
            # 是否会话占用队列为空?
            if( len(self.s_SimulateUniqueArray) == 0):
                bExecReqSend = True
            else:
                # 会话占用至少一个忙，等待时间符合？
                bExecTimerCheck = True

        if( bExecTimerCheck):
            # 等待时间符合？
            if (self.CanActiveSendNow(iMaxIdleTime)):
                bExecReqSend = True

        if( bExecReqSend):
            strRetTransUniqueSign = self.Request_Free_SessionUniqueSign()  # 申请会话占用符
            if (strRetTransUniqueSign):
                bCanExecSend = True
            else:
                # 如果中间网络断开，会话占用一直未释放，那么，需要发送心跳包进行检测
                if (self.Is_LastSend_IdleTime_LargeThan(iMaxSignBusyStillCheckTime)):
                    # 清空标识队列，表示等下可以发送了。
                    self.s_SimulateUniqueArray = []
                    bCanExecSend = True
        return bCanExecSend, strRetTransUniqueSign

    # 获得下一个，针对目标服务端，可以发送的数据包
    # start by sk. 170128
    def Pop_GetNext_Client_SendablePacket(self, mangClientUnivealParam):
        strExecFromUser = mangClientUnivealParam.s_u_strMySelfIDName
        strExecDestUser = ''
        strExecContentBuff = ''
        iMaxSendPackSize = 50000  # 10k
        iExecSubCmd = 0

        # 以前平衡单元，尚有未发数据?
        strRetFromUser, strRetDestUser, iRetSubCmd, strRetContentBuff =\
            self.s_midBalanceInOutBuffMang.Retrive_Pop_Next_Balaned_SendAblePacket()
        if( not strRetContentBuff):
            # 首先直接检查服务端数据包有否需要直接发送的
            strCurBuff = self.s_toServerStoreUnit.Convert_Pop_Comb_SendPacketArray(iMaxSendPackSize)
            if ( strCurBuff != ''):
                strRetContentBuff = strCurBuff
                strRetDestUser = self.s_toServerStoreUnit.s_strDestUser
                iRetSubCmd = CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_DirectSrvExec
            else:
                strExecFromUser, strExecDestUser, iExecSubCmd, strExecContentBuff = self.__Exec_PopGetNextSendPacket_ExistClientContentOut( mangClientUnivealParam)
                # 将内容传入平衡管理
                if( strExecContentBuff):
                    self.s_midBalanceInOutBuffMang.Trans_OrigNeedSend_Data_Into_MidBalance_Buff(strExecFromUser,
                                                                strExecDestUser, iExecSubCmd, strExecContentBuff)
                    # 传入后，格式化后取出
                    strRetFromUser, strRetDestUser, iRetSubCmd, strRetContentBuff = self.s_midBalanceInOutBuffMang.Retrive_Pop_Next_Balaned_SendAblePacket()
                else:
                    strRetFromUser, strRetDestUser, iRetSubCmd, strRetContentBuff = '', '', 0, ''

        return strRetFromUser, strRetDestUser, iRetSubCmd, strRetContentBuff

    # 获得下一个，针对目标服务端，可以发送 － 存在的客户端单元的数据包内容
    # start by sk. 170204
    def __Exec_PopGetNextSendPacket_ExistClientContentOut(self, mangClientUnivealParam):
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        strMySelfName = mangClientUnivealParam.s_u_strMySelfIDName
        onLineClientMang = mangClientUnivealParam.s_u_OnLineClientUnitMang

        strRetFromUser, strRetDestUser = '', ''
        strRetContentBuff = ''
        iMaxSendPackSize = 100000  # 100k

        iCurContentLength = 0
        iRetSubCmd = CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_Db_Session_Trans

        for eachClientUnit in self.s_peerRemoteClientList.values():
            sendFreeSessionUnitArray = []

            # 查找到此客户端单元的需要重发的数据包。 查找到此客户端单元的内容数据包。
            # 查找我需要重新执行发送的数据包。 自身需要执行重新发送的命令 需要对方重新发送范围
            iNeedExecRecTypeArray = [CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut,
                                     CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeerReSend,
                                     CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedSelfExecReSend,
                                     CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeer_ReSend_Range,
                                     CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedSelfExec_ReSend_Range]
            iStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
            for iEachRecType in iNeedExecRecTypeArray:
                curFreeSessionUnitArray = CTYLBDB_tpd_send_recv_session.GetUsersStatus_Type_SessionUnit_Array(
                    dbExecConn, iEachRecType, strMySelfName, eachClientUnit.s_strClientName, iStatus)
                sendFreeSessionUnitArray.extend(curFreeSessionUnitArray)

            # 对每个数据包类型进行执行
            if (len(sendFreeSessionUnitArray) > 0):
                curSendStoreUnit = CTYLB_Trans_Exec_StoreUser_Unit( strMySelfName, eachClientUnit.s_strClientName)
                for eachSendSessionUnit in sendFreeSessionUnitArray:
                    iCurUnitLength = 0

                    iDestExecReadSessionRecID = 0
                    sessionRecIDFromParam = None
                    if (eachSendSessionUnit.iTaskType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_RePeerSendSessionData):
                        # 直接构建，请求对方重发的数据包命令
                        newBusisPackUnit = CTYLB_Busis_Packet(eachSendSessionUnit.iTaskType, eachSendSessionUnit.iSessionID, 0, 1)
                        iCurUnitLength = newBusisPackUnit.NearCalcTransLength()
                        curSendStoreUnit.AddPacket(newBusisPackUnit)
                        onLineClientMang.Update_SelfReSend_ReqNonExistSession_Time( eachSendSessionUnit.strDestName)

                    elif (eachSendSessionUnit.iTaskType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_SelfExecResendSessionData):
                        # 需要对方重新发送数据包
                        # 对于需要重新发送的session_value，读取，执行。如果本身自己都不存在，以空的忽略记录代替
                        iNeedRealSessionRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID(
                            dbExecConn, CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut, eachSendSessionUnit.strMyName,
                            eachSendSessionUnit.strDestName, eachSendSessionUnit.iSessionID )
                        if( eachClientUnit.IsSessionIDExist( eachSendSessionUnit.iSessionID)):
                            # 缓冲记录已经发送过，跳过
                            ustrSendMiscInfo = u'resend SessionID:%d  rec:%d, --- need skip' % (eachSendSessionUnit.iSessionID, iNeedRealSessionRecID)
                        else:
                            # 更新时间
                            CTYLBDB_tpd_send_recv_session.UpdateField_ActionTime(dbExecConn, eachSendSessionUnit.id, datetime.now())
                            if (iNeedRealSessionRecID > 0):
                                iDestExecReadSessionRecID = iNeedRealSessionRecID
                                sessionRecIDFromParam = 1
                            else:
                                # 记录由于特殊原因不存在，发送忽略包
                                newBusisPackUnit = CTYLB_Busis_Packet(
                                    CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue, eachSendSessionUnit.iSessionID, 0, 1)
                                iCurUnitLength = newBusisPackUnit.NearCalcTransLength()
                                curSendStoreUnit.AddPacket(newBusisPackUnit)
                    elif (eachSendSessionUnit.iTaskType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_RePeerSend_Range_SessionData):
                        # 请求对方重新发送数据包范围
                        newBusisPackUnit = CTYLB_Busis_Packet(eachSendSessionUnit.iTaskType, eachSendSessionUnit.iSessionID, eachSendSessionUnit.iTaskParam1, 1)
                        iCurUnitLength = newBusisPackUnit.NearCalcTransLength()
                        curSendStoreUnit.AddPacket(newBusisPackUnit)

                        onLineClientMang.Update_SelfReSend_ReqNonExistSession_Time( eachSendSessionUnit.strDestName)
                    elif (eachSendSessionUnit.iTaskType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_SelfExec_RePeerSend_Range_SessionData):
                        # 执行重发范围数据
                        iSendRecvType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut

                        # 根据发送接收类型，源用户名，目标用户名，会话ID范围，读取记录列表
                        for iExecSessionValue in range( eachSendSessionUnit.iSessionID, eachSendSessionUnit.iTaskParam1):
                            iSessionRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID(
                                dbExecConn, iSendRecvType, eachSendSessionUnit.strMyName, eachSendSessionUnit.strDestName, iExecSessionValue)
                            if( iSessionRecID > 0):
                                # 更新本记录的操作发送时间
                                CTYLBDB_tpd_send_recv_session.UpdateField_ActionTime(dbExecConn, iSessionRecID,
                                                                                     datetime.now())
                                iCurTotSessionPackLength = self.__Prompt_Exec_ReadDb_Session_To_SendStoreUnit(
                                    dbExecConn, iSessionRecID, curSendStoreUnit)
                                iCurUnitLength += iCurTotSessionPackLength
                            else:
                                # 记录由于特殊原因不存在，发送忽略包
                                newBusisPackUnit = CTYLB_Busis_Packet(
                                    CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue, eachSendSessionUnit.iSessionID, 0, 1)
                                iCurUnitLength += newBusisPackUnit.NearCalcTransLength()
                                curSendStoreUnit.AddPacket(newBusisPackUnit)
                        pass
                    else:
                        eachClientUnit.AddSendSessionIDCache( eachSendSessionUnit.iSessionID)
                        iDestExecReadSessionRecID = eachSendSessionUnit.id
                        sessionRecIDFromParam = 2

                    if (iDestExecReadSessionRecID > 0):
                        iCurTotSessionPackLength = self.__Prompt_Exec_ReadDb_Session_To_SendStoreUnit(
                            dbExecConn, iDestExecReadSessionRecID, curSendStoreUnit)
                        iCurUnitLength = iCurTotSessionPackLength

                    # CTYLB_Ct_ServerUnit.ShowLog(0, u'send packet id:%d type:%d TaskType:%d Len:%d SessID:%d [%s]' %
                    #                             (iEachRecID, iType, iTaskType, iCurUnitLength, iSessionIDValue, ustrSendMiscInfo))
                    # 更新记录状态
                    CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus(dbExecConn, eachSendSessionUnit.id, CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Handling)
                    iCurContentLength += iCurUnitLength
                    if (iCurContentLength >= iMaxSendPackSize):
                        break
                strRetContentBuff = curSendStoreUnit.Convert_Pop_Comb_SendPacketArray()
                strRetDestUser = eachClientUnit.s_strClientName

                # 如果当前用户ID有内容，处理完即退出本循环。如果没有数据内容，则继续处理下一个用户
                break
        return strRetFromUser, strRetDestUser, iRetSubCmd, strRetContentBuff

    # 提交，读取数据库的会话数据，到发送存储单元
    # start by sk. 170128
    def __Prompt_Exec_ReadDb_Session_To_SendStoreUnit(self, dbConn, iScheduSessionRecID, curSendStoreUnit):
        iRetTotSessionPackLength = 0

        # 首先直接检查服务端数据包有否需要直接发送的
        iType, iStatus, strMyName, strDestName, iTaskType, iSessionID, iSessionType, iRecParam, actionTime, lReservedSendParam =\
            CTYLBDB_tpd_send_recv_session.ReadByRecID(dbConn, iScheduSessionRecID)

        tpdSessionDataArray = CTYLBDB_tpd_session_data.GetBelongSessionID_SessionUnit_Array(dbConn, iScheduSessionRecID)
        iContentLen = 0
        for eachSessionData in tpdSessionDataArray:
            newBusisPackUnit = CTYLB_Busis_Packet(iTaskType, iSessionID, eachSessionData.iSeqIndex,
                                                  eachSessionData.iLastPacket, eachSessionData.strContent)
            iRetTotSessionPackLength += newBusisPackUnit.NearCalcTransLength()
            curSendStoreUnit.AddPacket(newBusisPackUnit)
            iContentLen += len(eachSessionData.strContent)
        return iRetTotSessionPackLength

    # 处理接收到的通信数据包中，服务端的命令
    # start by sk. 170128
    # modify by sk. 修改传入参数1为 管理资源参数数组 CTYLB_Global_UnivTrans_ParamBlock
    def HandleRecvCommuPacketSrvCmd(self, mangClientUnivealParam, strSelfName, strFromUser, strDestUser,
                                    iSubCmd, strPacketContent):
        strOrigPackContent = strPacketContent
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        if( iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans):
            self.s_midBalanceInOutBuffMang.Trans_OrigRecv_Data_Into_MidBalance_Buff( strFromUser, strDestUser,
                                                                                     iSubCmd, strPacketContent)
            iRetPeerClientStatus, strFromUser, strDestUser, iSubCmd, strPacketContent =\
                self.s_midBalanceInOutBuffMang.Retrive_Pop_Next_Balaned_RecvOrigPacket()

            # 对方重启了，或者初始化，系统方式通知
            if( (iRetPeerClientStatus == CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Restart) or
                    ( iRetPeerClientStatus == CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Restart)):
                self.__HandleSysNotifyPeerClientStatus( mangClientUnivealParam, strFromUser,
                                                        mangClientUnivealParam.s_u_strMySelfIDName, iRetPeerClientStatus)

        if( (iSubCmd == 0) and (not strPacketContent) ):
            pass
        elif( iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_Ct_Ct_ChatText):
            strMsg = 'recv Ct_Ct_ChatText len:%d' % (len(strPacketContent))
            CTYLB_Ct_ServerUnit.ShowLog( 0, strMsg)
            self.__Handle_NotifyUserArrive(strFromUser)
            pass
        elif( iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_Db_Session_Trans):
            self.__Handle_NotifyUserArrive(strFromUser)
            busisUnitArray = CTYLB_Comb_PackArray.ExactCombindData( strPacketContent)
            if( len(busisUnitArray) > 1):
                pass
            for eachBusisUnit in busisUnitArray:
                self.__Handle_Recv_BusisUnitPacket( mangClientUnivealParam, strSelfName, strFromUser,
                                                    strDestUser, iSubCmd, eachBusisUnit)
            pass
        elif( iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_BCast_OnLine):
            # 获得本单元下一个数据包，提请调度发送
            strMsg = 'recv, Commu [%s->%s] UserOnline' % (strFromUser, strDestUser)
            CTYLB_Ct_ServerUnit.ShowLog( 0, strMsg)
            self.__Handle_NotifyUserArrive(strFromUser)
        else:
            busisUnitArray = []
            if(strPacketContent and (strPacketContent != ' ')):
                busisUnitArray = CTYLB_Comb_PackArray.ExactCombindData( strPacketContent)
            if( len(busisUnitArray)>0):
                strMsg = 'recv, comb_pack len:%d unitCount:%d' % (len(strPacketContent), len(busisUnitArray))
                CTYLB_Ct_ServerUnit.ShowLog( 0, strMsg)
            for eachBusisUnit in busisUnitArray:
                if( eachBusisUnit.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_Ct_Ct_ChatText):
                    self.__Handle_NotifyUserArrive( strFromUser)
                    # add to db
                    pass
                elif(eachBusisUnit.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Sv_Ct_RequestRearchAbleClientList_Reply):
                    self.__HandleRecv_RearchAbleClientList( dbExecConn, eachBusisUnit.s_strContent)
                    pass
                elif (eachBusisUnit.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Sv_Ct_RequestNeedRearchClientList_Reply):
                    self.__HandleRecv_OnLineReachClientList(dbExecConn, eachBusisUnit.s_strContent)
                    pass
                else:
                    strMsg = 'client recv, unknown business [%s->%s] iSubCmd:%d cmd:%d' % (strFromUser, strDestUser,
                                                                                           iSubCmd, eachBusisUnit.s_iBusiCmdID)
                    CTYLB_Ct_ServerUnit.ShowLog(0, strMsg)
            pass

    # 处理服务器单元重启的命令
    def HandlePeerServerRestart(self, mangClientUnivealParam, strPeerServerName):
        dbExecConn = mangClientUnivealParam.s_u_DbConn

        strExJsonData = {'status':CTYLB_MidBalance_InOutBuffMang.s_g_iPeerServer_Restart, 'from':strPeerServerName}
        strContent = json.dumps(strExJsonData)

        nowTime = datetime.now()
        # 增加记录，实现系统通知。
        CTYLBDB_tpd_inout_text.AddNewdRec( dbExecConn, CTYLB_SvClt_Cmd_Base_bytes.s_g_iInOutType_SystemNotify,
                                           strContent, '', mangClientUnivealParam.s_u_strMySelfIDName,
                                           CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free,
                                           nowTime, nowTime)
        pass

    # 处理系统通知远端客户端的状态消息
    # update by sk. 180318
    def __HandleSysNotifyPeerClientStatus(self, mangClientUnivealParam, strFromUser, strMySelfName, iRetPeerClientStatus):
        dbExecConn = mangClientUnivealParam.s_u_DbConn

        if(iRetPeerClientStatus == CTYLB_MidBalance_InOutBuffMang.s_g_iPeerClient_Restart):
            # 客户端重启，清除数据
            self.__HandleClientRestart(mangClientUnivealParam, strFromUser)

            pass

        strExJsonData = {'status':iRetPeerClientStatus, 'from':strFromUser}
        strContent = json.dumps(strExJsonData)

        nowTime = datetime.now()
        # 增加记录，实现系统通知。
        CTYLBDB_tpd_inout_text.AddNewdRec( dbExecConn, CTYLB_SvClt_Cmd_Base_bytes.s_g_iInOutType_SystemNotify,
                                           strContent, strFromUser, strMySelfName,
                                           CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free,
                                           nowTime, nowTime)

    # 处理系统通知远端客户端的重启消息
    # update by sk. 180318
    def __HandleClientRestart(self, mangClientUnivealParam, strClientName):
        # 每个客户节点单元重新启动，所有会话重置，所有未发送，已发送的数据包清0，
        clientNameUnit = self.__GetCLientNameUnit(strClientName)
        clientNameUnit.Reset()

        # 该节点的会话HLSock关闭。

        # 该节点的状态数据清0

        # 该节点相关数据库记录删除，清0
        #    表tpd_inout_text中，如果我重启，删除全部数据。如果节点A重启，删除到节点A的数据记录
        #    表tpd_peer_ack中，如果我重启，删除全部数据。如果节点A重启，则删除到节点A的数据记录
        #    表tpd_send_recv_session亦如上处理
        #    表tpd_session_data亦如上处理
        dbExecConn = mangClientUnivealParam.s_u_DbConn

        CTYLBDB_tpd_peek_ack.DeleteRec_By_PeerName(dbExecConn, strClientName)
        CTYLBDB_tpd_session_data.DeleteRec_By_BelongSessionID_in_SendRecvSessionRec(dbExecConn, strClientName)  # 删除会话数据
        CTYLBDB_tpd_send_recv_session.DeleteRec_By_MyNameOrDestName(dbExecConn, strClientName)  # 删除发送接收会话数据
        # CTYLBDB_tpd_inout_text.EmptyTable( dbExecConn)  # 此表保留

        pass

    # 处理接收到的业务单元
    # start by sk. 170202
    # modify by sk. 修改参数1，为传入管理参数队列
    def __Handle_Recv_BusisUnitPacket(self, mangClientUnivealParam, strSelfName, strFromUser, strDestUser,
                                      iSubCmd, busisUnit):
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        iBusisPackType = busisUnit.s_iBusiCmdID
        if( iBusisPackType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_RePeerSendSessionData):
            # 重新读取该会话数据， execing，在数据库中，增加一个需要重新发送的记录
            # 把此记录写入 send_recv_session里面，send_recv_type=NeedReSendRequest
            # 此处首发和目标用户名，先自动进行倒转
            self.__Exec_Add_SelfExecReSend_SessionRec( dbExecConn, strSelfName, strFromUser, busisUnit.s_iSessionID)
            pass
        elif (iBusisPackType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_RePeerSend_Range_SessionData):
            # 重新读取该会话数据 范围
            # 此处首发和目标用户名，先自动进行倒转
            self.__Exec_Add_SelfExecReSend_Range_SessionRec(dbExecConn, strSelfName, strFromUser,
                                                            busisUnit.s_iSessionID, busisUnit.s_iSubIndex)
        else:
            self.Recv_Write_Content_To_Db_CheckContinue(mangClientUnivealParam, strSelfName, strFromUser,
                                                        strDestUser, iSubCmd, busisUnit.s_iBusiCmdID,
                                                        busisUnit.s_iSessionID, busisUnit.s_iSubIndex, busisUnit.s_iLastPacket,
                                                        busisUnit.s_strContent)
            pass

    # 把接收到的数据包，写入数据库
    # start by sk. 170128
    # modify by sk. 修改参数1，为传入管理参数队列
    def Recv_Write_Content_To_Db_CheckContinue(self, mangClientUnivealParam, strSelfName, strFromUser,
                                               strDestUser, iSubCmd, iPacketType, iRecvBusisPeerSessionID,
                                               iRecvBusisPeerSubIndex, iIsLastPacket, strContentBuff):
        dbExecConn = mangClientUnivealParam.s_u_DbConn

        iRecType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_Recv
        bRecDiscard = False  # 记录是否需要丢弃?

        if( iPacketType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue):
            # 在数据表中, 本id是最大的？并且不存在？
            iMaxSessionValue = CTYLBDB_tpd_send_recv_session.GetMax_FromToUser_SendRecvType_SessionID( dbExecConn, iRecType,
                                                                                strFromUser, strDestUser)
            if( iRecvBusisPeerSessionID > iMaxSessionValue):
                bRecDiscard = True

        if( not bRecDiscard):
            # 写入新的数据
            iTaskType = iPacketType
            iStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_RecvStatus_Recving if( iIsLastPacket == 0)\
                else CTYLB_SvClt_Cmd_Base_bytes.s_iSession_RecvStatus_Recv_Finish

            iSessionType = 0
            # 查找这个用户的会话ID是否已经存在
            iCurSessionRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID( dbExecConn, iRecType,
                                                                strFromUser, strDestUser, iRecvBusisPeerSessionID)
            if( iCurSessionRecID == 0):
                # 如果此记录为坏的。进行标记。
                if (iPacketType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue):
                    iWriteSessionType = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue
                else:
                    iWriteSessionType = 0
                iCurSessionRecID = CTYLBDB_tpd_send_recv_session.AddNewdRec( dbExecConn, iRecType, iStatus, strFromUser, strDestUser,
                                                                             iTaskType, iRecvBusisPeerSessionID, iWriteSessionType, 0)
            if( iCurSessionRecID > 0):
                # 如果此记录为坏的。进行标记。
                if (iPacketType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue):
                    strWriteContentBuff = ''
                else:
                    strWriteContentBuff = strContentBuff

                # 判断记录是否已经存在
                iSubIndexRecID = CTYLBDB_tpd_session_data.GetSubIndex_RecID( dbExecConn, iCurSessionRecID, iRecvBusisPeerSubIndex)
                if( iSubIndexRecID == 0):    # 不存在，增加
                    iSubIndexRecID = CTYLBDB_tpd_session_data.AddNewdRec( dbExecConn, iCurSessionRecID, iRecvBusisPeerSubIndex,
                                                                          iIsLastPacket, strWriteContentBuff)
                if( iIsLastPacket):
                    self.__Internal_Continue_Check_SessionExtend( mangClientUnivealParam, strSelfName, strFromUser,
                                                                  iRecvBusisPeerSessionID, iCurSessionRecID, iRecvBusisPeerSubIndex)
                    pass
        pass

    # 持续检测数据包的完整性
    # start by sk. 170217
    # modify by sk. 修改参数1，为传入管理参数队列
    def __Internal_Continue_Check_SessionExtend(self, mangClientUnivealParam, strSelfName, strFromUser,
                                                iExecBusiSessionID, iExecSessionRecID, iExecPeerSeqIndex):
        dbExecConn = mangClientUnivealParam.s_u_DbConn

        bCheckNext = True
        # 循环进行下一个记录的检查，直到末尾。
        iCheckNextRecvType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_Recv

        while (bCheckNext):
            bCheckNext = self.__Internal_Check_ContinuePacketMissing(mangClientUnivealParam, strSelfName, strFromUser,
                                                                     iExecBusiSessionID, iExecSessionRecID, iExecPeerSeqIndex)
            if (bCheckNext):
                iExecBusiSessionID += 1
                # 查找这个用户的会话ID是否已经存在
                iExecSessionRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID(
                    dbExecConn, iCheckNextRecvType, strFromUser, strSelfName, iExecBusiSessionID)
                if (iExecSessionRecID > 0):
                    # 下个记录ok，可以继续进行检查
                    iExecPeerSeqIndex = CTYLBDB_tpd_session_data.GetMaxSubIndex_By_SessionRecID(dbExecConn, iExecSessionRecID)
                else:
                    bCheckNext = False
            pass

    # 检查数据库有否缺少接收的数据
    # start by sk. 170202
    # 为了避免死循环，把本函数修改返回值。返回True，表示本记录ok，可以继续检查下一个记录。如果False，表示本记录是缺失的
    # modify by sk. 修改参数1，为传入管理参数队列
    def __Internal_Check_ContinuePacketMissing(self, mangClientUnivealParam, strSelfName, strPacketFromName, iRecvBusisSessionID,
                                               iSessionRecID, iLastSubIndex):
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        onLineClientUnitMang = mangClientUnivealParam.s_u_OnLineClientUnitMang

        bRetCurRecOKNeedCheckNext = False
        # 当前是否最后一个会话子次序的数据包？
        iResendSessionIDValue = 0

        iSubIndexRecID = CTYLBDB_tpd_session_data.GetSubIndex_RecID(dbExecConn, iSessionRecID, iLastSubIndex)
        if( iSubIndexRecID > 0):
            iDataSessionID, iDataSeqIndex, strDataContent, iDataLastPacket = CTYLBDB_tpd_session_data.ReadByRecID( dbExecConn, iSubIndexRecID)
            if( iDataLastPacket > 0): # 最后一个到达了，可以整个检查
                # 读取之前的，是否存在断档
                # update to 批量读取内容
                belongSessionUnitArray = CTYLBDB_tpd_session_data.GetBelongSessionID_SessionUnit_Array( dbExecConn, iSessionRecID)
                iLastSeqIndex = 0
                bBadPacket = False
                for eachBelongSessionUnit in belongSessionUnitArray:
                    if( (iLastSeqIndex == 0) and (eachBelongSessionUnit.iSeqIndex == 0) and (len(belongSessionUnitArray)==1) ):
                        pass
                    elif( iLastSeqIndex +1 == eachBelongSessionUnit.iSeqIndex):
                        iLastSeqIndex += 1
                    else:
                        bBadPacket = True
                        break
                if( bBadPacket ):
                    iResendSessionIDValue = iRecvBusisSessionID
                else:  # ok的数据包。
                    # 设置当前数据包完成状态
                    # 读取旧的状态。如果是已经被完成读取，那么，设置此处为忽略
                    iOldStatus = CTYLBDB_tpd_send_recv_session.ReadRec_Status( dbExecConn, iSessionRecID)
                    if( iOldStatus == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_RecvStatus_Recving):
                        CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus( dbExecConn, iSessionRecID,
                                                                CTYLB_SvClt_Cmd_Base_bytes.s_iSession_RecvStatus_Recv_Finish)

                # 如果是，是否上次的最后一个＋1？
                bLoopCheckNextPossibleExist = False
                if (iResendSessionIDValue == 0):
                    iLastMaxSessionID = CTYLBDB_tpd_peek_ack.GetMax_PeerName_SessionID(dbExecConn, strPacketFromName)
                    if( iLastMaxSessionID == 0):
                        # 记录不存在，增加新的记录
                        if( iRecvBusisSessionID == 1):
                            CTYLBDB_tpd_peek_ack.AddNewdRec( dbExecConn, strPacketFromName, 1)
                            bLoopCheckNextPossibleExist = True
                        else:
                            # 记录不存在，直接从1开始要求重发
                            iResendSessionIDValue = 1
                    else:
                        if (iLastMaxSessionID + 1 == iRecvBusisSessionID):
                            # 如果是，则更新最后的id
                            CTYLBDB_tpd_peek_ack.UpdatePeerName_LastValidSessionID( dbExecConn, strPacketFromName, iRecvBusisSessionID)
                            bLoopCheckNextPossibleExist = True
                        else:
                            # 存在断档，继续调度重发
                            iResendSessionIDValue = iLastMaxSessionID + 1
                pass
                if( bLoopCheckNextPossibleExist): # 更新了，再次检查下一个。
                    bRetCurRecOKNeedCheckNext = True
                    # 也更新接收最新有效会话的时间
                    onLineClientUnitMang.UpdatePeerClientRecvSeqAckSession(strPacketFromName)
                    pass
            else:
                # 不是最后一个数据包，忽略
                pass
        else:
            # 数据库不存在该记录，不处理。
            pass

        return bRetCurRecOKNeedCheckNext

    # 执行，查找末尾，增加需要重新发送的记录范围
    # start by sk. 170217
    # modify by sk. 修改参数1，为传入管理参数队列
    def Exec_Check_Request_ReSend_BetweenSessionStart(self, mangClientUnivealParam, strFromName, strToName, iNeedResend_StartSessionID_Value):
        dbExecConn = mangClientUnivealParam.s_u_DbConn

        # 搜索下一个，对方发给我的最大的记录值。
        # 查找下一个虽然断档但是已经接收到的记录
        iRecvSendType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_Recv
        iNextValidSessionID = CTYLBDB_tpd_send_recv_session.Search_NextExist_RecBy_SendRecvType_FromToUser_SessionID(
            dbExecConn, iRecvSendType, strToName, strFromName, iNeedResend_StartSessionID_Value)
        if( iNextValidSessionID == 0):
            # 如果只有一条记录需要读取，那么，调用申请读取一条记录函数
            self.Exec_Add_NeedReSend_Single_SessionRec( dbExecConn, strFromName, strToName, iNeedResend_StartSessionID_Value)
        else:
            # 最多一次发送100个数据包
            if( iNextValidSessionID > iNeedResend_StartSessionID_Value + self.s_g_iMaxReSendOneRecCount):
                iNextValidSessionID = iNeedResend_StartSessionID_Value + self.s_g_iMaxReSendOneRecCount

            iRecvSendType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeer_ReSend_Range
            iStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
            iSessionTaskType = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_RePeerSend_Range_SessionData
            iOrigRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID_Param(
                dbExecConn, iRecvSendType, strFromName, strToName, iNeedResend_StartSessionID_Value, iNextValidSessionID)
            if (iOrigRecID > 0):
                # 判断记录有否存在，如果已经存在，直接设置状态＝0
                CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus(dbExecConn, iOrigRecID, iStatus)
            else:
                CTYLBDB_tpd_send_recv_session.AddNewdRec(dbExecConn, iRecvSendType, iStatus, strFromName, strToName, iSessionTaskType,
                                                         iNeedResend_StartSessionID_Value, 0, iNextValidSessionID)
            pass
        pass

    # 执行，增加需要重新发送的记录
    # start by sk. 170202
    def Exec_Add_NeedReSend_Single_SessionRec(self, dbConn, strFromName, strToName, iDestSessionID):
        iRecvSendType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeerReSend
        iStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
        iSessionTaskType = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_RePeerSendSessionData
        iOrigRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID(
            dbConn, iRecvSendType, strFromName, strToName, iDestSessionID)
        if( iOrigRecID > 0):
            # 判断记录有否存在，如果已经存在，直接设置状态＝0
            CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus( dbConn, iOrigRecID, iStatus)
        else:
            CTYLBDB_tpd_send_recv_session.AddNewdRec(dbConn, iRecvSendType, iStatus, strFromName, strToName, iSessionTaskType,
                                                     iDestSessionID, 0, 0)

    # 执行，增加，进行重新发送的记录
    # start by sk. 170203
    def __Exec_Add_SelfExecReSend_SessionRec(self, dbConn, strSelfName, strOrigFromName, iDestSessionID):
        iRecvSendType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedSelfExecReSend
        iOutFreeStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
        iSessionTaskType = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_SelfExecResendSessionData


        lastSendOutActionTime = None  # 上次发送的时间初始化
        bCheckAddNewOrExecUpdate = True  # 增加新记录还是执行更新
        bExecReSend = False   # 执行重发的工作

        # 首先，找到，我发给伙伴节点的，session_id_value的记录。再找到该单元对应的tpd_session_data记录。再找到该单元的内容长度

        # 找直接发送过的记录。此记录是对方需要我们重新发送的原始记录。获得此记录的内容
        iSendOutType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut
        origSendOut_SendRecvSessionRecUnit = CTYLBDB_tpd_send_recv_session.ReadRecUnit_By_SendRecvType_FromToUser_SessionID(
            dbConn, iSendOutType, strSelfName, strOrigFromName, iDestSessionID)
        # 获得原始发送的时间
        if (origSendOut_SendRecvSessionRecUnit):
            lastSendOutActionTime = origSendOut_SendRecvSessionRecUnit.execAtionTime

        # 这里自动根据参数传入，将收发名字进行放置。
        origExecReSend_RecUnit = CTYLBDB_tpd_send_recv_session.ReadRecUnit_By_SendRecvType_FromToUser_SessionID(
            dbConn, iRecvSendType, strSelfName, strOrigFromName, iDestSessionID)
        if( origExecReSend_RecUnit):
            # 此处增加判断，是否以前提交过。如果内容长度太大，则需要调整。

            # 对此重发的时间内进行判断，如果此记录重发过，则时间更新
            if(origExecReSend_RecUnit.iStatus != iOutFreeStatus):
                lastSendOutActionTime = origExecReSend_RecUnit.execAtionTime

        iContentLength = CTYLBDB_tpd_session_data.GetContentLength_By_BelongSessionID(
            dbConn, origSendOut_SendRecvSessionRecUnit.id) if (origSendOut_SendRecvSessionRecUnit) else 0

        strSendParamMsg=""
        if(lastSendOutActionTime):
            # 获得会话ID的长度内容
            iDiffSecondTime = 1
            bSmallPacket=False
            if(iContentLength > 10000000):
                # 大于10M, 15分钟
                iDiffSecondTime = 900
            elif(iContentLength > 5000000):
                # 5M~10M, 10分钟
                iDiffSecondTime = 600
            elif (iContentLength > 1000000):
                # 1M~5M, 5分钟
                iDiffSecondTime = 300
            elif (iContentLength > 500000):
                # 500k~1M, 3分钟
                iDiffSecondTime = 180
            elif(iContentLength > 100000):
                # 100k~500k, 1分钟
                iDiffSecondTime = 60
            elif(iContentLength > 50000):
                # 50k~100k, 20秒
                iDiffSecondTime = 20
            elif(iContentLength > 10000):
                iDiffSecondTime = 5
            elif(iContentLength > 1000):
                iDiffSecondTime = 3
                bSmallPacket=True
            else:
                bSmallPacket=True

            fromTimeDiff = datetime.now() - lastSendOutActionTime

            if(origExecReSend_RecUnit):
                if(bSmallPacket):
                    iTotalDiffCount=iDiffSecondTime
                    strSendParamMsg += "small" % (origExecReSend_RecUnit.iReservedSendParam)
                else:
                    iTotalDiffCount=(origExecReSend_RecUnit.iReservedSendParam +1) * iDiffSecondTime
                    strSendParamMsg += "%d times" % (origExecReSend_RecUnit.iReservedSendParam)
            else:
                strSendParamMsg += "first"
                iTotalDiffCount=iDiffSecondTime

            if(fromTimeDiff.total_seconds() > iTotalDiffCount):
                bExecReSend = True
        else:
            # 实质内容记录不存在，重发记录不存在，则不需要重发
            bExecReSend = False

        if( bExecReSend):
            if(iContentLength>10000):
                self.ShowLog(0, 'need %s resend %s->%s SessionID:%d, length:%d' % (strSendParamMsg, strSelfName,
                                                                                   strOrigFromName, iDestSessionID, iContentLength))
            if( origExecReSend_RecUnit):
                # 判断记录有否存在，如果已经存在，直接设置状态＝0，并且更新发送参数次数
                CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus( dbConn, origExecReSend_RecUnit.id, iOutFreeStatus)
                CTYLBDB_tpd_send_recv_session.UpdateField_ReservedSendParam( dbConn, origExecReSend_RecUnit.id,
                                                                             origExecReSend_RecUnit.iReservedSendParam+1)
            else:
                CTYLBDB_tpd_send_recv_session.AddNewdRec(dbConn, iRecvSendType, iOutFreeStatus, strSelfName, strOrigFromName,
                                                         iSessionTaskType, iDestSessionID, 0, 0)

    # 执行，增加，进行重新发送的记录 范围
    # start by sk. 170217
    def __Exec_Add_SelfExecReSend_Range_SessionRec(self, dbConn, strSelfName, strOrigFromName, iDestSessionID, iDestSessionEndID):
        iRecvSendType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedSelfExec_ReSend_Range
        iStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
        iSessionTaskType = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_SelfExec_RePeerSend_Range_SessionData
        # 这里自动根据参数传入，将收发名字进行放置。
        iOrigRecID = CTYLBDB_tpd_send_recv_session.SearchRecBy_SendRecvType_FromToUser_SessionID_Param(
            dbConn, iRecvSendType,strSelfName, strOrigFromName, iDestSessionID, iDestSessionEndID)
        if( iOrigRecID > 0):
            # 判断记录有否存在，如果已经存在，直接设置状态＝0
            CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus( dbConn, iOrigRecID, iStatus)
        else:
            CTYLBDB_tpd_send_recv_session.AddNewdRec(dbConn, iRecvSendType, iStatus, strSelfName, strOrigFromName, iSessionTaskType,
                                                     iDestSessionID, 0, iDestSessionEndID)

    @staticmethod
    def ShowLog( iWarnLevel, ustrMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'SrvUnit', ustrMsg)

# 管理服务端单元队列
# start by sk. 170124
class CTYLB_Ct_Mang_Server(CTYLB_Mang_BusisUnit_Base_bytes):
    def __init__(self, strSelfClientName):
        CTYLB_Mang_BusisUnit_Base_bytes.__init__(self, strSelfClientName)
        pass

    def __del__(self):
        pass

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        newServerUnit = CTYLB_Ct_ServerUnit( socketValue, iSockType, peerAddress)
        return newServerUnit

    # 获得某个目标用户名，可以通过服务端对象发送的列表
    # start by sk. 170128
    def Get_ReachSendList_SrvUnit_By_RemotePeerName(self, strRemoteClientName):
        retSrvUnitArray = []
        for eachSrvUnit in self.s_mangUnitArray:
            if( eachSrvUnit.IsClientInMyArray( strRemoteClientName)):
                retSrvUnitArray.append( eachSrvUnit)
        return retSrvUnitArray

    # 管套接收数据调度
    # modify by sk. 第一个参数为 管理参数队列
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, bstrRecvData_bytes):
        CTYLB_Mang_BusisUnit_Base_bytes._Viul_HandleSockRecvPacket( self, mangClientUnivealParam, socketValue, bstrRecvData_bytes)
        dbExecConn = mangClientUnivealParam.s_u_DbConn
        connSockThreadMang = mangClientUnivealParam.s_u_connSockThread

        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol

        serverClientUnit = self.SearchUnitBySockValue(socketValue)
        if( not serverClientUnit):
            iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock
        else:
            bAtLeastOneSucc = False    # 至少一个成功

            bstrNotHandleBuff_bytes = bstrRecvData_bytes
            while( len(bstrNotHandleBuff_bytes) > 0):
                bstrCurValidRecvData = bstrNotHandleBuff_bytes
                bstrNotHandleBuff_bytes = b''
                # 是accept对象
                if (serverClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                    # 解包对方发送的post内容，如果正确，我回应 http结果
                    bExactResult, strFromUniqueSign, tyCmdUnit, strFromUser, strDestUser, buildTime, bstrNotHandleBuff_bytes =\
                        CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket( bstrCurValidRecvData, True)
                    if (bExactResult and tyCmdUnit):
                        bAtLeastOneSucc = True

                        bHaveContent = False if(tyCmdUnit.IsCmdUnitEmpty()) else True
                        serverClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty( False, bHaveContent)

                        # 我是accept，对方主动连接，对方是服务端，我是client，如果有需要。发送请求。对方会下一个动作进行回应
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_7_Connect_SendCheck):
                            serverClientUnit.HandleRecvCommuPacketSrvCmd( mangClientUnivealParam, self.s_strMySelfName,
                                                                          strFromUser, strDestUser,
                                                                          tyCmdUnit.s_iSubCmd, tyCmdUnit.s_strContent)
                            # 如果我有数据需要发送，那么，这里调度出去，进行发送。
                            strFromUser, strDestUser, iSubCmd, strSendContent = serverClientUnit.Pop_GetNext_Client_SendablePacket(
                                mangClientUnivealParam)
                            # 有内容进行发送。
                            bHaveContent = True if (len(strSendContent) > 0) else False
                            serverClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(True, bHaveContent)

                            # 我构建汇报包进行发送
                            bstrReplyContent = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                                strFromUniqueSign, CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_12_Reply_SendCheck, iSubCmd,
                                strFromUser, strDestUser, strSendContent, False)
                            serverClientUnit.Set_ExecSendAction_Flag( )
                            connSockThreadMang.SafePromptDataToSend( socketValue, bstrReplyContent)
                # 是connect对象
                elif (serverClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                    # 我已经发送了post内容，对方回应 http结果，此处进行分析解包
                    bExactResult, strPeerUniqueSign, tyCmdUnit, strFromUser, strDestUser, buildTime, bstrNotHandleBuff_bytes =\
                        CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket( bstrCurValidRecvData, False)
                    if (bExactResult and tyCmdUnit):
                        serverClientUnit.GiveBack_SessionUniqueSign( strPeerUniqueSign)  # 归还会话占用符
                        bAtLeastOneSucc = True
                        bHaveContent = False if( tyCmdUnit.IsCmdUnitEmpty()) else True
                        serverClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty( False, bHaveContent)

                        # 服务端向我发的 回应包
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_6_Reply_SendCheck):
                            serverClientUnit.HandleRecvCommuPacketSrvCmd(
                                mangClientUnivealParam, self.s_strMySelfName, strFromUser, strDestUser,
                                tyCmdUnit.s_iSubCmd, tyCmdUnit.s_strContent)
                        else:
                            strMsg = 'ct_mang_srv._Viul_HandleSockRecvPacket recv cmd:[%s->%s] cmd:%d:%d contentlen:%d' % (
                                strFromUser, strDestUser, tyCmdUnit.s_iMainCmd, tyCmdUnit.s_iSubCmd, len(tyCmdUnit.s_strContent))
                            CTYLB_Ct_Mang_Server.ShowLog( 0, strMsg)
                    else:
                        if( len(bstrCurValidRecvData) > 0):
                            CTYLB_Ct_Mang_Server.ShowLog(1, 'Sock_Recv_Data Error. data-len: %d' % (len(bstrCurValidRecvData)))
                    pass
            if( bAtLeastOneSucc):
                if (serverClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                    iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData
                elif (serverClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                    iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply
            else:
                serverClientUnit.SetDataFormatBadClose()
        return iReplyCode

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False
        connSockThreadMang = mangClientUnivealParam.s_u_connSockThread

        for eachUnit in self.s_mangUnitArray:
            eachUnit.ExecTimerCheck( mangClientUnivealParam)
            # 是否主动连接？
            if (eachUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                bCanExecSend, strTransUniqueSign = eachUnit.Viul_GetNextSendResource(
                    CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxSvCtCheckSecond, CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxBusyStillCheckTick)
                # 若无数据内容提交，主动发送握手包。可能服务端会有数据回应
                if (bCanExecSend):
                    strFromUser, strDestUser, iSubCmd, strSendContent = '', '', 0, ''
                    if( strTransUniqueSign):
                        # 如果我有数据需要发送，那么，这里调度出去，进行发送。
                        strFromUser, strDestUser, iSubCmd, strSendContent = eachUnit.Pop_GetNext_Client_SendablePacket(
                            mangClientUnivealParam)
                        # 如果没有标识，那么，设置空闲。

                    # 有内容，或者时间到了，需要发送，就进行调度发送
                    bHaveContent = True if( len(strSendContent) > 0) else False

                    eachUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(True, bHaveContent)  # 设置最后发送时间
                    # 构建握手包，进行发送
                    bstrSendPacket = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                        strTransUniqueSign, CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_5_Connect_SendCheck, iSubCmd,
                        strFromUser, strDestUser, strSendContent, True)
                    eachUnit.Set_ExecSendAction_Flag()
                    connSockThreadMang.SafePromptDataToSend(eachUnit.s_destSockValue, bstrSendPacket)
                    bRetValue = True
                else:
                    # 如果长时间没有数据包传输，发送心跳包，确认网络还通畅。
                    pass

            # 如果是被动连接，是否长时间无内容接收，如果是，则关闭
            elif( eachUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                if (eachUnit.Is_LastSend_IdleTime_LargeThan(CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxWaitComuInvalidIdleSecond)):
                    eachUnit.SetShakeHandResult(False)
                pass

        return bRetValue

    @staticmethod
    def ShowLog( iWarnLevel, strMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'MangSrv', strMsg)

# 主执行运行类
# start by sk. 170123
class CTYLB_Base_Client:
    s_checkRecvToInOutDiffSecond = 0.1
    s_g_iWhileLoopMaxStepCount = 1000  # 每次循环最大的次数是1000
    s_g_iExecCleanTimeDiff = 120  # 每2分钟清除一次垃圾数据

    def __init__(self, strConfigFile, strDbFile):
        self.s_globalTaskQueue = queue.Queue()
        self.s_acceptConnectSockThread = None
        self.s_initiactiveConnectSockThread= None

        self.s_clientConfig = CTYLB_Client_Config()
        self.s_clientConfig.ReadFromConfigFile( strConfigFile)
        self.s_MyGlobalQueue = queue.Queue()

        self.s_acceptConnectSockMang = CTCPAcceptConnectMangClient_bytes( self.s_globalTaskQueue)
        self.s_execConnectSrvSockMang = CExecConnectSockMang_bytes( self.s_clientConfig.s_strSrvAddrArray)

        self.s_execListenSockMang = None

        self.s_lastSendTime = datetime.now()
        self.s_sendWaitDiffSecond = 10

        self.s_lastCheckRecvToInOutTime = datetime.now()
        self.s_lastCleanUnusedDataTime = datetime.now()
        self.s_lastRequestHaveContentOffLineUserTime = datetime.now()  # 上次请求，有内容，又下线了的时间
        self.s_needIdentifyUnitMang = CTYLB_Ct_Mang_NeedIdentify( self.s_clientConfig.s_strMyID)
        self.s_serverUnitMang = CTYLB_Ct_Mang_Server(self.s_clientConfig.s_strMyID)

        self.s_needCloseSockValueArray = []
        self.s_sqlLiteExecDB = CTYLB_SQLite_DB_Conn( strDbFile)
        self.s_strSqlLiteBackupDBFileName = strDbFile + u'.bak'
        self.s_onlineClientMang = CTYLB_OnLineClient_Mang()  # 在线客户端单元管理 CTYLB_OnLineClient_Mang

        # 创建，初始化4个表
        CTYLBDB_tpd_peek_ack.CreateNewTable(self.s_sqlLiteExecDB.s_dbConn)
        CTYLBDB_tpd_send_recv_session.CreateNewTable(self.s_sqlLiteExecDB.s_dbConn)
        CTYLBDB_tpd_session_data.CreateNewTable(self.s_sqlLiteExecDB.s_dbConn)
        CTYLBDB_tpd_inout_text.CreateNewTable( self.s_sqlLiteExecDB.s_dbConn)

        # 清除之前的垃圾记录
        CTYLBDB_tpd_peek_ack.EmptyTable(self.s_sqlLiteExecDB.s_dbConn)
        CTYLBDB_tpd_send_recv_session.EmptyTable(self.s_sqlLiteExecDB.s_dbConn)
        CTYLBDB_tpd_session_data.EmptyTable(self.s_sqlLiteExecDB.s_dbConn)
        CTYLBDB_tpd_inout_text.EmptyTable( self.s_sqlLiteExecDB.s_dbConn)

        pass

    # prepare to run
    # start by sk. 170212
    def PrePare_Run(self):
        CTYLB_Base_Client.ShowLog(0, "[tylb_p2p client] Starting...")

        # start listen port
        if( self.s_clientConfig.s_iClientListenPort > 0):
            self.s_execListenSockMang = CTCPListenSock( self.s_clientConfig.s_iClientListenPort, self.s_globalTaskQueue)
            self.s_execListenSockMang.Start()

        self.s_acceptConnectSockMang.Start()
        pass

    # Service run main.
    # start by sk. 170116
    def Run_TimerCheck(self):
        bTaskBusy = False
        mangClientUnivealParam = CTYLB_Global_UnivTrans_Param( self.s_sqlLiteExecDB.s_dbConn, self.s_onlineClientMang,
                                                               self.s_serverUnitMang, self.s_clientConfig.s_strMyID,
                                                               self.s_acceptConnectSockMang.s_myExecConnectSocketThread)

        # 对网络功能，进行维护调用
        if( self.__Maintance_Exec_NetworkSocket()):
            bTaskBusy = True

        # 对辨别客户端的网络单元，进行维护检查
        if( self.s_needIdentifyUnitMang._Viul_TimerCheckSockSendPacket( mangClientUnivealParam)):
            bTaskBusy = True

        # 有出错被主动关闭的客户端？
        beenPeerClosedUnit = self.s_needIdentifyUnitMang.Pop_ClosedByPeer_Unit()
        if( beenPeerClosedUnit):
            self.s_needCloseSockValueArray.append( beenPeerClosedUnit.s_destSockValue)

        # 对服务端的单元，进行维护检查
        if( self.s_serverUnitMang._Viul_TimerCheckSockSendPacket(mangClientUnivealParam)):
            bTaskBusy = True

        # 对于出错关闭的管套，从各个队列中移除
        for eachSockValue in self.s_needCloseSockValueArray:
            # 在执行连接的服务器中处理
            self.s_execConnectSrvSockMang.DestSockClosed(eachSockValue)
            # 在应用辨别单元队列中检查
            self.s_needIdentifyUnitMang.ExecHandleSockClose(eachSockValue)
            # 在服务器管理队列中检查
            self.s_serverUnitMang.ExecHandleSockClose(eachSockValue)
            # 在接收的监听连接队列中检查
            if( self.s_acceptConnectSockMang.s_myExecConnectSocketThread):
                self.s_acceptConnectSockMang.s_myExecConnectSocketThread.CloseExecSocket( eachSockValue)
        self.s_needCloseSockValueArray = []

        # 广播消息，客户端需要发送请求数据包
        self.__CheckAllClientNeedExecSendSeqReqPacket()
        # 检查有否需要发送的消息
        if( self.__Check_DB_Read_NeedSendDestMsg()):
            bTaskBusy = True
        if( self.__Check_DB_Write_SuccRecvNewMsg()):
            bTaskBusy = True
        if( self.__Check_Schedule_OffLine_User_ActiveRequest()):
            bTaskBusy = True
        # 在线客户端进行检查
        if( self.s_onlineClientMang.TimerCheck( mangClientUnivealParam)):
            bTaskBusy = True

        return bTaskBusy

    # stop to run,quit.
    # start by sk. 170212
    def StopRun(self):
        # 停止监听，退出线程
        if( self.s_execListenSockMang):
            self.s_execListenSockMang.Stop()
            self.s_execListenSockMang = None
        if( self.s_acceptConnectSockMang.s_myExecConnectSocketThread):
            self.s_acceptConnectSockMang.s_myExecConnectSocketThread.SafeStop()
        # wait all queue task exit.
        self.s_globalTaskQueue.join()
        pass

    # Maintance exec network-socket function
    # start by sk. 170124
    def __Maintance_Exec_NetworkSocket(self):
        bRetValue = False

        # 检查监听管套，新接收的管套
        if (self.s_execListenSockMang):
            newClientSock, newClientAddr = self.s_execListenSockMang.s_myListenThread.SafeGetNewClientConnec()
            if (newClientSock):
                # 加入到连接管理队列
                if( self.s_acceptConnectSockMang.s_myExecConnectSocketThread):
                    self.s_acceptConnectSockMang.s_myExecConnectSocketThread.AddClientSocket(newClientSock, None)
                CTYLB_Base_Client.ShowLog( 0, 'New Connect Accept, From:%s' % (str(newClientAddr)))
                bRetValue = True
                # 加入到应用辨别单元队列
                self.s_needIdentifyUnitMang.NewSockUnitArrive( newClientSock, True)

        # 对连接管理的管套，进行数据检查
        iCurLoopIndex = 0
        while( iCurLoopIndex < CTYLB_Base_Client.s_g_iWhileLoopMaxStepCount):
            iCurLoopIndex += 1
            if( self.s_acceptConnectSockMang.s_myExecConnectSocketThread):
                bstrRecvData, curExecSockUnit = self.s_acceptConnectSockMang.s_myExecConnectSocketThread.SafePopRecvPacketUnit()
            else:
                bstrRecvData, curExecSockUnit = b'', None
            if (bstrRecvData):
                mangClientUnivealParam = CTYLB_Global_UnivTrans_Param(self.s_sqlLiteExecDB.s_dbConn,
                                                                      self.s_onlineClientMang,
                                                                      self.s_serverUnitMang, self.s_clientConfig.s_strMyID,
                                                                      self.s_acceptConnectSockMang.s_myExecConnectSocketThread)
                # 把数据给辨别单元管理，进行处理
                iReplyCode = self.s_needIdentifyUnitMang._Viul_HandleSockRecvPacket(
                    mangClientUnivealParam, curExecSockUnit.s_mySocket,  bstrRecvData)
                if( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply):
                    pass
                elif( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol):
                    self.s_needCloseSockValueArray.append(curExecSockUnit.s_mySocket)
                elif( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData):
                    pass
                elif( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock):
                    # 把数据交给服务器管理，进行处理
                    iReplyCode = self.s_serverUnitMang._Viul_HandleSockRecvPacket(
                        mangClientUnivealParam, curExecSockUnit.s_mySocket, bstrRecvData)
                    if( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply):
                        pass
                    elif( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol):
                        self.s_needCloseSockValueArray.append( curExecSockUnit.s_mySocket)
                    elif( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData):
                        pass
                    elif( iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock):
                        pass

                bRetValue = True

                # 有成功完成辨别的客户端？
                finishIdentifyUnit = self.s_needIdentifyUnitMang.Pop_Finish_Identify_Server()
                if (finishIdentifyUnit):
                    if (finishIdentifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_OK):
                        bIsAccept = True if (
                        finishIdentifyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept) else False
                        newServerUnit = self.s_serverUnitMang.NewSockUnitArrive(finishIdentifyUnit.s_destSockValue, bIsAccept)
                        strMsg = 'Server [%s] ShakeHand Success: %s' % (newServerUnit.s_strUnitName, str(finishIdentifyUnit.s_peerAddress))
                        CTYLB_Base_Client.ShowLog(0, strMsg)

                        # 此处应该对其他节点发送一个通知，服务器重启，上层可以重启数据包的提交发送
                        newServerUnit.HandlePeerServerRestart(mangClientUnivealParam, newServerUnit.s_strUnitName)

                    elif (finishIdentifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_Fail):
                        # 关闭管套
                        self.s_needCloseSockValueArray.append(finishIdentifyUnit.s_destSockValue)
                    break
            else:
                # 直到处理完全部数据，没有数据可读取
                break

        # 检查是否有连接了的管套被关闭了。
        disconnectSocket = self.s_acceptConnectSockMang.s_myExecConnectSocketThread.SafePopDisconnectClosedSocket()
        if (disconnectSocket):
            self.s_needCloseSockValueArray.append( disconnectSocket)

        # 对连接服务器端进行调度自动连接
        if (self.s_execConnectSrvSockMang.TimerCheck_Auto_Connect()):
            bRetValue = True

        # 对连接成功的管套进行处理
        newConnectSockUnit = self.s_execConnectSrvSockMang.GetLastSuccConnectSock()
        if (newConnectSockUnit):
            # 成功连接后，把单元加入到连接管套队列，进行管理
            if( self.s_acceptConnectSockMang.s_myExecConnectSocketThread):
                self.s_acceptConnectSockMang.s_myExecConnectSocketThread.AddClientSocket(newConnectSockUnit.s_execSocket,
                                                                                     newConnectSockUnit.s_tmpSaveRecvBuffArray)
            newConnectSockUnit.SetSockMonitorByOtherThread()
            # 也把该管套，加入到应用辨别队列
            self.s_needIdentifyUnitMang.NewSockUnitArrive( newConnectSockUnit.s_execSocket, False)
            bRetValue = True

        return bRetValue

    # 广播检查消息给各个客户端
    # start by sk. 170124
    def __CheckAllClientNeedExecSendSeqReqPacket(self):
        bRetValue = False

        curTime = datetime.now()
        timeDiff = curTime - self.s_lastSendTime
        if( timeDiff.seconds > self.s_sendWaitDiffSecond):
            self.s_lastSendTime = curTime
            # 给每个客户端单元，提交进行发送
            for eachClientSrvUnit in self.s_serverUnitMang.s_mangUnitArray:
                eachClientSrvUnit.DirectPromptCmdSendToSrv(CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_BCast_OnLine)
            pass

        return bRetValue

    # 检查，读取需要发送的消息
    # start by sk. 170128
    def __Check_DB_Read_NeedSendDestMsg(self):
        bRetValue = False
        dbExecConn = self.s_sqlLiteExecDB.s_dbConn
        # 读取数据库回复的记录
        iFreeInOutRecID = CTYLBDB_tpd_inout_text.GetNextRec_By_FromName_Status(dbExecConn, self.s_clientConfig.s_strMyID, 0)
        if (iFreeInOutRecID > 0):
            bRetValue = True
            iInputReplyType, strContent, strFromName, strDestName, iPeerStatus, createTime, replyTime = \
                CTYLBDB_tpd_inout_text.ReadByRecID(dbExecConn, iFreeInOutRecID)
            CTYLBDB_tpd_inout_text.UpdateField_PeerStatus( dbExecConn, iFreeInOutRecID, 2)
            CTYLBDB_tpd_inout_text.UpdateField_ReplyTime(dbExecConn, iFreeInOutRecID, datetime.now())

            # 转换到 tpd_send_recv_session 表中
            # 获得最后的session-id.
            iSendRecvType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut
            iLastSessionID = CTYLBDB_tpd_send_recv_session.GetMax_FromToUser_SendRecvType_SessionID(dbExecConn,
                                                                    iSendRecvType, strFromName, strDestName)
            iLastSessionID += 1

            iRecStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
            iTaskType = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_ChatText
            iNewSessionRecID = CTYLBDB_tpd_send_recv_session.AddNewdRec( dbExecConn, iSendRecvType,
                                                                         iRecStatus, strFromName, strDestName, iTaskType,
                                                                         iLastSessionID, 0, 0)
            if( iNewSessionRecID > 0):
                iSequIndex = 0
                iIsLastPacket = 1
                iNewSessionContentRecID = CTYLBDB_tpd_session_data.AddNewdRec( dbExecConn, iNewSessionRecID,
                                                                               iSequIndex, iIsLastPacket, strContent)
                # 删除旧的inout text 记录，只在send_recv中保存
                # CTYLBDB_tpd_inout_text.DeleteRec( dbExecConn, iFreeInOutRecID)
            pass
        return bRetValue

    # 检查，读取到达的消息
    # start by sk. 170202
    def __Check_DB_Write_SuccRecvNewMsg(self):
        bRetValue = False

        nowTime = datetime.now()
        if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_lastCheckRecvToInOutTime, self.s_checkRecvToInOutDiffSecond)):
            destDbConn = self.s_sqlLiteExecDB.s_dbConn
            strSelfMyName = self.s_clientConfig.s_strMyID
            strDestNameArray = CTYLBDB_tpd_peek_ack.Get_PeerName_Array(destDbConn)

            for strEachDestName in strDestNameArray:
                iMaxLastValidSessionID = CTYLBDB_tpd_peek_ack.GetMax_PeerName_SessionID( destDbConn, strEachDestName)

                # 这个id，和send_recv_session表中的id相比，空闲，未读的进行读取
                recvSessionUnitArray = CTYLBDB_tpd_send_recv_session.Get_MyDestName_Status_RangeValueSession_DataUnitArray(
                    destDbConn, CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_Recv, strEachDestName, strSelfMyName,
                    CTYLB_SvClt_Cmd_Base_bytes.s_iSession_RecvStatus_Recv_Finish, iMaxLastValidSessionID)

                for eachSessionUnit in recvSessionUnitArray:
                    bRetValue = True
                    # 判断记录是否有效。如果无效，那么，忽略
                    #iType, iStatus, ustrMyName, ustrDestName, iTaskType, iSessionID, iSessionType, iRecParam = \
                    #    CTYLBDB_tpd_send_recv_session.ReadByRecID( destDbConn, eachSessionUnit.id)
                    if( eachSessionUnit.iSessionType == CTYLB_SvClt_Cmd_Base_bytes.s_iSession_TaskType_BadSessionIDValue):
                        pass
                    else:
                        sessionDataUnitArray = CTYLBDB_tpd_session_data.GetBelongSessionID_SessionUnit_Array(destDbConn, eachSessionUnit.id)
                        for eachSessionData in sessionDataUnitArray:
                            #iBelongSessionID, iSeqIndex, ustrContent, iIsLastPacket = CTYLBDB_tpd_session_data.ReadByRecID(
                            #    destDbConn, iEachSessionDataRecID)
                            CTYLBDB_tpd_inout_text.AddNewdRec( destDbConn, 1, eachSessionData.strContent, strEachDestName, strSelfMyName,
                                                               0, nowTime, nowTime)

                    CTYLBDB_tpd_send_recv_session.UpdateField_RecStatus(
                        destDbConn, eachSessionUnit.id, CTYLB_SvClt_Cmd_Base_bytes.s_iSession_RecvStatus_Recv_Finish_Readed)

            if(not bRetValue):  # 如果没有内容，设置等待时间。
                self.s_lastCheckRecvToInOutTime = nowTime

                if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_lastCleanUnusedDataTime, self.s_g_iExecCleanTimeDiff)):
                    self.s_lastCleanUnusedDataTime = nowTime
                    self.__db_ExecCleanUnUsedRec()

        return bRetValue

    # 获得下一个，针对目标服务端，可以发送 － 调度未上线客户端请求
    # start by sk. 170204
    def __Check_Schedule_OffLine_User_ActiveRequest(self):
        bRetValue = False

        # 查找未发送的数据包中，未上线的客户端名字列表
        timeDiff = datetime.now() - self.s_lastRequestHaveContentOffLineUserTime
        if( timeDiff.seconds >= CTYLB_Ct_ServerUnit.s_g_iRequestOffLineUserTimeCheck):
            dbConn = self.s_sqlLiteExecDB.s_dbConn
            self.s_lastRequestHaveContentOffLineUserTime = datetime.now()

            # 找具有未发送数据的客户端列表
            iSendRecvType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut
            iRecStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Free
            iFreeSessionRecID = CTYLBDB_tpd_send_recv_session.GetUsersStatus_Type_FromUser_RecID_Array(
                dbConn, iSendRecvType, self.s_clientConfig.s_strMyID, iRecStatus)
            strToUserNameArray = []
            for iEachID in iFreeSessionRecID:
                strDestName = CTYLBDB_tpd_send_recv_session.ReadByRecID_DestName( dbConn, iEachID)
                if( strDestName not in strToUserNameArray):
                    strToUserNameArray.append( strDestName)
                pass
            # 客户端名字是否已经存在？
            strOffLineUserNameArray = []
            for strEachToUser in strToUserNameArray:
                # 这个客户端可到达？
                srvList = self.s_serverUnitMang.Get_ReachSendList_SrvUnit_By_RemotePeerName(strEachToUser)
                if( len(srvList) == 0):
                    if(strEachToUser and (strEachToUser not in strOffLineUserNameArray)):
                        strOffLineUserNameArray.append( strEachToUser)

            # 封装数据包，给每个服务端提交发送
            if( len(strOffLineUserNameArray) > 0):
                strNeedOnLineSendPack = CTYLB_SvClt_Cmd_Base_bytes.Comb_MultiClientNameList_Packet( strOffLineUserNameArray)
                for eachSrvUnit in self.s_serverUnitMang.s_mangUnitArray:
                    eachSrvUnit.DirectPromptCmdSendToSrv( CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Sv_RequestNeedRearchClientList,
                                                          strNeedOnLineSendPack)
            bRetValue = True
        return bRetValue

    # 数据库，清除未用的记录
    # start by sk. 170204
    def __db_ExecCleanUnUsedRec( self):
        # 1. 对 peer_ack 之前的记录进行删除
        dbConn = self.s_sqlLiteExecDB.s_dbConn
        strPeerNameArray = CTYLBDB_tpd_peek_ack.Get_PeerName_Array( dbConn)
        for strEachName in strPeerNameArray:
            iLastMaxSessionID = CTYLBDB_tpd_peek_ack.GetMax_PeerName_SessionID(dbConn, strEachName)
            # 把之前记录 send_recv_session 和 session_data的记录删除
            iSendRecvType = CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_Recv
            iRecStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Finish

            if( iLastMaxSessionID > 5):
                iLastMaxSessionID -= 5
                recvSessionRecIDArray = CTYLBDB_tpd_send_recv_session.Get_MyDestName_Status_RangeValueSession_RecIDArray(
                    dbConn, iSendRecvType, strEachName, self.s_clientConfig.s_strMyID, iRecStatus, iLastMaxSessionID)
                for iEachSessionRecID in recvSessionRecIDArray:
                    iSessionDataRecIDArray = CTYLBDB_tpd_session_data.GetBelongSessionID_RecID_Array(dbConn, iEachSessionRecID)
                    for iEachSessionDataRecID in iSessionDataRecIDArray:
                        # 删除 会话数据
                        CTYLBDB_tpd_session_data.DeleteRec( dbConn, iEachSessionDataRecID)
                    # 删除会话记录
                    CTYLBDB_tpd_send_recv_session.DeleteRec( dbConn, iEachSessionRecID)
                    pass

        # 2. 对 in_out 请求发送,已经转入 session 的记录进行删除
        # 对已经读取了的inout记录，进行写入备份数据库。
        # 对备份数据库进行初始化
        bakDbExec = CTYLB_SQLite_DB_Conn( self.s_strSqlLiteBackupDBFileName)
        CTYLBDB_tpd_inout_text.CreateNewTable( bakDbExec.s_dbConn)

        bWriteBackupDb = False

        origFinishRecIDArray = CTYLBDB_tpd_inout_text.GetStatus_RecID_Array( dbConn, CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Finish)
        for iRecID in origFinishRecIDArray:
            iInputReplyType, strContent, strSelfName, strDestName, iPeerStatus, strCreateTime, strReplyTime =\
                CTYLBDB_tpd_inout_text.ReadByRecID( dbConn, iRecID)
            if( strCreateTime):
                strCreateTime = strCreateTime.replace(u'.000', u'')
                realCreateTime = datetime.strptime( strCreateTime, '%Y-%m-%d %H:%M:%S')
            else:
                realCreateTime = datetime.now()
            if( strReplyTime):
                strReplyTime = strReplyTime.replace(u'.000', u'')
                realReplyTime = datetime.strptime( strReplyTime, '%Y-%m-%d %H:%M:%S')
            else:
                realReplyTime = datetime.now()

            if(bWriteBackupDb):
                CTYLBDB_tpd_inout_text.AddNewdRec( bakDbExec.s_dbConn, iInputReplyType, strContent, strSelfName, strDestName,
                                                   iPeerStatus, realCreateTime, realReplyTime)
            CTYLBDB_tpd_inout_text.DeleteRec( dbConn, iRecID)

        # 3. 对已经发送的，记录100前的数据包进行删除， 表send_recv_session 和 session_data的记录
        #    对于发送类型的数据包，本系统暂时无机制判断是否已经发送成功，只能暂时判断，最后sessionid-100，是对方已经接收到的。
        iRecStatus = CTYLB_SvClt_Cmd_Base_bytes.s_iSession_OutStatus_Handling
        s_g_iNeedCleanSessionIDDistance = 100  # 需要清除的会话ID距离值
        iCleanSendRecvTypeArray = [CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_SendOut,
                                   CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedPeerReSend,
                                   CTYLB_SvClt_Cmd_Base_bytes.s_iSessionRecType_NeedSelfExecReSend]

        for strEachName in strPeerNameArray:
            # 对每个用户名进行检查清除
            for iEachSendRecvType in iCleanSendRecvTypeArray:
                # 对每个数据类型进行检查清除
                iLastMaxSendSessionID = CTYLBDB_tpd_send_recv_session.GetMax_FromToUser_SendRecvType_SessionID(
                    dbConn, iEachSendRecvType, self.s_clientConfig.s_strMyID, strEachName)
                if(iLastMaxSendSessionID > s_g_iNeedCleanSessionIDDistance):
                    iExecCleanEachSessionID = iLastMaxSendSessionID - s_g_iNeedCleanSessionIDDistance
                    recIDArray = CTYLBDB_tpd_send_recv_session.Get_MyDestName_Status_RangeValueSession_RecIDArray(
                        dbConn, iEachSendRecvType, self.s_clientConfig.s_strMyID, strEachName, iRecStatus, iExecCleanEachSessionID)
                    for iEachRecID in recIDArray:
                        iSessionDataRecIDArray = CTYLBDB_tpd_session_data.GetBelongSessionID_RecID_Array(dbConn, iEachRecID)
                        for iEachSessionDataRecID in iSessionDataRecIDArray:
                            # 删除 会话数据
                            CTYLBDB_tpd_session_data.DeleteRec(dbConn, iEachSessionDataRecID)
                        # 删除会话记录
                        CTYLBDB_tpd_send_recv_session.DeleteRec(dbConn, iEachRecID)
                        pass
        pass

    @staticmethod
    def ShowLog( iWarnLevel, strMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'Client_MainRun', strMsg)
