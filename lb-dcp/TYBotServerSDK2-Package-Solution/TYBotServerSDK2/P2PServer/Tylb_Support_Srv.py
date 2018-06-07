# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Support_Srv.py support Server realize function
#
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# update to v3. config文件格式，和数据流结构json格式

import struct
import time
from datetime import datetime
from .Tylb_p2p_share import CTY_YamlFile, CTCPAcceptConnectMangClient_bytes, CExecConnectSockMang_bytes, CTCPListenSock, \
    CTYLB_Ct_NetBase_bytes, CTYLB_Mang_BusisUnit_Base_bytes, CTYLB_ShakeHand_NetBase_bytes, \
    CTYLB_SvClt_Cmd_Base_bytes, CTYLB_Busis_Packet, CTYLB_Comb_PackArray, CTYLB_Log, \
    CTY_WebClientPacket, CTYLB_Global_UnivTrans_Param, CTYLB_MainSys_MiscFunc
from .Tylb_p2p_Busines_func import CT2P_SHand_Ct_Srv
import queue
import json

g_iMaxExecIdleCount = 50  # 最大的执行休眠次数


# 服务端与服务端之间的命令定义
# start by sk. 170203
class CTYLB_PsvPsv_BaseCmd:
    s_iPsv_MainCmd_SvSv_DataTrans = 0  # 主命令：服务端之间传输
    s_iPsv_MainCmd_MultiV2Packet = 1  # 主命令：本数据包包含多个V2CmdPacket数据包
    s_iPsv_MainCmd_NullPacket = 2  # 主命令：本单元为空
    s_iPsv_DTrans_SubCmd_Unknown = 0  # 未知子命令
    s_iPsv_DTrans_SubCmd_DataTrans = 1  # 传输数据_源_目标客户名
    s_iPsv_DTrans_SubCmd_BCast_ClientOnLine = 2  # 向前广播客户端上线_源用户名
    s_iPsv_DTrans_SubCmd_Dest_NotRearch = 3  # 目标节点无法到达_目标用户名
    s_iPsv_DTrans_SubCmd_MultiV2Packet = 4  # 本数据包包含多个V2CmdPacket数据包
    s_iPsv_DTrans_SubCmd_NullPacket = 5  # 本单元为空
    s_iPsv_DTrans_SubCmd_MidBanance_DataTrans = 6  # 经过平衡的传输数据单元
    # 不能超过10，否则与 CTYLB_SvClt_Cmd_Base 子命令冲突。


# 客户端配置功能实现
# start by sk. 170124
# Pxk更新，171213
class CTYLB_PeerServer_Config:
    def __init__(self):
        self.s_strPeerSrvAddrArray = []  # 兄弟服务器地址队列
        self.s_strInitConnectClientAddrArray = []  # 主动连接的客户端地址队列
        self.s_iWaitPeerSrvConnectPort = 8087
        self.s_iClientSrvListenPort = 8088
        self.s_strMyID = None

    # Read Config Setting
    # start by sk. 170116
    def ReadFromConfigFile(self, strCfgFileName):
        yamlSrvCfgRead = CTY_YamlFile(strCfgFileName)
        yamlSrvCfgRead.load_configs()

        self.s_strMyID = yamlSrvCfgRead.get_config("peerserver.myid", 'pppnotinput')
        self.s_iWaitPeerSrvConnectPort = yamlSrvCfgRead.get_config('peerserver.peer_server_listen_port', 0)

        # 读取伙伴服务器列表
        for server in yamlSrvCfgRead.get_config('peerserver.peer_servers',[]):
            strPeerSrvAddr = server['addr']
            iPeerSrvPort = server['port']

            if strPeerSrvAddr == '' or strPeerSrvAddr == '0' or iPeerSrvPort == 0:
                continue
            self.s_strPeerSrvAddrArray.append((strPeerSrvAddr, iPeerSrvPort))

        # 读取监听等待客户端连接的断开
        self.s_iClientSrvListenPort = yamlSrvCfgRead.get_config('peerserver.client_listen_port', 0)

        # 读取需要主动连接的客户端列表
        for client in yamlSrvCfgRead.get_config('peerserver.clients',[]):
            strClientAddr = client['addr']
            iClientPort = client['port']

            if strClientAddr == '' or strClientAddr == '0' or iClientPort == 0:
                continue
            self.s_strInitConnectClientAddrArray.append((strClientAddr, iClientPort))


# 对方是服务端，进行辨别握手
# start by sk. 170126
class CTYLB_Sv_Sv_Identify_Unit(CTYLB_ShakeHand_NetBase_bytes):
    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_ShakeHand_NetBase_bytes.__init__(self, socketValue, iSockType, peerNetAddr)
        pass

    def __del__(self):
        pass


# 对方是客户端，进行辨别握手
# start by sk. 170126
class CTYLB_Sv_Client_Identify_Unit(CTYLB_ShakeHand_NetBase_bytes):
    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_ShakeHand_NetBase_bytes.__init__(self, socketValue, iSockType, peerNetAddr)
        pass

    def __del__(self):
        pass


# 管理服务端端的辨别单元队列，对方是服务端单元，对服务端进行握手
# start by sk. 170126
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_Mang_PeerSrv_NeedIdentify(CTYLB_Mang_BusisUnit_Base_bytes):
    def __init__(self, strServerName):
        CTYLB_Mang_BusisUnit_Base_bytes.__init__(self, strServerName)

    def __del__(self):
        pass

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        newServerUnit = CTYLB_Sv_Sv_Identify_Unit(socketValue, iSockType, peerAddress)
        return newServerUnit

    # 管套接收数据调度
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, strRecvData_bytes):
        CTYLB_Mang_BusisUnit_Base_bytes._Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue,
                                                                   strRecvData_bytes)
        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol

        identifySrvUnit = self.SearchUnitBySockValue(socketValue)
        if (not identifySrvUnit):
            iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock
        else:
            bProtocolOK = False

            # 是accept对象
            if (identifySrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                # 解包对方发送的post内容，如果正确，我回应 http结果
                bExactResult, strFromUniqueSign_bytes, tyCmdUnit, strFromUser_bytes, strDestUser_bytes, buildTime, \
                strNotHandleBuff_bytes = CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket(
                    strRecvData_bytes, True)
                if (bExactResult and tyCmdUnit):
                    # 我是accept，对方主动连接，对方是服务端，我是服务端，所以，对方先发一个pass包过来。
                    if (identifySrvUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None):
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Sv_10_Connect_ReportName):
                            if (tyCmdUnit.s_iSubCmd == CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Sv_10_None):
                                # 我构建回复包进行发送
                                strReplyContent_bytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                                    strFromUniqueSign_bytes, CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Sv_11_ReplyReportName,
                                    CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Sv_11_None, '', '', self.s_strMySelfName,
                                    False)
                                identifySrvUnit.TempShort_ExecSendPacket(strReplyContent_bytes)
                                iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData
                                identifySrvUnit.SetShakeHandResult(True)
                                bProtocolOK = True
                                identifySrvUnit.SetUnitName(tyCmdUnit.s_strContent)
                pass
            # 是connect对象
            elif (identifySrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 我已经发送了post内容，对方回应 http结果，此处进行分析解包
                bExactResult, strReplyUniqueSign_bytes, tyCmdUnit, strFromUser_bytes, strDestUser_bytes, buildTime, \
                strNotHandleBuff_bytes = CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket(
                    strRecvData_bytes, False)
                if (bExactResult and tyCmdUnit):
                    identifySrvUnit.GiveBack_SessionUniqueSign(strReplyUniqueSign_bytes)
                    # 我已经发送了握手包－告诉对方我的名字， 等待对方回应
                    if (
                        identifySrvUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1):
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Sv_11_ReplyReportName):
                            if (tyCmdUnit.s_iSubCmd == CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Sv_11_None):
                                identifySrvUnit.SetUnitName(tyCmdUnit.s_strContent)
                                iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply
                                bProtocolOK = True
                                # 握手成功
                                identifySrvUnit.SetShakeHandResult(True)
                pass
            if (not bProtocolOK):
                identifySrvUnit.SetShakeHandResult(False)
        return iReplyCode

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False

        for eachSrvIdenyUnit in self.s_mangUnitArray:
            # 是否主动连接？
            if (eachSrvIdenyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 状态是否在等待未执行
                if (eachSrvIdenyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None):
                    # 构建握手包，进行发送
                    if (eachSrvIdenyUnit.Is_LastSend_IdleTime_LargeThan(3)):
                        strTransUniqueSign_bytes = eachSrvIdenyUnit.Request_Free_SessionUniqueSign()  # 申请会话占用标识符
                        strSendPacket_bytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                            strTransUniqueSign_bytes,
                            CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Sv_10_Connect_ReportName,
                            CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Sv_10_None, '', '', self.s_strMySelfName, True)
                        bSendSucc = eachSrvIdenyUnit.TempShort_ExecSendPacket(strSendPacket_bytes)
                        eachSrvIdenyUnit.s_iShakeHandStepStatus = CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1 if bSendSucc \
                            else CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_PeerClose
                        bRetValue = True
                    pass
                elif (
                    eachSrvIdenyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1):
                    # 已经发送了第一个包，等待时间判断
                    if (eachSrvIdenyUnit.Is_LastSend_IdleTime_LargeThan(
                            CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxWaitHandSecond)):
                        eachSrvIdenyUnit.SetShakeHandResult(False)
            # 如果是被动连接，是否长时间无内容接收，如果是，则关闭
            elif (eachSrvIdenyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                if (eachSrvIdenyUnit.Is_LastSend_IdleTime_LargeThan(
                        CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxWaitComuInvalidIdleSecond)):
                    eachSrvIdenyUnit.SetShakeHandResult(False)
                pass

        return bRetValue

    # 判断是否有对象成功完成辨别
    def Pop_Finish_Identify_Server(self):
        retUnit = None
        for eachUnit in self.s_mangUnitArray:
            if ((eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_OK) or
                    (eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_Fail)):
                self.s_mangUnitArray.remove(eachUnit)
                retUnit = eachUnit
                break
        return retUnit


# 管理客户端的辨别单元队列，对方是客户端单元，对客户端进行握手
# start by sk. 170126
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_Mang_Client_NeedIdentify(CTYLB_Mang_BusisUnit_Base_bytes):
    def __init__(self, strServerName_bytes):
        CTYLB_Mang_BusisUnit_Base_bytes.__init__(self, strServerName_bytes)

    def __del__(self):
        pass

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        newServerUnit = CTYLB_Sv_Client_Identify_Unit(socketValue, iSockType, peerAddress)
        return newServerUnit

    # 管套接收数据调度
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, strRecvData_bytes):
        CTYLB_Mang_BusisUnit_Base_bytes._Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue,
                                                                   strRecvData_bytes)
        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol

        identifyUnit = self.SearchUnitBySockValue(socketValue)
        if (not identifyUnit):
            iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock
        else:
            bProtocolOK = False

            # 是accept对象
            if (identifyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                # 解包对方发送的post内容，如果正确，我回应 http结果
                bExactResult, strFromTransUniqueSign_bytes, tyCmdUnit, strFromUser_bytes, strDestUser_bytes, buildTime, \
                strNotHandleBuff_bytes = CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket(
                    strRecvData_bytes, True)
                if (bExactResult and tyCmdUnit):
                    # 我是accept，对方主动连接，对方是服务端，我是client，所以，对方先发一个pass包过来。
                    if (identifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None):
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_1_ReportName):
                            if (tyCmdUnit.s_iSubCmd == CT2P_SHand_Ct_Srv.s_iSubCmd_Ct_Sv_1_None):
                                # 我构建回复包进行发送
                                strReplyContent_bytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                                    strFromTransUniqueSign_bytes,
                                    CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_2_ReplySrvName,
                                    CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Ct_2_None, '', '', self.s_strMySelfName,
                                    False)
                                identifyUnit.TempShort_ExecSendPacket(strReplyContent_bytes)
                                identifyUnit.SetUnitName(tyCmdUnit.s_strContent)
                                iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData
                                identifyUnit.SetShakeHandResult(True)
                                bProtocolOK = True
                pass
            # 是connect对象
            elif (identifyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 我已经发送了post内容，对方回应 http结果，此处进行分析解包
                bExactResult, strReplyTransUniqueSign_bytes, tyCmdUnit, strFromUser_bytes, strDestUser_bytes, buildTime, \
                strNotHandleBuff_bytes = CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket(
                    strRecvData_bytes, False)
                if (bExactResult and tyCmdUnit):
                    identifyUnit.GiveBack_SessionUniqueSign(strReplyTransUniqueSign_bytes)  # 归还释放会话占用标识符
                    # 我已经发送了握手包－告诉对方我的名字， 等待对方回应
                    if (
                        identifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1):
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_1_ReportName):
                            if (tyCmdUnit.s_iSubCmd == CT2P_SHand_Ct_Srv.s_iSubCmd_Ct_Sv_1_None):
                                iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply
                                bProtocolOK = True
                                # 握手成功
                                identifyUnit.SetShakeHandResult(True)
                pass
            if (not bProtocolOK):
                identifyUnit.SetShakeHandResult(False)
        return iReplyCode

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False

        for eachUnit in self.s_mangUnitArray:
            # 是否主动连接？
            if (eachUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 状态是否在等待未执行
                if (eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None):
                    # 构建握手包，进行发送
                    strTransUniqueSign_bytes = eachUnit.Request_Free_SessionUniqueSign()  # 申请会话占用标识符
                    strSendPacket_bytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                        strTransUniqueSign_bytes,
                        CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_7_Connect_SendCheck,
                        CT2P_SHand_Ct_Srv.s_iSubCmd_Sv_Ct_7_None, '', '', self.s_strMySelfName, True)
                    bSendSucc = eachUnit.TempShort_ExecSendPacket(strSendPacket_bytes)
                    eachUnit.s_iShakeHandStepStatus = CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1 if bSendSucc else \
                        CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_PeerClose
                    bRetValue = True
                    pass
                elif (eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iClientHand_Connect_Send1):
                    # 已经发送了第一个包，等待时间判断
                    if (eachUnit.Is_LastSend_IdleTime_LargeThan(CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxWaitHandSecond)):
                        eachUnit.SetShakeHandResult(False)
            # 如果是被动连接，是否长时间无内容接收，如果是，则关闭
            elif (eachUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                if (eachUnit.Is_LastSend_IdleTime_LargeThan(
                        CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxWaitComuInvalidIdleSecond)):
                    eachUnit.SetShakeHandResult(False)
                pass

        return bRetValue

    # 判断是否有对象成功完成辨别
    def Pop_Finish_Identify_Server(self):
        retUnit = None
        for eachUnit in self.s_mangUnitArray:
            if ((eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_OK) or
                    (eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_Fail)):
                self.s_mangUnitArray.remove(eachUnit)
                retUnit = eachUnit
                break
        return retUnit


# 服务端存储执行传输给客户端的管理单元
# start by sk. 170130
class CTYLB_Trans_Exec_StoreToClient_Unit:
    def __init__(self, bSrvDirectSend, strFromUser, iSubCmd, strContent):
        self.s_strFromUser = strFromUser
        self.s_iSubCmd = iSubCmd
        self.s_strContent = strContent
        self.s_bSrvDirectSend = bSrvDirectSend


# 服务端管理对象存储，待处理的客户端数据包
# start by sk. 170130
class CTYLB_Trans_NeedExec_RecvContentUnit:
    def __init__(self, strFromUser, strToUser, iSubCmd, strContent):
        self.s_strFromUser = strFromUser
        self.s_strToUser = strToUser
        self.s_iSubCmd = iSubCmd
        self.s_strContent = strContent


# 中间路径单元
# start by sk. 170203
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTY_MidPath_PackUnit:
    s_strMidPathSign = 'md##x'  # 本单元的数据包标记
    s_strOrigSrcPathJoin = '%w##'  # 源服务器的分割标记
    s_strDstPathJoin = '%x#@'  # 源服务器的分割标记
    s_strEmptyPath = '$$empty$$'  # 空路径
    s_strMidPathSeperate = '##mpsepxx$$'

    # 初始化
    def __init__(self):
        self.s_strDestNextSrvArray = []  # 需要继续到达的服务器队列
        self.s_strOrigSrvSrvArray = []  # 源经过的服务端队列

    # 释放类对象
    def __del__(self):
        pass

    # 设置内容
    def SetSrcDstPath(self, strSrcPathArray, strDstPathArray):
        self.SetDstPath(strDstPathArray)
        self.s_strOrigSrvSrvArray = []  # 源经过的服务端队列
        if (strSrcPathArray):
            self.s_strOrigSrvSrvArray.extend(strSrcPathArray)

    # 设置目标路径内容
    def SetDstPath(self, strDstPathArray):
        self.s_strDestNextSrvArray = []  # 需要继续到达的服务器队列
        if (strDstPathArray):
            self.s_strDestNextSrvArray.extend(strDstPathArray)
        pass

    # 将目标路径的第一个去除，表示已经到达了本节点
    def PopFirstNameFromDstPath(self):
        if (self.s_strDestNextSrvArray):
            self.s_strDestNextSrvArray.pop(0)

    # 将节点单元加入到经过的路径
    def AddNameToSrcPath(self, strUnitName):
        self.s_strOrigSrvSrvArray.append(strUnitName)

    s_g_Key_strSign = 'str_sign'
    s_g_Key_strMidPath = 'str_midPath'
    s_g_Key_strDestPath = 'str_destPath'
    s_g_Key_strContent = 'str_content'

    # 获得组合数据包。
    # 数据格式：#sign#len1#len2#src_path1-srv_path2#dst_path1-dst_path2#
    # 返回值： strFormat, strBuffer --- 封装的数据格式，字符串缓冲数据
    def GetCombindPathData(self):
        exJson = {}

        exJson[CTY_MidPath_PackUnit.s_g_Key_strSign] = CTY_MidPath_PackUnit.s_strMidPathSign
        exJson[CTY_MidPath_PackUnit.s_g_Key_strMidPath] = self.s_strOrigSrcPathJoin.join(self.s_strOrigSrvSrvArray)
        exJson[CTY_MidPath_PackUnit.s_g_Key_strDestPath] = self.s_strDstPathJoin.join(self.s_strDestNextSrvArray)

        strTotal = json.dumps(exJson, ensure_ascii=False)
        return strTotal

    # 分解组合数据包
    # strFormat --- 数据格式
    # strBuffer --- 经过封装的缓冲内容
    # 返回值：bool, strFromUser_bytes, strDestUser_bytes, iMainCmd, iSubCmd, cmdBuildTime, strCmdContent_bytes
    def ExactCombindPathData(self, strBuffer):
        bRetValue = False
        # 清空
        self.SetSrcDstPath(None, None)

        strOrigBuff = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strBuffer)
        try:
            origJson = json.loads(strOrigBuff)

            if( origJson[CTY_MidPath_PackUnit.s_g_Key_strSign] == CTY_MidPath_PackUnit.s_strMidPathSign):
                strFromPath = origJson[CTY_MidPath_PackUnit.s_g_Key_strMidPath]
                strDestPath = origJson[CTY_MidPath_PackUnit.s_g_Key_strDestPath]

                strExactFromPathArray, strExactDestPathArray = [], []
                if(strFromPath):
                    strExactFromPathArray = strFromPath.split(self.s_strOrigSrcPathJoin)
                if(strDestPath):
                    strExactDestPathArray = strFromPath.split(self.s_strDstPathJoin)

                self.SetSrcDstPath(strExactFromPathArray, strExactDestPathArray)
                bRetValue = True
        except:
            pass

        return bRetValue


    # 提取下一个目标到达的节点
    def PopRetriveNextDestPath(self, bRemove=True):
        strRetNextSrvName = ''
        if (len(self.s_strDestNextSrvArray) > 0):
            if (bRemove):
                strRetNextSrvName = self.s_strDestNextSrvArray.pop(0)
            else:
                strRetNextSrvName = self.s_strDestNextSrvArray[0]
        return strRetNextSrvName

    # 增加节点到来源路径
    def AddAppendToFromPath(self, strPassUnit):
        self.s_strOrigSrvSrvArray.append(strPassUnit)
        pass

    # 获得上一个经过的服务器节点
    def Get_LastSrvName_From_FromPath(self):
        strRetLastSrvName = ''
        if (len(self.s_strOrigSrvSrvArray) > 0):
            strRetLastSrvName = self.s_strOrigSrvSrvArray.pop()
        return strRetLastSrvName

    # 反转路径队列
    # start by sk. 170203
    @staticmethod
    def ReversePathArray(strPathArray):
        retPathArray = []
        iCount = len(strPathArray)
        for iIndex in range(iCount):
            retPathArray.append(strPathArray[iCount - iIndex - 1])
        return retPathArray


# 服务端之间传输的数据包单元封装类
# start by sk. 170203
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTY_CmdV2PackUnit:
    s_g_iSelfBaseSize = 50  # 本身单元基本大小
    s_g_iStepMultiPackCount = 4  # 每次压缩4个单元

    s_strV2PackUnitSign = '2p##x'  # 本单元的数据包标记
    s_g_strV2MultiPackSign = '2mp#x'  # 本单元多包的标记

    # 初始化
    def __init__(self, copyFromUnit=None):
        self.s_midPathUnit = CTY_MidPath_PackUnit()
        self.s_strOrigTyCmdPack = ''
        self.s_strSrcUserID = ''
        self.s_strDestUserID = ''
        self.s_iMainSrvCmd = 0
        self.s_iSubSrvCmd = 0

        if (copyFromUnit):
            self.SetSrcDstUserID(copyFromUnit.s_strSrcUserID, copyFromUnit.s_strDestUserID)
            self.SetSrvCmd(copyFromUnit.s_iMainSrvCmd, copyFromUnit.s_iSubSrvCmd)
            self.s_midPathUnit = CTY_MidPath_PackUnit()
            self.s_midPathUnit.s_strOrigSrvSrvArray.extend(copyFromUnit.s_midPathUnit.s_strOrigSrvSrvArray)
            self.s_midPathUnit.s_strDestNextSrvArray.extend(
                copyFromUnit.s_midPathUnit.s_strDestNextSrvArray)
            self.s_strOrigTyCmdPack = copyFromUnit.s_strOrigTyCmdPack
        else:
            self.SetSrcDstUserID('', '')
            self.SetSrvCmd(0, 0)
            self.s_strOrigTyCmdPack = ''

    # 释放类对象
    def __del__(self):
        pass

    # 设置源目标用户ID
    def SetSrcDstUserID(self, strSrcID, strDstID):
        self.s_strSrcUserID = strSrcID
        self.s_strDestUserID = strDstID

    # 中间路径单元
    def SetSrvCmd(self, iMainCmd, iSubCmd):
        self.s_iMainSrvCmd = iMainCmd
        self.s_iSubSrvCmd = iSubCmd

    s_g_Key_strV2Sign = 'str_v2sign'
    s_g_Key_strSrcUserID = 'str_srcuserid'
    s_g_Key_strDestUserID = 'str_destuserid'
    s_g_Key_iMainSrvCmd = 'iMainSrvCmd'
    s_g_Key_iSubSrvCmd = 'iSubSrvCmd'
    s_g_Key_strPathBuff = 'strPathBuff'
    s_g_Key_strOrigTyCmdPack = 'strOrigTyCmdPack'

    # 获得组合数据包。
    # 数据格式：$# 标志$# 来自用户ID $# 目标用户ID $# 主命令 $# 子命令  $# 路径内容 $# 原tycmd数据包内容 $#
    # 返回值： strFormat, strBuffer --- 封装的数据格式，字符串缓冲数据
    def GetCombindData(self):
        exJson = {}

        exJson[CTY_CmdV2PackUnit.s_g_Key_strV2Sign] = CTY_CmdV2PackUnit.s_strV2PackUnitSign
        exJson[CTY_CmdV2PackUnit.s_g_Key_strSrcUserID] = self.s_strSrcUserID
        exJson[CTY_CmdV2PackUnit.s_g_Key_strDestUserID] = self.s_strDestUserID
        exJson[CTY_CmdV2PackUnit.s_g_Key_iMainSrvCmd] = self.s_iMainSrvCmd
        exJson[CTY_CmdV2PackUnit.s_g_Key_iSubSrvCmd] = self.s_iSubSrvCmd
        exJson[CTY_CmdV2PackUnit.s_g_Key_strPathBuff] = self.s_midPathUnit.GetCombindPathData()
        exJson[CTY_CmdV2PackUnit.s_g_Key_strOrigTyCmdPack] = self.s_strOrigTyCmdPack

        strTotal = json.dumps(exJson, ensure_ascii=False)
        return strTotal

    # 大概预估本单元的流空间大小
    # 返回值： 长度值
    def GetNearlyUnitSize(self):
        iRetNearlySize = CTY_CmdV2PackUnit.s_g_iSelfBaseSize + len(self.s_strOrigTyCmdPack_bytes)
        return iRetNearlySize

    s_g_Key_V2StrSign = 'strV2Sign'
    s_g_Key_V2Str_1 = "str_V2_1"
    s_g_Key_V2Str_2 = "str_V2_2"
    s_g_Key_V2Str_3 = "str_V2_3"
    s_g_Key_V2Str_0 = "str_V2_0"

    # 综合多个数据包，把多个数据包综合为当前一个数据包
    # 返回值： 综合buffer
    # start by sk. 170207
    @staticmethod
    def CombineMultiV2PacketIntoTotalUnit(v2PackUnitArray):
        iPackCount = len(v2PackUnitArray)
        # 大于需要分组的个数，进行分组
        if (iPackCount > CTY_CmdV2PackUnit.s_g_iStepMultiPackCount):
            iEachSplitPackCount = int((
                                      iPackCount + CTY_CmdV2PackUnit.s_g_iStepMultiPackCount - 1) /
                                      CTY_CmdV2PackUnit.s_g_iStepMultiPackCount)
            iCurIndex = 0
            eachPackArray = []
            midTotPackUnitArray = []
            for iEachIndex in range(iPackCount):
                eachPackArray.append(v2PackUnitArray[iEachIndex])
                iCurIndex += 1
                # 当前是否充足？
                if (iCurIndex >= iEachSplitPackCount):
                    # 填充足够，分成一个综合包
                    strEachTotal = CTY_CmdV2PackUnit.CombineMultiV2PacketIntoTotalUnit(eachPackArray)
                    newPackUnit = CTY_CmdV2PackUnit()
                    newPackUnit.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_MultiV2Packet,
                                          CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Unknown)
                    newPackUnit.s_strOrigTyCmdPack_bytes = strEachTotal
                    midTotPackUnitArray.append(newPackUnit)
                    # 重新清0
                    eachPackArray = []
                    iCurIndex = 0
                    pass
            if ((iCurIndex > 0) and (iCurIndex < iEachSplitPackCount)):
                for iLeftSubIndex in range(iCurIndex, iEachSplitPackCount):
                    # 不够数量，用空包填充
                    nullV2Packet = CTY_CmdV2PackUnit()
                    nullV2Packet.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_NullPacket,
                                           CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Unknown)
                    eachPackArray.append(nullV2Packet)
                # 填充足够，组成综合包
                strEachTotal = CTY_CmdV2PackUnit.CombineMultiV2PacketIntoTotalUnit(eachPackArray)
                newPackUnit = CTY_CmdV2PackUnit()
                newPackUnit.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_MultiV2Packet,
                                      CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Unknown)
                newPackUnit.s_strOrigTyCmdPack_bytes = strEachTotal
                midTotPackUnitArray.append(newPackUnit)
            strMultiTotal = CTY_CmdV2PackUnit.CombineMultiV2PacketIntoTotalUnit(midTotPackUnitArray)
        else:
            # 数量足够吗？如果不够，填充到4个，进行封装组合
            fitCountArray = []
            fitCountArray.extend(v2PackUnitArray)
            # 需要填充多少个空包？
            iNeedFillCount = CTY_CmdV2PackUnit.s_g_iStepMultiPackCount - iPackCount
            if (iNeedFillCount > 0):
                for iFill in range(iNeedFillCount):
                    nullV2Packet = CTY_CmdV2PackUnit()
                    nullV2Packet.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_NullPacket,
                                           CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Unknown)
                    fitCountArray.append(nullV2Packet)
            strExBuffArray = []
            for eachExUnit in fitCountArray:
                strEachBuff = eachExUnit.GetCombindData()
                strExBuffArray.append(strEachBuff)

            exJson = {}
            exJson[CTY_CmdV2PackUnit.s_g_Key_V2StrSign] = CTY_CmdV2PackUnit.s_g_strV2MultiPackSign
            exJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_0] = strExBuffArray[0]
            exJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_1] = strExBuffArray[1]
            exJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_2] = strExBuffArray[2]
            exJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_3] = strExBuffArray[3]

            strMultiTotal = json.dumps(exJson, ensure_ascii=False)

        return strMultiTotal

    # 分解多个组合的数据包
    # start by sk. 170207
    @staticmethod
    def ExactMultiV2PacketFromTotalUnit(strMultiPackBuff):
        retV2UnitPackArray = []

        strOrigMultiBuff = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strMultiPackBuff)
        try:
            origJson = json.loads(strOrigMultiBuff)

            if( origJson[CTY_CmdV2PackUnit.s_g_Key_V2StrSign] == CTY_CmdV2PackUnit.s_g_strV2MultiPackSign):
                strEachContentArray = []
                strEachContentArray.append(origJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_0])
                strEachContentArray.append(origJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_1])
                strEachContentArray.append(origJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_2])
                strEachContentArray.append(origJson[CTY_CmdV2PackUnit.s_g_Key_V2Str_3])

                for eachContent in strEachContentArray:
                    newV2PackUnit = CTY_CmdV2PackUnit()
                    if (newV2PackUnit.ExactCombindData(eachContent)):
                        if (newV2PackUnit.s_iMainSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_NullPacket):
                            pass
                        elif (newV2PackUnit.s_iMainSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_MultiV2Packet):
                            strCurV2PackArray = CTY_CmdV2PackUnit.ExactMultiV2PacketFromTotalUnit(
                                newV2PackUnit.s_strOrigTyCmdPack)
                            retV2UnitPackArray.extend(strCurV2PackArray)
                        else:
                            retV2UnitPackArray.append(newV2PackUnit)
        except:
            pass

        return retV2UnitPackArray

    # 分解组合数据包
    # strFormat --- 数据格式
    # strBuffer --- 经过封装的缓冲内容
    # 返回值：bool
    def ExactCombindData(self, strBuffer):
        bRetValue = False
        self.s_strSrcUserID = ''
        self.s_strDestUserID = ''
        self.s_iMainSrvCmd = 0
        self.s_iSubSrvCmd = 0
        self.s_strOrigTyCmdPack = ''
        self.s_midPathUnit.ExactCombindPathData('')

        strOrigBuff = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strBuffer)
        try:
            exJson = json.loads(strOrigBuff)

            if( exJson[CTY_CmdV2PackUnit.s_g_Key_strV2Sign] == CTY_CmdV2PackUnit.s_strV2PackUnitSign):
                self.s_strSrcUserID = exJson[CTY_CmdV2PackUnit.s_g_Key_strSrcUserID]
                self.s_strDestUserID = exJson[CTY_CmdV2PackUnit.s_g_Key_strDestUserID]
                self.s_iMainSrvCmd = exJson[CTY_CmdV2PackUnit.s_g_Key_iMainSrvCmd]
                self.s_iSubSrvCmd = exJson[CTY_CmdV2PackUnit.s_g_Key_iSubSrvCmd]

                strPathBuff = exJson[CTY_CmdV2PackUnit.s_g_Key_strPathBuff]
                self.s_midPathUnit.ExactCombindPathData(strPathBuff)

                self.s_strOrigTyCmdPack = exJson[CTY_CmdV2PackUnit.s_g_Key_strOrigTyCmdPack]
                bRetValue = True
        except:
            pass

        return bRetValue

    # 数据包是否为空
    # start by sk. 170216
    def IsEmpty(self):
        bRetValue = False
        if ((self.s_iMainSrvCmd == 0) and (self.s_iSubSrvCmd == 0)):
            bRetValue = True
        return bRetValue


# 服务器与服务器之间，通信实现的基本功能
# start by sk. 170203
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_PsvPsv_Trans_Real_BaseFunc:
    # 从数据包中，分析命令单元
    # start by sk. 170203
    @staticmethod
    def Analy_Each_Exact_CmdV2Unit_FromPacket(strHttpPacket_bytes, bHttp_SendPost_or_RecvReply):
        bRetExactResult = True
        replyCmdV2PackUnit = None
        strNotHandleBuff_bytes = b''

        webClientPack = CTY_WebClientPacket()
        if (bHttp_SendPost_or_RecvReply):  # 是Post数据
            # 解包对方发送的post内容，如果正确，我回应 http结果
            strOrigPacket, strRetUniqueSign, strNotHandleBuff_bytes = webClientPack.Srv_Exact_From_RecvPostPacket(
                strHttpPacket_bytes)
        else:
            # 解包对方发送的post内容，如果正确，我回应 http结果
            strOrigPacket, strRetUniqueSign, strNotHandleBuff_bytes = webClientPack.Client_Exact_From_RecvWebReplyPacket(
                strHttpPacket_bytes)

        if (strOrigPacket):
            replyCmdV2PackUnit = CTY_CmdV2PackUnit()
            if (replyCmdV2PackUnit.ExactCombindData(strOrigPacket)):
                bRetExactResult = True
        return bRetExactResult, strRetUniqueSign, replyCmdV2PackUnit, strNotHandleBuff_bytes

    # 整合完整输出包，作为格式
    # start by sk. 170203
    @staticmethod
    def Build_FullPacket_With_CmdV2Unit(strUniqueSign, cmdV2Packet, bHttp_SendPost_or_RecvReply):
        if (cmdV2Packet):
            strReplyCombData = cmdV2Packet.GetCombindData()
        else:
            emptyCmdV2PackUnit = CTY_CmdV2PackUnit()
            strReplyCombData = emptyCmdV2PackUnit.GetCombindData()

        webClientPack = CTY_WebClientPacket()
        if (bHttp_SendPost_or_RecvReply):
            strReplyContent_bytes = webClientPack.Client_Data_To_SendPostPacket(strUniqueSign,
                                                                                strReplyCombData)
        else:
            strReplyContent_bytes = webClientPack.Srv_Data_To_WebReplyPacket(strUniqueSign,
                                                                             strReplyCombData)

        return strReplyContent_bytes


# 服务端权限判断功能
# start by sk. 170204
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Psv_PrivRight_Check:
    # 此用户名，可否向前传输或者广播
    # start by sk. 170204
    @staticmethod
    def IsUserNameCanSendBcast(strFromName, strDestClientName):
        bSendUserOnlineMsgToClient = False
        if (strFromName == CTYLB_SvClt_Cmd_Base_bytes.s_g_strConsoleName):
            # 可以向控制台广播
            bSendUserOnlineMsgToClient = True
            pass
        elif (strDestClientName == CTYLB_SvClt_Cmd_Base_bytes.s_g_strConsoleName):
            # 控制台向其他客户端广播
            bSendUserOnlineMsgToClient = True
            pass
        else:
            bSendUserOnlineMsgToClient = False
            pass
        return bSendUserOnlineMsgToClient


# 客户端单元
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_ClientUnit(CTYLB_Ct_NetBase_bytes):
    # s_tobeSendClientBuffArray_bytes = []  # 到客户端的存储单元队列 CTYLB_Trans_Exec_StoreToClient_Unit

    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_Ct_NetBase_bytes.__init__(self, socketValue, iSockType, peerNetAddr)
        self.s_tobeSendClientBuffArray = []
        pass

    def __del__(self):
        pass

    # 获得下一个，针对目标服务端，可以发送的数据包
    # start by sk. 170128
    def Pop_GetNext_SendablePacket(self):
        iMaxSendPackSize = 10000  # 10k

        iExecRetSubCmd, strExecRetFromUser, strExecRetContentBuff = self.Convert_Pop_Comb_SendPacketArray(
            iMaxSendPackSize)

        strRetFromtUser = strExecRetFromUser
        strRetContentBuff = strExecRetContentBuff
        iRetSubCmd = iExecRetSubCmd
        return strRetFromtUser, self.s_strUnitName, iRetSubCmd, strRetContentBuff

    # 转换，综合成可发送的数据包队列，返回string
    #  iMaxBuffSize --- 最大的缓冲大小
    # start by sk. 170128
    def Convert_Pop_Comb_SendPacketArray(self, iMaxBuffSize=0):
        strRetSendTotalPacket = ''
        iRetSubCmd = 0
        strRetFromUser = ''

        bFirstPacket = True
        srvDirectSendUnitArray = []
        iSrvDirectSendTotalPackSize = 0  # 调度发送的数据包大小
        bExecCombSrvSendPacket = False  # 执行综合发送服务端数据包，还是发送客户端中转包？

        while (True):
            if (not self.s_tobeSendClientBuffArray):
                break

            curNextPackUnit = self.s_tobeSendClientBuffArray[0]
            if (not curNextPackUnit.s_bSrvDirectSend):
                # 是其他客户端转发的，直接提取，返回
                if (bFirstPacket):
                    # 第一个数据包，是客户端转发，直接返回
                    curNextPackUnit = self.s_tobeSendClientBuffArray.pop(0)
                    strRetSendTotalPacket = curNextPackUnit.s_strContent
                    bExecCombSrvSendPacket = False
                    iRetSubCmd = curNextPackUnit.s_iSubCmd
                    strRetFromUser = curNextPackUnit.s_strFromUser
                else:
                    # 以前一直在处理服务端发送包，跳出循环，停止处理
                    # 只要是第二个数据包以上，那么，就表示以前一直在处理服务端数据包。现在碰到客户端包，所以停止处理
                    bExecCombSrvSendPacket = True
                # 只要是客户端转发的，都直接传输发送。停止多包封装
                break
            else:
                # 是服务端转发的数据包类型
                # 无论是第一个，还是第几个，均加入队列
                if (bFirstPacket):
                    bExecCombSrvSendPacket = True

                # 是客户端处理包
                curNextPackUnit = self.s_tobeSendClientBuffArray.pop(0)
                curNewTmpBusisPacket = CTYLB_Busis_Packet(curNextPackUnit.s_iSubCmd, 0, 0, 0, curNextPackUnit.s_strContent)
                iSrvDirectSendTotalPackSize += curNewTmpBusisPacket.NearCalcTransLength()
                srvDirectSendUnitArray.append(curNewTmpBusisPacket)
                if (iMaxBuffSize > 0):
                    if (iSrvDirectSendTotalPackSize >= iMaxBuffSize):
                        break
            bFirstPacket = False
        if (bExecCombSrvSendPacket):
            # 服务端发送包，综合发送
            if (len(srvDirectSendUnitArray) > 0):
                strRetSendTotalPacket = CTYLB_Comb_PackArray.GetCombindData(srvDirectSendUnitArray)
                iRetSubCmd = 0
                strRetFromUser = ''
        else:
            # 客户端转发包，以前已经处理
            if (len(srvDirectSendUnitArray) > 0):
                CTYLB_Log.ShowLog(1, 'sv_client_Unit', 'why discard poped unit? %d' % (len(srvDirectSendUnitArray)))
            pass

        return iRetSubCmd, strRetFromUser, strRetSendTotalPacket

    # 调度下一个可以发送的数据包, 数据包由服务端直接提请发送，发送时需要封装
    # start by sk. 170128
    def Prompt_Srv_DirectSend_Pack_ToBe_Send(self, strFromUser, iSubCmd, strPacket):
        newUnit = CTYLB_Trans_Exec_StoreToClient_Unit(True, strFromUser, iSubCmd, strPacket)
        self.s_tobeSendClientBuffArray.append(newUnit)

    # 调度下一个可以发送的数据包，由其他地方转发，不需要再封装了
    # start by sk. 170128
    def Prompt_ReTransable_Pack_ToBe_Send(self, strFromUser, iSubCmd, strPacket):
        newUnit = CTYLB_Trans_Exec_StoreToClient_Unit(False, strFromUser, iSubCmd, strPacket)
        self.s_tobeSendClientBuffArray.append(newUnit)

    pass


# 在伙伴服务器上，可到达的客户端单元 信息
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_ClientInPeerSrv:
    # s_strClientName = ''  # 节点名字
    # s_strMidPathArray = []   # 到达客户端的中间路径

    def __init__(self, strClientName, strMidPathArray):
        self.s_strClientName = strClientName
        self.s_strMidPathArray = []
        self.UpdateMidPath(strMidPathArray)
        pass

    # 更新路径
    # start by sk. 170203
    def UpdateMidPath(self, strPathArray):
        self.s_strMidPathArray = []
        self.s_strMidPathArray.extend(strPathArray)

    pass


# 伙伴服务端单元
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_PeerSrvUnit(CTYLB_Ct_NetBase_bytes):
    # s_clientRearchUnitArray = []  # 到客户端的存储单元队列 CTYLB_Sv_ClientInPeerSrv
    # s_toBeSendCmdPackArray = []  # 需要发送的节点单元 CTY_CmdV2PackUnit
    # s_recv_ToBeHandle_CmdV2Unit_Array = []   # 接收到等待处理的V2单元队列 CTY_CmdV2PackUnit

    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_Ct_NetBase_bytes.__init__(self, socketValue, iSockType, peerNetAddr)
        self.s_clientRearchUnitArray = []  # 到客户端的存储单元队列 CTYLB_Sv_ClientInPeerSrv
        self.s_toBeSendCmdPackArray = []  # 需要发送的节点单元 CTY_CmdV2PackUnit
        self.s_recv_ToBeHandle_CmdV2Unit_Array = []  # 接收到等待处理的V2单元队列 CTY_CmdV2PackUnit
        pass

    def __del__(self):
        pass

    # 获得可到达的客户端单元
    # start by sk. 170203
    def GetRearchClientUnitByName(self, strClientName):
        retClientUnit = None
        for eachSvClient in self.s_clientRearchUnitArray:
            if (eachSvClient.s_strClientName == strClientName):
                retClientUnit = eachSvClient
                break
        return retClientUnit

    pass

    # 提交客户端接收到的数据包，进行存储，等待调度
    # start by sk. 170203
    def Prompt_RecvClientPacket_ToBe_StoreSend(self, strSelfID, strFromUser, strToUser, iClientSubCmd,
                                               strOrigTyCmdPackBuff):
        rearchClientUnit = self.GetRearchClientUnitByName(strToUser)
        if (rearchClientUnit):
            iSrvMainCmd = CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_SvSv_DataTrans
            if (iClientSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_Db_Session_Trans):
                iSrvSubCmd = CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_DataTrans
            elif (iClientSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans):
                iSrvSubCmd = CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_MidBanance_DataTrans
            else:
                iSrvSubCmd = CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Unknown

            newPackUnit = CTY_CmdV2PackUnit()
            newPackUnit.SetSrcDstUserID(strFromUser, strToUser)
            newPackUnit.SetSrvCmd(iSrvMainCmd, iSrvSubCmd)
            newPackUnit.s_strOrigTyCmdPack = strOrigTyCmdPackBuff
            newPackUnit.s_midPathUnit.SetDstPath(rearchClientUnit.s_strMidPathArray)
            newPackUnit.s_midPathUnit.AddAppendToFromPath(strSelfID)  # 是从我这边开始发出去的
            self.TmpStore_NeedWaitSend_CmdV2Pack(newPackUnit)
        pass

    # 存储接收到待处理的数据包
    # start by sk. 170203
    def TmpStore_Recv_CmdV2Pack(self, cmdV2PackUnit):
        if (cmdV2PackUnit.s_iMainSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_NullPacket):
            pass
        elif (cmdV2PackUnit.s_iMainSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_MultiV2Packet):
            recvV2PackUnitArray = CTY_CmdV2PackUnit.ExactMultiV2PacketFromTotalUnit(
                cmdV2PackUnit.s_strOrigTyCmdPack)
            for eachV2PackUnit in recvV2PackUnitArray:
                self.TmpStore_Recv_CmdV2Pack(eachV2PackUnit)
            pass
        else:
            self.s_recv_ToBeHandle_CmdV2Unit_Array.append(cmdV2PackUnit)
        pass

    # 存储等待发送的数据包
    # start by sk. 170203
    def TmpStore_NeedWaitSend_CmdV2Pack(self, cmdV2PackUnit):
        self.s_toBeSendCmdPackArray.append(cmdV2PackUnit)

    # 取出可调度发送的命令包
    # start by sk. 170203
    def Pop_Single_SendAble_CmdV2Pack(self):
        retCmdV2PackUnit = None
        if (self.s_toBeSendCmdPackArray):
            retCmdV2PackUnit = self.s_toBeSendCmdPackArray.pop(0)
        return retCmdV2PackUnit

    # 取出可调度发送的命令包
    # start by sk. 170207
    def Pop_Multi_SendAble_CmdV2Pack(self, iMaxPackSize):
        retCmdV2PackUnit = None

        exMultiV2PackArray = []
        iCurExSize = 0
        while (True):
            nextPopV2Pack = self.Pop_Single_SendAble_CmdV2Pack()
            if (not nextPopV2Pack):
                break
            iCurExSize += nextPopV2Pack.GetNearlyUnitSize()
            exMultiV2PackArray.append(nextPopV2Pack)
            if (iCurExSize >= iMaxPackSize):
                break
        if (len(exMultiV2PackArray) > 0):
            strTotExBuff = CTY_CmdV2PackUnit.CombineMultiV2PacketIntoTotalUnit(exMultiV2PackArray)
            retExPack = CTY_CmdV2PackUnit()
            retExPack.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_MultiV2Packet,
                                CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Unknown)
            retExPack.s_strOrigTyCmdPack = strTotExBuff
            retCmdV2PackUnit = retExPack

        return retCmdV2PackUnit

    # 取出一个待处理的接收包
    # start by sk. 170203
    def Pop_RecvNeedExec_CmdV2Pack(self):
        retCmdV2PackUnit = None
        if (self.s_recv_ToBeHandle_CmdV2Unit_Array):
            retCmdV2PackUnit = self.s_recv_ToBeHandle_CmdV2Unit_Array.pop(0)
        return retCmdV2PackUnit

    # 更新可到达的客户端对象
    # start by sk. 170203
    def UpdateReachAbleClient(self, strClientName_bytes, strDestPathArray_bytes):
        clientUnit = self.GetRearchClientUnitByName(strClientName_bytes)
        if (clientUnit):
            clientUnit.UpdateMidPath(strDestPathArray_bytes)
        else:
            clientUnit = CTYLB_Sv_ClientInPeerSrv(strClientName_bytes, strDestPathArray_bytes)
            self.s_clientRearchUnitArray.append(clientUnit)

    # 客户端下线了
    # start by sk. 170203
    def NotifyClientUnitOffLine(self, strClientName):
        for eachUnit in self.s_clientRearchUnitArray:
            if (eachUnit.s_strClientName == strClientName):
                self.s_clientRearchUnitArray.remove(eachUnit)
                break

    pass


# 管理伙伴服务器单元队列
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_Mang_PeerSrv(CTYLB_Mang_BusisUnit_Base_bytes):
    s_g_iMaxEachSendBuffSize = 10000  # 每次发送缓冲最大大小10k

    def __init__(self, strMySrvName):
        CTYLB_Mang_BusisUnit_Base_bytes.__init__(self, strMySrvName)

    def __del__(self):
        pass

    @staticmethod
    def ShowLog(iWarnLevel, strMsg):
        CTYLB_Log.ShowLog(iWarnLevel, 'PeerSrvMang', strMsg)

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        newServerUnit = CTYLB_Sv_PeerSrvUnit(socketValue, iSockType, peerAddress)
        return newServerUnit

    # 管套接收数据调度
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, strRecvData_bytes):
        CTYLB_Mang_BusisUnit_Base_bytes._Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue,
                                                                   strRecvData_bytes)
        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol
        connSockThreadMang = mangClientUnivealParam.s_u_connSockThread

        peerSrvUnit = self.SearchUnitBySockValue(socketValue)
        if (not peerSrvUnit):
            iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock
        else:
            strLeftRecvData_bytes = strRecvData_bytes
            bOneSuccess = False  # 至少有一个成功
            while (strLeftRecvData_bytes):
                # 是accept对象
                if (peerSrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                    # 解包对方发送的post内容，如果正确，我回应 http结果
                    bExactResult, strFromUniqueSign, tyCmdV2Unit, strNotHandleBuff_bytes = \
                        CTYLB_PsvPsv_Trans_Real_BaseFunc.Analy_Each_Exact_CmdV2Unit_FromPacket(strLeftRecvData_bytes,
                                                                                               True)
                    if (bExactResult and tyCmdV2Unit):
                        bOneSuccess = True

                        bHaveContent = False if (tyCmdV2Unit.IsEmpty()) else True
                        peerSrvUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(False, bHaveContent)
                        # 命令正确吗？对方是主动连接，我们都是服务端。那么，
                        peerSrvUnit.TmpStore_Recv_CmdV2Pack(tyCmdV2Unit)

                        popSendCmdV2PackUnit = peerSrvUnit.Pop_Multi_SendAble_CmdV2Pack(
                            CTYLB_Sv_Mang_PeerSrv.s_g_iMaxEachSendBuffSize)
                        bHaveContent = True if (popSendCmdV2PackUnit) else False
                        peerSrvUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(True, bHaveContent)  # 设置最后发送接收时间
                        strReplyFullBuff_bytes = CTYLB_PsvPsv_Trans_Real_BaseFunc.Build_FullPacket_With_CmdV2Unit(
                            strFromUniqueSign, popSendCmdV2PackUnit, False)
                        # CTYLB_Log.ShowLog(0, 'recv-peer-srv', ' reply sign:same: %s size:%d' % (strFromUniqueSign, len(strReplyFullBuff)))
                        peerSrvUnit.Set_ExecSendAction_Flag()
                        connSockThreadMang.SafePromptDataToSend(socketValue, strReplyFullBuff_bytes)
                    else:
                        if (strLeftRecvData_bytes):
                            CTYLB_Sv_Mang_PeerSrv.ShowLog(1, 'sock-analy-recv Error. data-len: %d' % (
                            len(strLeftRecvData_bytes)))
                # 是connect对象
                elif (peerSrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                    # 我已经发送了post内容，对方回应 http结果，此处进行分析解包
                    bExactResult, strReplyUniqueSign, tyCmdV2Unit, strNotHandleBuff_bytes = \
                        CTYLB_PsvPsv_Trans_Real_BaseFunc.Analy_Each_Exact_CmdV2Unit_FromPacket(strLeftRecvData_bytes,
                                                                                               False)
                    # CTYLB_Log.ShowLog(0, 'recv-peer-srv', '   connect-reply: sign:%s size:%d' % (strReplyUniqueSign, len(strLeftRecvData)))
                    if (bExactResult and tyCmdV2Unit):
                        peerSrvUnit.GiveBack_SessionUniqueSign(strReplyUniqueSign)  # 归还会话占用符
                        bOneSuccess = True
                        # 服务端向我发的 回应包
                        peerSrvUnit.TmpStore_Recv_CmdV2Pack(tyCmdV2Unit)
                        bHaveContent = False if (tyCmdV2Unit.IsEmpty()) else True
                        peerSrvUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(False, bHaveContent)
                    else:
                        if (strLeftRecvData_bytes):
                            CTYLB_Sv_Mang_PeerSrv.ShowLog(1, 'sock-analy-recv -connect, Error. data-len: %d' % (
                            len(strLeftRecvData_bytes)))
                else:
                    strNotHandleBuff_bytes = ''
                if (strNotHandleBuff_bytes):
                    CTYLB_Sv_Mang_PeerSrv.ShowLog(1, 'still not handle buff %d' % (len(strNotHandleBuff_bytes)))
                strLeftRecvData_bytes = strNotHandleBuff_bytes

            if (not bOneSuccess):  # 一个都没有成功?
                peerSrvUnit.SetDataFormatBadClose()
            else:
                if (peerSrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                    iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData
                elif (peerSrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                    iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply

            return iReplyCode

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False
        connSockThreadMang = mangClientUnivealParam.s_u_connSockThread

        for eachSrvUnit in self.s_mangUnitArray:
            # 是否主动连接？
            if (eachSrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 若无数据内容提交，主动发送握手包。可能服务端会有数据回应
                bCanExecSend, strTransUniqueSign = eachSrvUnit.Viul_GetNextSendResource(
                    CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxSvCtCheckSecond,
                    CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxBusyStillCheckTick)
                if (bCanExecSend):
                    popSendCmdV2PackUnit = None
                    if (strTransUniqueSign):
                        # self.ShowLog( 1, 'unique session is full 2. wait free more')
                        popSendCmdV2PackUnit = eachSrvUnit.Pop_Multi_SendAble_CmdV2Pack(
                            CTYLB_Sv_Mang_PeerSrv.s_g_iMaxEachSendBuffSize)
                    else:
                        pass
                    bRetValue = True
                    # 构建内容包，进行发送
                    bHaveContent = True if (popSendCmdV2PackUnit) else False
                    eachSrvUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(True, bHaveContent)  # 设置最后发送时间
                    strSendPacket_bytes = CTYLB_PsvPsv_Trans_Real_BaseFunc.Build_FullPacket_With_CmdV2Unit(
                        strTransUniqueSign, popSendCmdV2PackUnit, True)
                    eachSrvUnit.Set_ExecSendAction_Flag()
                    connSockThreadMang.SafePromptDataToSend(eachSrvUnit.s_destSockValue, strSendPacket_bytes)
                    pass
            # 如果是被动连接，是否长时间无内容接收，如果是，则关闭
            elif (eachSrvUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                if (eachSrvUnit.Is_LastSend_IdleTime_LargeThan(
                        CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxWaitComuInvalidIdleSecond)):
                    eachSrvUnit.SetDataFormatBadClose()
                pass
        return bRetValue

    # 获得可到达的客户端单元
    # start by sk. 170203
    def Get_PeerSrv_RearchClientUnit_ByName(self, strClientName):
        retClientUnit = None
        retPeerSrvUnit = None
        for eachPeerSrv in self.s_mangUnitArray:
            clientUnit = eachPeerSrv.GetRearchClientUnitByName(strClientName)
            if (clientUnit):
                retClientUnit = clientUnit
                retPeerSrvUnit = eachPeerSrv
                break
        return retPeerSrvUnit, retClientUnit

    pass

    # 获得可到达的客户端单元
    # start by sk. 170203
    def SearchSrvUnitByName(self, strPeerSrvName):
        retPeerSrvUnit = None
        for eachPeerSrv in self.s_mangUnitArray:
            if (eachPeerSrv.s_strUnitName == strPeerSrvName):
                retPeerSrvUnit = eachPeerSrv
                break
        return retPeerSrvUnit

    pass


# 管理远端客户端单元队列
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Sv_Mang_RemoteClient(CTYLB_Mang_BusisUnit_Base_bytes):
    # s_storRecvContentArray = []   # 存储接收到的内容队列 CTYLB_Trans_NeedExec_RecvContentUnit

    def __init__(self, strMySrvName):
        CTYLB_Mang_BusisUnit_Base_bytes.__init__(self, strMySrvName)
        self.s_storRecvContentArray = []  # 存储接收到的内容队列 CTYLB_Trans_NeedExec_RecvContentUnit

    def __del__(self):
        pass

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        newServerUnit = CTYLB_Sv_ClientUnit(socketValue, iSockType, peerAddress)
        return newServerUnit

    # 管套接收数据调度
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, strRecvData_bytes):
        CTYLB_Mang_BusisUnit_Base_bytes._Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue,
                                                                   strRecvData_bytes)
        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol
        connSockThreadMang = mangClientUnivealParam.s_u_connSockThread

        remoteClientUnit = self.SearchUnitBySockValue(socketValue)
        if (not remoteClientUnit):
            iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock
        else:
            bAtLeastOneSucc = False
            strNotHandleBuff_bytes = strRecvData_bytes

            while (strNotHandleBuff_bytes):
                strValidNextBuff_bytes = strNotHandleBuff_bytes
                strNotHandleBuff_bytes = b''
                # 是accept对象
                if (remoteClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                    # 解包对方发送的post内容，如果正确，我回应 http结果
                    bExactResult, strFromUniqueIndex, tyCmdUnit, strFromUser, strDestUser, buildTime, strNotHandleBuff_bytes = \
                        CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket(strValidNextBuff_bytes, True)
                    if (bExactResult and tyCmdUnit):
                        bAtLeastOneSucc = True
                        bShowLog = False

                        bPacketEmptyContentSet = False
                        if (tyCmdUnit.IsCmdUnitEmpty()):
                            bPacketEmptyContentSet = True
                        # 命令正确吗？对方是主动连接，对方是客户端，我是服务端。那么，
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_5_Connect_SendCheck):
                            bShowLog = True
                            if (tyCmdUnit.s_iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_DirectSrvExec):
                                bShowLog = False
                            elif (tyCmdUnit.s_iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_CtSv_SvCt_SvSv_Empty):
                                bShowLog = False
                                bPacketEmptyContentSet = False
                            elif (
                                (tyCmdUnit.s_iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_Db_Session_Trans) or
                                (
                                    tyCmdUnit.s_iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans)):
                                if (len(tyCmdUnit.s_strContent) == 0):
                                    # 是检测包，并且没有内容，那么，不需要设置最后发送时间
                                    bShowLog = False
                                    bPacketEmptyContentSet = False

                            iReplyMainCmd = CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_6_Reply_SendCheck
                        elif (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_1_ReportName):
                            bShowLog = True
                            iReplyMainCmd = CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_2_ReplySrvName
                        elif (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_CtSv_0_Pass):
                            iReplyMainCmd = 0
                            pass
                        else:
                            bShowLog = True
                            iReplyMainCmd = CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_2_ReplySrvName

                        remoteClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(False, not bPacketEmptyContentSet)

                        if (bShowLog):
                            strMsg = u'recv:[%s],[%s->%s] cmd:%d-%d len(%d)' % (remoteClientUnit.s_strUnitName,
                                                                                strFromUser, strDestUser,
                                                                                tyCmdUnit.s_iMainCmd,
                                                                                tyCmdUnit.s_iSubCmd,
                                                                                len(tyCmdUnit.s_strContent))
                            CTYLB_Sv_Mang_RemoteClient.ShowLog(0, strMsg)

                        self.TmpStore_RecvContent(remoteClientUnit.s_strUnitName, strDestUser,
                                                  tyCmdUnit.s_iSubCmd,
                                                  tyCmdUnit.s_strContent)
                        strPacketFromtUser, strPacketDestUser, iPackSubCmd, strPacketContentBuff = \
                            remoteClientUnit.Pop_GetNext_SendablePacket()
                        # 有内容进行发送。
                        bHaveContent = True if (len(strPacketContentBuff) > 0) else False
                        remoteClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(True, bHaveContent)
                        # 我构建汇报包进行发送
                        strReplyContent_bytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                            strFromUniqueIndex, iReplyMainCmd, iPackSubCmd, strPacketFromtUser,
                            strPacketDestUser, strPacketContentBuff, False)

                        remoteClientUnit.Set_ExecSendAction_Flag()
                        connSockThreadMang.SafePromptDataToSend(socketValue, strReplyContent_bytes)
                    else:
                        if (strValidNextBuff_bytes):
                            CTYLB_Sv_Mang_RemoteClient.ShowLog(1, 'Sock_Recv_Data Error. data-len: %d' % (
                            len(strValidNextBuff_bytes)))

                # 是connect对象
                elif (remoteClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                    # 我已经发送了post内容，对方回应 http结果，此处进行分析解包
                    bExactResult, strReplyTransUniqueSign, tyCmdUnit, strFromUser, strDestUser, \
                        buildTime, strNotHandleBuff_bytes = CTYLB_Mang_BusisUnit_Base_bytes.AnalySingleExactCmdUnitFromPacket(
                        strValidNextBuff_bytes, False)
                    if (bExactResult and tyCmdUnit):
                        remoteClientUnit.GiveBack_SessionUniqueSign(strReplyTransUniqueSign)  # 归还释放会话占用标识符
                        # 设置接收新的时间
                        bHaveContent = False if (tyCmdUnit.IsCmdUnitEmpty()) else True
                        remoteClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(False, bHaveContent)
                        bAtLeastOneSucc = True
                        # 服务端向我发的 回应包
                        if (tyCmdUnit.s_iMainCmd == CT2P_SHand_Ct_Srv.s_iMnCmd_Ct_Sv_12_Reply_SendCheck):
                            self.TmpStore_RecvContent(strFromUser, strDestUser, tyCmdUnit.s_iSubCmd,
                                                      tyCmdUnit.s_strContent)
                    else:
                        if (strValidNextBuff_bytes):
                            CTYLB_Sv_Mang_RemoteClient.ShowLog(1, 'Sock_Recv_Data Error - connect. data-len: %d' % (
                            len(strValidNextBuff_bytes)))
                if (strNotHandleBuff_bytes):
                    CTYLB_Sv_Mang_PeerSrv.ShowLog(1, 'still not handle buff %d' % (len(strNotHandleBuff_bytes)))

            if (bAtLeastOneSucc):
                if (remoteClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                    iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData
                elif (remoteClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                    iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply
            else:
                remoteClientUnit.SetDataFormatBadClose()

        return iReplyCode

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False
        connSockThreadMang = mangClientUnivealParam.s_u_connSockThread

        for eachClientUnit in self.s_mangUnitArray:
            # 是否主动连接？
            if (eachClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Connect):
                # 若无数据内容提交，主动发送握手包。可能服务端会有数据回应
                bCanExecSend, strTransUniqueSign_bytes = eachClientUnit.Viul_GetNextSendResource(
                    CTYLB_Mang_BusisUnit_Base_bytes.s_iMaxSvCtCheckSecond,
                    CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxBusyStillCheckTick)
                if (bCanExecSend):
                    strPacketFromtUser, strPacketDestUser, iPackSubCmd, strPacketContentBuff_bytes = '', '', 0, b''
                    if (strTransUniqueSign_bytes):
                        strPacketFromtUser, strPacketDestUser, iPackSubCmd, strPacketContentBuff_bytes = \
                            eachClientUnit.Pop_GetNext_SendablePacket()
                    else:
                        pass
                    bHaveContent = True if (strPacketContentBuff_bytes) else False
                    eachClientUnit.Set_LastNetContent_ActionTime_HaveOrEmpty(True, bHaveContent)  # 设置最后发送时间

                    strTransUniqueSign_bytes = CTYLB_Mang_BusisUnit_Base_bytes.GenerateUniqueKeyStr()
                    # 构建内容包，进行发送
                    strSendPacket_bytes = CTYLB_Mang_BusisUnit_Base_bytes.BuildFullPacketWithCmdUnit(
                        strTransUniqueSign_bytes,
                        CT2P_SHand_Ct_Srv.s_iMnCmd_Sv_Ct_7_Connect_SendCheck, iPackSubCmd, strPacketFromtUser,
                        strPacketDestUser, strPacketContentBuff_bytes, True)
                    eachClientUnit.Set_ExecSendAction_Flag()
                    connSockThreadMang.SafePromptDataToSend(eachClientUnit.s_destSockValue, strSendPacket_bytes)
                    bRetValue = True
                    pass
            # 如果是被动连接，是否长时间无内容接收，如果是，则关闭
            elif (eachClientUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept):
                if (eachClientUnit.Is_LastSend_IdleTime_LargeThan(
                        CTYLB_Mang_BusisUnit_Base_bytes.s_g_iMaxWaitComuInvalidIdleSecond)):
                    eachClientUnit.SetDataFormatBadClose()
                pass

        return bRetValue

    # 存储接收到待处理的数据包
    # start by sk. 170130
    def TmpStore_RecvContent(self, strFromName_bytes, strToUser, iSubCmd, strContent=''):
        newRecvUnit = CTYLB_Trans_NeedExec_RecvContentUnit(strFromName_bytes, strToUser, iSubCmd,
                                                           strContent)
        self.s_storRecvContentArray.append(newRecvUnit)

    # 获得客户端名字列表
    # start by sk. 170130
    def GetClientNameArray(self):
        strRetClientNameArray = []
        for eachClientUnit in self.s_mangUnitArray:
            strAppend = eachClientUnit.s_strUnitName if(eachClientUnit.s_strUnitName) else ''
            strRetClientNameArray.append(strAppend)
        return strRetClientNameArray

    # 获得客户端名字列表
    # start by sk. 170130
    def GetUnit_By_ClientName(self, strClientName):
        retClientUnit = None
        for eachClientUnit in self.s_mangUnitArray:
            if (eachClientUnit.s_strUnitName == strClientName):
                retClientUnit = eachClientUnit
                break
        return retClientUnit

    # 取出待处理的数据包
    def Pop_Need_Handle_RecvContent(self):
        bRetHaveContain = False  # 返回无内容
        strRetFromUser, strRetToUser= '', ''
        iRetSubCmd = 0
        strRetContent = ''
        if (self.s_storRecvContentArray):
            bRetHaveContain = True
            storeUnit = self.s_storRecvContentArray.pop(0)
            strRetFromUser = storeUnit.s_strFromUser
            strRetToUser = storeUnit.s_strToUser
            iRetSubCmd = storeUnit.s_iSubCmd
            strRetContent = storeUnit.s_strContent
        return bRetHaveContain, strRetFromUser, strRetToUser, iRetSubCmd, strRetContent

    @staticmethod
    def ShowLog(iWarnLevel, strMsg):
        CTYLB_Log.ShowLog(iWarnLevel, 'ClientMang', strMsg)


# 主Peer-Server执行运行类
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Peer_Server:
    s_sendWaitDiffSecond = 5

    def __init__(self, strRegFile):
        self.s_acceptConnectSockThread = None
        self.s_initiactiveConnectSockThread = None

        self.s_peerServerConfig = CTYLB_PeerServer_Config()
        self.s_peerServerConfig.ReadFromConfigFile(strRegFile)
        self.s_MyGlobalQueue = queue.Queue()

        self.s_acceptPeerSrvConnectSockMang = CTCPAcceptConnectMangClient_bytes(self.s_MyGlobalQueue)  # 伙伴服务器连接管套管理执行
        self.s_acceptClientConnectSockMang = CTCPAcceptConnectMangClient_bytes(self.s_MyGlobalQueue)  # 客户端接收连接管理执行
        self.s_execConnectPeerSrvSockMang = CExecConnectSockMang_bytes(
            self.s_peerServerConfig.s_strPeerSrvAddrArray)  # 执行连接远端服务器管理
        self.s_execConnectClientSockMang = CExecConnectSockMang_bytes(
            self.s_peerServerConfig.s_strInitConnectClientAddrArray)  # 执行连接客户端管理

        if (self.s_peerServerConfig.s_iClientSrvListenPort > 0):
            self.s_execListenClientSockThread = CTCPListenSock(self.s_peerServerConfig.s_iClientSrvListenPort,
                                                               self.s_MyGlobalQueue)  # 客户端监听
        else:
            self.s_execListenClientSockThread = None

        if (self.s_peerServerConfig.s_iWaitPeerSrvConnectPort):
            self.s_execListenPeerSockThread = CTCPListenSock(self.s_peerServerConfig.s_iWaitPeerSrvConnectPort,
                                                             self.s_MyGlobalQueue)  # 服务端监听
        else:
            self.s_execListenPeerSockThread = None

        self.s_needIdentifyClientMang = CTYLB_Sv_Mang_Client_NeedIdentify(
            self.s_peerServerConfig.s_strMyID)  # 需要握手的远程客户端单元管理
        self.s_needIdentifyPeerSrvMang = CTYLB_Sv_Mang_PeerSrv_NeedIdentify(
            self.s_peerServerConfig.s_strMyID)  # 需要握手的远程服务端单元管理
        self.s_clientUnitMang = CTYLB_Sv_Mang_RemoteClient(self.s_peerServerConfig.s_strMyID)  # 经过验证的客户端对象管理
        self.s_peerSrvUnitMang = CTYLB_Sv_Mang_PeerSrv(self.s_peerServerConfig.s_strMyID)  # 经过验证的服务端对象管理

        self.s_needCloseSockValueArray = []
        self.s_lastSendTime = datetime.now()

        pass

    # Service run main.
    # start by sk. 170116
    def run(self, strProgName, funcIsGlobalExit):
        global g_bSysRunning

        CTYLB_Peer_Server.ShowLog(0, "[%s] Starting..." % (strProgName))
        # start listen port
        if (self.s_execListenClientSockThread):
            self.s_execListenClientSockThread.Start()
        if (self.s_execListenPeerSockThread):
            self.s_execListenPeerSockThread.Start()

        self.s_acceptPeerSrvConnectSockMang.Start()  # 伙伴服务器连接管套管理执行
        self.s_acceptClientConnectSockMang.Start()  # 客户端接收连接管理执行
        self.s_execConnectPeerSrvSockMang = CExecConnectSockMang_bytes(
            self.s_peerServerConfig.s_strPeerSrvAddrArray)  # 执行连接远端服务器管理
        self.s_execConnectClientSockMang = CExecConnectSockMang_bytes(
            self.s_peerServerConfig.s_strInitConnectClientAddrArray)  # 执行连接客户端管理

        # start connect to remote server.

        # check client connection
        # check need send packet
        # check recv packet
        # close server thread

        iMaxLoopCount = 1000
        iFreeCount = 0
        while (not funcIsGlobalExit()):
            bTaskBusy = False

            # 对网络功能，进行维护调用
            bExecMaintanceValue = self.__Maintance_Exec_BusinessType_NetworkSocket(self.s_execListenClientSockThread,
                                                                                   self.s_execConnectClientSockMang,
                                                                                   self.s_acceptClientConnectSockMang,
                                                                                   self.s_needIdentifyClientMang,
                                                                                   self.s_clientUnitMang)
            if (bExecMaintanceValue):
                bTaskBusy = True

            # 对网络功能，进行维护调用
            bExecMaintanceValue = self.__Maintance_Exec_BusinessType_NetworkSocket(self.s_execListenPeerSockThread,
                                                                                   self.s_execConnectPeerSrvSockMang,
                                                                                   self.s_acceptPeerSrvConnectSockMang,
                                                                                   self.s_needIdentifyPeerSrvMang,
                                                                                   self.s_peerSrvUnitMang)
            if (bExecMaintanceValue):
                bTaskBusy = True

            if (self.__ExecMainTanceNetUnitFunc()):
                bTaskBusy = True

            # 广播消息，测试，调试
            if (self.__RandomBroadCastMsgToAll_Peer_Client()):
                bTaskBusy = True

            # 处理消息内容相关
            iCurLoop = 0
            while (iCurLoop < iMaxLoopCount):
                iCurLoop += 1
                if (self.__Check_Handle_ClientMang_RecvMsg_Content()):
                    bTaskBusy = True
                else:
                    break

            iCurLoop = 0
            while (iCurLoop < iMaxLoopCount):
                iCurLoop += 1
                if (self.__Check_Exec_PeerSrvMang_ClientMang_RecvCmdV2Packet_Func()):
                    bTaskBusy = True
                else:
                    break

            # 等待休眠
            if (not bTaskBusy):
                iFreeCount += 1
                if iFreeCount > g_iMaxExecIdleCount:
                    time.sleep(0.01)
            else:
                iFreeCount = 0

        # 关闭，停止监听，关闭管套
        if (self.s_execListenClientSockThread):
            self.s_execListenClientSockThread.Stop()
        if (self.s_execListenPeerSockThread):
            self.s_execListenPeerSockThread.Stop()

        self.s_acceptPeerSrvConnectSockMang.Stop()  # 伙伴服务器连接管套管理执行
        self.s_acceptClientConnectSockMang.Stop()  # 客户端接收连接管理执行

        # wait all queue task exit.
        self.s_MyGlobalQueue.join()
        pass

    # 执行维护网络单元功能
    # start by sk. 170130
    def __ExecMainTanceNetUnitFunc(self):
        bRetValue = False
        # 对辨别客户端的网络单元，进行维护检查
        if (self.s_needIdentifyClientMang._Viul_TimerCheckSockSendPacket(None)):
            bRetValue = True
        # 对服务端的网络单元，进行维护检查
        if (self.s_needIdentifyPeerSrvMang._Viul_TimerCheckSockSendPacket(None)):
            bRetValue = True

        # 有出错被主动关闭的客户端？
        beenPeerClosedUnit = self.s_needIdentifyClientMang.Pop_ClosedByPeer_Unit()
        if (beenPeerClosedUnit):
            self.s_needCloseSockValueArray.append(beenPeerClosedUnit.s_destSockValue)
        # 有出错被主动关闭的服务端？
        beenPeerClosedUnit = self.s_needIdentifyPeerSrvMang.Pop_ClosedByPeer_Unit()
        if (beenPeerClosedUnit):
            self.s_needCloseSockValueArray.append(beenPeerClosedUnit.s_destSockValue)
        # 有出错被主动关闭的正式客户端？
        beenPeerClosedUnit = self.s_clientUnitMang.Pop_ClosedByError_Unit()
        if (beenPeerClosedUnit):
            self.s_needCloseSockValueArray.append(beenPeerClosedUnit.s_destSockValue)
        # 有出错被主动关闭的正式服务端？
        beenPeerClosedUnit = self.s_peerSrvUnitMang.Pop_ClosedByError_Unit()
        if (beenPeerClosedUnit):
            self.s_needCloseSockValueArray.append(beenPeerClosedUnit.s_destSockValue)

        # 对客户端的单元，进行维护检查
        mangClientUnivealParam = CTYLB_Global_UnivTrans_Param(None, None, None, None,
                                                              self.s_acceptClientConnectSockMang.s_myExecConnectSocketThread)
        if (self.s_clientUnitMang._Viul_TimerCheckSockSendPacket(mangClientUnivealParam)):
            bRetValue = True
        # 对服务端的单元，进行维护检查
        mangClientUnivealParam = CTYLB_Global_UnivTrans_Param(None, None, None, None,
                                                              self.s_acceptPeerSrvConnectSockMang.s_myExecConnectSocketThread)
        if (self.s_peerSrvUnitMang._Viul_TimerCheckSockSendPacket(mangClientUnivealParam)):
            bRetValue = True

        # 对于出错关闭的管套，从各个队列中移除
        for eachSockValue in self.s_needCloseSockValueArray:
            # 在执行连接的服务器中处理
            self.s_execConnectPeerSrvSockMang.DestSockClosed(eachSockValue)
            self.s_execConnectClientSockMang.DestSockClosed(eachSockValue)
            # 在应用辨别单元队列中检查
            self.s_needIdentifyClientMang.ExecHandleSockClose(eachSockValue)
            self.s_needIdentifyPeerSrvMang.ExecHandleSockClose(eachSockValue)
            # 在服务器管理队列中检查
            self.s_clientUnitMang.ExecHandleSockClose(eachSockValue)
            self.s_peerSrvUnitMang.ExecHandleSockClose(eachSockValue)
            # 在接收的监听连接队列中检查
            self.s_acceptClientConnectSockMang.s_myExecConnectSocketThread.CloseExecSocket(eachSockValue)
            self.s_acceptPeerSrvConnectSockMang.s_myExecConnectSocketThread.CloseExecSocket(eachSockValue)
        self.s_needCloseSockValueArray = []

        return bRetValue

    # 处理消息内容
    # start by sk. 170130
    def __Check_Handle_ClientMang_RecvMsg_Content(self):
        bRetValue = False
        bHaveContain, strFromUser, strToUser, iSubCmd, strContent = self.s_clientUnitMang.Pop_Need_Handle_RecvContent()
        if (bHaveContain):
            # 调整，修正服务端子命令，传到客户端的子命令中。要注意： CTYLB_PsvPsv_BaseCmd 的子命令定义，与 CTYLB_SvClt_Cmd_Base 的 子命令定义，不能冲突
            if (iSubCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_DataTrans):
                iSubCmd = CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_Db_Session_Trans
            elif (iSubCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_MidBanance_DataTrans):
                iSubCmd = CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans

            bRetValue = True
            if (iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_DirectSrvExec):
                self.__HandleRecvClientMsg_DirectSrvExec(strFromUser, strToUser, iSubCmd, strContent)
                pass
            elif (iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_Ct_Ct_ChatText):
                if (len(strToUser) > 0):
                    busisPackArray = CTYLB_Comb_PackArray.ExactCombindData(strContent)
                    for eachBusisPack in busisPackArray:
                        if (eachBusisPack.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_Ct_Ct_ChatText):
                            destClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(strToUser)
                            destClientUnit.Prompt_ReTransable_Pack_ToBe_Send(strFromUser,
                                                                             eachBusisPack.s_iBusiCmdID,
                                                                             eachBusisPack.s_strContent)
                            pass
                        else:
                            strMsg = 'unknown recv pack type: [%s->%s %d len(%d)]' % (
                                strFromUser, strToUser, eachBusisPack.s_iBusiCmdID,
                                len(eachBusisPack.s_strContent))
                            CTYLB_Peer_Server.ShowLog(1, strMsg)
                pass

            elif ((iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_Db_Session_Trans) or
                      (iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans)):
                destClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(strToUser)
                if (destClientUnit):
                    destClientUnit.Prompt_ReTransable_Pack_ToBe_Send(strFromUser, iSubCmd, strContent)
                else:
                    # 不在当前直接连接的客户端对象中，转发到服务端节点中，找对象进行传递。
                    if (len(strToUser) == 0):
                        # no dest user, what content?
                        pass
                    else:
                        peerSrvUnit, rearchClientUnit = self.s_peerSrvUnitMang.Get_PeerSrv_RearchClientUnit_ByName(
                            strToUser)
                        if (peerSrvUnit and rearchClientUnit):
                            peerSrvUnit.Prompt_RecvClientPacket_ToBe_StoreSend(self.s_peerServerConfig.s_strMyID,
                                                                               strFromUser, strToUser,
                                                                               iSubCmd, strContent)
                        else:
                            if (len(strContent) == 0):
                                # only cmd?
                                pass
                            else:
                                CTYLB_Peer_Server.ShowLog(
                                    1, 'not x know where :%s->%s [%d] len:%d' % (
                                        strFromUser, strToUser, iSubCmd, len( strContent)))

            elif (iSubCmd == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_CtSv_SvCt_SvSv_Empty):
                pass
            else:
                strMsg = 'unknown sub cmd:%d [%s->%s len:(%d)]' % (
                iSubCmd, strFromUser, strToUser, len(strContent))
                CTYLB_Peer_Server.ShowLog(1, strMsg)
        return bRetValue

    # 处理接收到的客户端消息 － 服务端直接执行命令
    # start by sk. 170218
    def __HandleRecvClientMsg_DirectSrvExec(self, strFromUser, strToUser, iSubCmd, strContent):
        busisPackArray = CTYLB_Comb_PackArray.ExactCombindData(strContent)
        for eachBusisPack in busisPackArray:
            if (eachBusisPack.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Sv_RequestRearchAbleClientList):
                strClientNameArray = self.s_clientUnitMang.GetClientNameArray()
                strSendContent = CTYLB_SvClt_Cmd_Base_bytes.Comb_MultiClientNameList_Packet(strClientNameArray)
                curClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(strFromUser)
                if (curClientUnit):
                    curClientUnit.Prompt_Srv_DirectSend_Pack_ToBe_Send(strToUser,
                                                                       CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Sv_Ct_RequestRearchAbleClientList_Reply,
                                                                       strSendContent)
                else:
                    CTYLB_Peer_Server.ShowLog(1, 'client %s not exist' % (strFromUser))
            elif (eachBusisPack.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_Ct_Ct_ChatText):
                destClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(strToUser)
                destClientUnit.Prompt_ReTransable_Pack_ToBe_Send(strFromUser, eachBusisPack.s_iBusiCmdID,
                                                                 eachBusisPack.s_strContent)
                pass
            elif (eachBusisPack.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_BCast_OnLine):
                # 给所有客户端发送通知消息，取最新的数据。
                for eachClientUnit in self.s_clientUnitMang.s_mangUnitArray:
                    if (eachClientUnit.s_strUnitName == strFromUser):
                        pass
                    else:
                        # 判断权限，可否广播到客户端，或者控制台
                        bSendUserOnlineMsgToClient = CTYLB_Psv_PrivRight_Check.IsUserNameCanSendBcast(
                            eachClientUnit.s_strUnitName, eachClientUnit.s_strUnitName)
                        if (bSendUserOnlineMsgToClient):
                            self.s_clientUnitMang.TmpStore_RecvContent(strFromUser, eachClientUnit.s_strUnitName, iSubCmd)
                # 给所有服务端发送消息，向前广播我在线
                # 构造单元，第一个经过本服务器路径，然后向前发送广播
                if (len(self.s_peerSrvUnitMang.s_mangUnitArray) > 0):
                    for eachSrvUnit in self.s_peerSrvUnitMang.s_mangUnitArray:
                        newBCastsOnlineUnit = CTY_CmdV2PackUnit()
                        newBCastsOnlineUnit.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_SvSv_DataTrans,
                                                      CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_BCast_ClientOnLine)
                        newBCastsOnlineUnit.SetSrcDstUserID(strFromUser, '')
                        newBCastsOnlineUnit.s_midPathUnit.AddAppendToFromPath(self.s_peerServerConfig.s_strMyID)
                        eachSrvUnit.TmpStore_NeedWaitSend_CmdV2Pack(newBCastsOnlineUnit)
                    pass
            elif (
                eachBusisPack.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Ct_Sv_RequestNeedRearchClientList):
                strNeedClientNameArray = CTYLB_SvClt_Cmd_Base_bytes.Exact_MultiClientNameList_Packet(
                    eachBusisPack.s_strContent)
                curFromClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(strFromUser)
                if (curFromClientUnit):
                    # 每个单元查找。
                    for eachStrNeedClientName in strNeedClientNameArray:
                        destClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(eachStrNeedClientName)
                        bCurClientOnLine = False
                        if (destClientUnit):
                            bCurClientOnLine = True
                        else:
                            peerSrvUnit, destPeerSrvClientUnit = self.s_peerSrvUnitMang.Get_PeerSrv_RearchClientUnit_ByName(
                                eachStrNeedClientName)
                            if (peerSrvUnit and destPeerSrvClientUnit):
                                bCurClientOnLine = True
                        if (bCurClientOnLine):
                            curFromClientUnit.Prompt_Srv_DirectSend_Pack_ToBe_Send(strToUser,
                                                                                   CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_Sv_Ct_RequestNeedRearchClientList_Reply,
                                                                                   eachStrNeedClientName)
                else:
                    CTYLB_Peer_Server.ShowLog(1, 'client %s not exist, unit eerror' % (strFromUser))
                pass
            else:
                strMsg = 'unknown recv pack type: [%s->%s %d len(%d)]' % (
                    strFromUser, strToUser, eachBusisPack.s_iBusiCmdID,
                    len(eachBusisPack.s_strContent))
                CTYLB_Peer_Server.ShowLog(1, strMsg)

    # 随机广播消息给各个客户端
    # start by sk. 170124
    def __RandomBroadCastMsgToAll_Peer_Client(self):
        bRetValue = False

        curTime = datetime.now()
        timeDiff = curTime - self.s_lastSendTime
        if (timeDiff.seconds > self.s_sendWaitDiffSecond):
            self.s_lastSendTime = curTime
            pass

        return bRetValue

    # 维护，执行，业务类型级别的 网络管套相关资源对象。Maintance exec network-socket function
    # start by sk. 170126
    def __Maintance_Exec_BusinessType_NetworkSocket(self, execListenThreadMang, execConnectSockMang, execAcceptSockMang,
                                                    execIdentifyMang, execHandOkUnitMang):
        bRetValue = False

        # 检查监听管套，新接收的管套  针对服务端
        if (execListenThreadMang):
            newUnitSock, newUnitAddr = execListenThreadMang.s_myListenThread.SafeGetNewClientConnec()
            if (newUnitSock):
                # 加入到连接管理队列
                execAcceptSockMang.s_myExecConnectSocketThread.AddClientSocket(newUnitSock, None)
                CTYLB_Peer_Server.ShowLog(0, 'New Connect Accept, From:%s' % (str(newUnitAddr)))
                bRetValue = True
                # 加入到应用辨别单元队列
                execIdentifyMang.NewSockUnitArrive(newUnitSock, True)

        # 对连接管理的管套，进行数据检查 针对服务端
        iMaxLoopCount = 1000
        iCurLoop = 0
        while (iCurLoop < iMaxLoopCount):
            iCurLoop += 1
            recvData_bytes, curExecSockUnit = execAcceptSockMang.s_myExecConnectSocketThread.SafePopRecvPacketUnit()
            if (recvData_bytes):
                mangClientUnivealParam = CTYLB_Global_UnivTrans_Param(None, None, None, None,
                                                                      execAcceptSockMang.s_myExecConnectSocketThread)
                # 把数据给辨别单元管理，进行处理
                iReplyCode = execIdentifyMang._Viul_HandleSockRecvPacket(mangClientUnivealParam,
                                                                         curExecSockUnit.s_mySocket, recvData_bytes)
                if (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply):
                    pass
                elif (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol):
                    self.s_needCloseSockValueArray.append(curExecSockUnit.s_mySocket)
                elif (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData):
                    pass
                elif (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock):
                    # 把数据交给服务器管理，进行处理
                    iReplyCode = execHandOkUnitMang._Viul_HandleSockRecvPacket(mangClientUnivealParam,
                                                                               curExecSockUnit.s_mySocket,
                                                                               recvData_bytes)
                    if (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_ProtocolOK_NotNeedReply):
                        pass
                    elif (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol):
                        self.s_needCloseSockValueArray.append(curExecSockUnit.s_mySocket)
                    elif (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_WebHTTP_Answner_CombedData):
                        pass
                    elif (iReplyCode == CTYLB_Ct_NetBase_bytes.s_iReply_NotMySock):
                        pass
                # 释放内存
                bRetValue = True

                # execIdentifyMang, execHandOkUnitMang):
                # 有成功完成辨别的客户端？
                finishIdentifyUnit = execIdentifyMang.Pop_Finish_Identify_Server()
                if (finishIdentifyUnit):
                    if (finishIdentifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_OK):
                        bIsAccept = True if (
                        finishIdentifyUnit.s_iSockType == CTYLB_Ct_NetBase_bytes.s_iSockType_Accept) else False
                        newSuccUnit = execHandOkUnitMang.NewSockUnitArrive(finishIdentifyUnit.s_destSockValue,
                                                                           bIsAccept)
                        strUnitName_bytes = finishIdentifyUnit.GetUnitName()
                        CTYLB_Peer_Server.ShowLog(0, '[%s] identify succ' % (strUnitName_bytes))
                        newSuccUnit.SetUnitName(strUnitName_bytes)
                        # update by sk. 170907. 新的同名单元上线，把旧单元挤下去
                        execHandOkUnitMang.UniqueUserOnlineAdjust(newSuccUnit)
                    elif (finishIdentifyUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_Fail):
                        # 关闭管套
                        self.s_needCloseSockValueArray.append(finishIdentifyUnit.s_destSockValue)
                    break
            else:
                # 直到处理完全部数据，没有数据可读取
                break

        # 检查是否有连接了的管套被关闭了。
        disconnectSocket = execAcceptSockMang.s_myExecConnectSocketThread.SafePopDisconnectClosedSocket()
        if (disconnectSocket):
            self.s_needCloseSockValueArray.append(disconnectSocket)

        # 对连接服务器端进行调度自动连接
        if (execConnectSockMang.TimerCheck_Auto_Connect()):
            bRetValue = True

        # 对连接成功的管套进行处理
        newConnectSockUnit = execConnectSockMang.GetLastSuccConnectSock()
        if (newConnectSockUnit):
            # 成功连接后，把单元加入到连接管套队列，进行管理
            execAcceptSockMang.s_myExecConnectSocketThread.AddClientSocket(newConnectSockUnit.s_execSocket,
                                                                           newConnectSockUnit.s_tmpSaveRecvBuffArray_bytes)
            newConnectSockUnit.SetSockMonitorByOtherThread()
            # 也把该管套，加入到应用辨别队列
            execIdentifyMang.NewSockUnitArrive(newConnectSockUnit.s_execSocket, False)
            bRetValue = True

        return bRetValue

    # 对客户端管理，和服务端管理，接收到的数据包，进行调度传输发送
    # start by sk. 170203
    def __Check_Exec_PeerSrvMang_ClientMang_RecvCmdV2Packet_Func(self):
        bRetValue = False

        # 每个服务端单元，下面的每个客户端单元进行检查
        for eachPeerSrvUnit in self.s_peerSrvUnitMang.s_mangUnitArray:
            toBeExecCmdV2PackUnit = eachPeerSrvUnit.Pop_RecvNeedExec_CmdV2Pack()
            if (toBeExecCmdV2PackUnit):
                self.__ExecRecvCmdV2PackUnit(eachPeerSrvUnit, toBeExecCmdV2PackUnit)
                bRetValue = True

        return bRetValue

    # 处理接收到的命令包
    # start by sk. 170203
    def __ExecRecvCmdV2PackUnit(self, peerSrvUnit, execCmdV2PackUnit):
        # 取出目标数据中，我本机的单元名字。因为已经到达了。
        strFirstDestHostName = execCmdV2PackUnit.s_midPathUnit.PopRetriveNextDestPath(False)
        if (strFirstDestHostName == self.s_peerServerConfig.s_strMyID):
            execCmdV2PackUnit.s_midPathUnit.PopRetriveNextDestPath()
        # 执行检查
        if (execCmdV2PackUnit.s_iMainSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_SvSv_DataTrans):
            if ((execCmdV2PackUnit.s_iSubSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_DataTrans) or
                    (execCmdV2PackUnit.s_iSubSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_MidBanance_DataTrans)):
                self.__Exec_Recv_CmdV2Pack_DataTrans(execCmdV2PackUnit.s_iSubSrvCmd, peerSrvUnit, execCmdV2PackUnit)
            elif (execCmdV2PackUnit.s_iSubSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_BCast_ClientOnLine):
                self.__Exec_Recv_CmdV2Pack_BCast_ClientOnLine(peerSrvUnit, execCmdV2PackUnit)
            elif (execCmdV2PackUnit.s_iSubSrvCmd == CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Dest_NotRearch):
                # 目标节点无法到达_目标用户名
                # 自身的服务器单元中，删除该节点
                peerSrvUnit.NotifyClientUnitOffLine(execCmdV2PackUnit.s_strDestUserID)
                # 不反向广播。可能该客户端其他路径会到达上面的其他节点。
                pass
            else:
                pass
        pass

    # 执行，接收到的服务端V2命令包－ 数据传输
    # start by sk. 170204
    def __Exec_Recv_CmdV2Pack_DataTrans(self, iOrigSubCmd, peerSrvUnit, execCmdV2PackUnit):
        # 更新来源用户的路径信息
        strFromUserPathArray = CTY_MidPath_PackUnit.ReversePathArray(
            execCmdV2PackUnit.s_midPathUnit.s_strOrigSrvSrvArray)
        peerSrvUnit.UpdateReachAbleClient(execCmdV2PackUnit.s_strSrcUserID, strFromUserPathArray)
        # 如果下个路径中，client节点存在，那么，提交发送，否则，自动重新找目标用户的路径
        # 取出下一个，但不删除。删除工作，由下个节点接收到后处理。
        strNextHostNode = execCmdV2PackUnit.s_midPathUnit.PopRetriveNextDestPath(False)
        if (len(strNextHostNode) == 0):  # 下一个节点不存在，在我的客户端单元中找。如果找到，投递给该单元，执行
            directClientUnit = self.s_clientUnitMang.GetUnit_By_ClientName(execCmdV2PackUnit.s_strDestUserID)
            if (directClientUnit):
                self.s_clientUnitMang.TmpStore_RecvContent(execCmdV2PackUnit.s_strSrcUserID,
                                                           execCmdV2PackUnit.s_strDestUserID,
                                                           iOrigSubCmd, execCmdV2PackUnit.s_strOrigTyCmdPack)
            else:
                # 客户端不存在，给上级服务器的服务端单元发送广播包，客户端下线了。其他服务端不发送。因为可能会还有其他路径存在
                strLastFromSrvName = execCmdV2PackUnit.s_midPathUnit.Get_LastSrvName_From_FromPath()
                lastFromSrvUnit = self.s_peerSrvUnitMang.SearchSrvUnitByName(strLastFromSrvName)
                if (lastFromSrvUnit):
                    newRevSendOfflineUnit = CTY_CmdV2PackUnit()
                    newRevSendOfflineUnit.SetSrvCmd(CTYLB_PsvPsv_BaseCmd.s_iPsv_MainCmd_SvSv_DataTrans,
                                                    CTYLB_PsvPsv_BaseCmd.s_iPsv_DTrans_SubCmd_Dest_NotRearch)
                    newRevSendOfflineUnit.SetSrcDstUserID(self.s_peerServerConfig.s_strMyID,
                                                          execCmdV2PackUnit.s_strDestUserID)
                    peerSrvUnit.TmpStore_NeedWaitSend_CmdV2Pack(newRevSendOfflineUnit)
                pass
        else:
            nextPeerSrvUnit = self.s_peerSrvUnitMang.SearchSrvUnitByName(strNextHostNode)
            if (nextPeerSrvUnit):
                # 找到了，下一个服务端节点，修改路径，投递
                execCmdV2PackUnit.s_midPathUnit.AddAppendToFromPath(self.s_peerServerConfig.s_strMyID)
                nextPeerSrvUnit.TmpStore_NeedWaitSend_CmdV2Pack(execCmdV2PackUnit)
        pass

    # 执行，接收到的服务端V2命令包－ 广播客户端上线消息
    # start by sk. 170204
    def __Exec_Recv_CmdV2Pack_BCast_ClientOnLine(self, peerSrvUnit, execCmdV2PackUnit):
        # 把本单元加入可达的客户端列表
        strFromUserPathArray = CTY_MidPath_PackUnit.ReversePathArray(
            execCmdV2PackUnit.s_midPathUnit.s_strOrigSrvSrvArray)
        peerSrvUnit.UpdateReachAbleClient(execCmdV2PackUnit.s_strSrcUserID, strFromUserPathArray)
        # 向我的客户端对象，广播客户端到达
        for eachClientUnit in self.s_clientUnitMang.s_mangUnitArray:
            strCurClientName = eachClientUnit.GetUnitName()
            if (strCurClientName == execCmdV2PackUnit.s_strSrcUserID):
                pass
            else:
                bSendUserOnlineMsgToClient = CTYLB_Psv_PrivRight_Check.IsUserNameCanSendBcast(
                    execCmdV2PackUnit.s_strSrcUserID,
                    strCurClientName)
                if (bSendUserOnlineMsgToClient):
                    self.s_clientUnitMang.TmpStore_RecvContent(execCmdV2PackUnit.s_strSrcUserID, strCurClientName,
                                                               CTYLB_SvClt_Cmd_Base_bytes.s_iPackCmd_SubCmd_BCast_OnLine)
            pass

        # 向前广播客户端上线_源用户名
        for eachSrvUnit in self.s_peerSrvUnitMang.s_mangUnitArray:
            # 找到所有节点，进行正向广播
            if (eachSrvUnit == peerSrvUnit):
                pass
            else:
                strCurSrvName = eachSrvUnit.s_strUnitName
                # 如果我在该节点的通过的列表内，那么，忽略
                if (strCurSrvName not in execCmdV2PackUnit.s_midPathUnit.s_strOrigSrvSrvArray):
                    newTransV2PackUnit = CTY_CmdV2PackUnit(execCmdV2PackUnit)
                    newTransV2PackUnit.s_midPathUnit.AddAppendToFromPath(self.s_peerServerConfig.s_strMyID)
                    eachSrvUnit.TmpStore_NeedWaitSend_CmdV2Pack(newTransV2PackUnit)
        pass

    @staticmethod
    def ShowLog(iWarnLevel, strMsg):
        CTYLB_Log.ShowLog(iWarnLevel, 'PS_MainRun', strMsg)
