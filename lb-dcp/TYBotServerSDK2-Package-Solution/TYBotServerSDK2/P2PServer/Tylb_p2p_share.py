# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_p2p_share.py p2p功能的基本共享文件
#
# start by sk. 170123
# update by sk. 170429, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# update to V3 by sk. 180314. 把各个结构内容，转成json的格式，尽量把各个bytes格式字符串，转成unicode操作

import zlib
import random
from datetime import datetime
import threading
import socket
import time
import base64
import yaml
import json
import requests
import traceback
import sys

g_chCmdPackSign = 'PWLFw2'  # 命令包的标志
# start by sk. 160502
g_strDataStartSign_bytes = '$#memat-dekl$#'.encode()
g_iMaxExecIdleCount = 50  # 最大的执行休眠次数

# 内存压缩操作类。
# start by sk. 160502
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTY_InMemoryZip:

    # 初始化
    # 生成随机文件名
    def __init__(self):
        pass

    def __del__(self):
        pass

    # 将内容压缩
    # 返回压缩结果数据
    def CompressData(self, strData):
        strData_bytes = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strData)
        result_bytes = zlib.compress( strData_bytes, zlib.Z_BEST_SPEED)  #  zlib.Z_BEST_SPEED
        return result_bytes

    # 将内容解压
    # 返回原始数据
    def DeCompressData(self, strZippedData_bytes):
        result_bytes = zlib.decompress( strZippedData_bytes)
        result_str = CTYLB_MainSys_MiscFunc.SafeGetUnicode(result_bytes)
        return result_str

# 日志信息显示
# start by sk. 170203
class CTYLB_Log:
    MonitorConsoleURL = "http://localhost:8889"
    MonitorURL = "http://localhost:8889"
    PostTimeout = 1
    MONITOR_TABLE_TYPE_UNMAN_STATUS = "status-table"
    MONITOR_TABLE_TYPE_UNMAN_BOT = "status-table-bot"
    MONITOR_TABLE_TYPE_UNMAN_BRAIN = "status-table-brain"

    @staticmethod
    def ShowLog(iWarnLevel, strRangeName, strMsg, iShowToMonitor=0):
        strTime = datetime.now().strftime('%m-%d %H:%M:%S')
        if (iWarnLevel == 0):
            strShowPrefix = '      '
        elif (iWarnLevel == 1):
            strShowPrefix = '   !Warning!  '
        elif (iWarnLevel == 2):
            strShowPrefix = '  !!!!Error!!!! '
        else:
            strShowPrefix = ' !!Unknown!! '

        strUnicodeRangeName = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRangeName)
        strUnicodeMsg = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strMsg)
        strShowTotalUnicode = '%s <%s> [%s] %s' % (strShowPrefix, strUnicodeRangeName, strTime, strUnicodeMsg)

        iStrLen = len(strShowTotalUnicode)
        iMaxShowLen = 130
        if (iStrLen < iMaxShowLen):
            strShowResult = strShowTotalUnicode
        else:
            iCutLen = iMaxShowLen
            for iIndex in range(iMaxShowLen, iStrLen):
                if (strShowTotalUnicode[iIndex] < 'z'):
                    iCutLen = iIndex
                    break
            strShowResult = strShowTotalUnicode[:iCutLen] + u'...'

        if (iShowToMonitor):
            CTYLB_Log.ShowMonitor(iShowToMonitor, iWarnLevel, strRangeName, strMsg)

        try:
            print(strShowResult)
        except Exception as e:
            print('      show log error on encoding...')
            pass

    # 将日志内容汇报到监控界面
    # Pxk  2017年3月28日11:41:45
    @staticmethod
    def ShowMonitorConsole(monitor_id, msg_level, msg_name, msg_content, use_long_time=False):
        strLongTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        strShortTime = datetime.now().strftime('%m-%d %H:%M:%S')
        msgData = {}
        msgData["monitor_id"] = monitor_id
        msgData["msg_level"] = msg_level
        msgData["msg_title"] = msg_name
        msgData["msg_content"] = msg_content
        msgData["short_time"] = strShortTime
        msgData["long_time"] = strLongTime
        msgData["use_long_time"] = use_long_time

        try:
            r = requests.post(url=CTYLB_Log.MonitorConsoleURL, json=msgData, timeout=CTYLB_Log.PostTimeout)
        except Exception as e:
            # print("[!]Error:Send monitor data failed:{}".format(e))
            pass

    @staticmethod
    def ShowMonitor(monitor_id, msg_level, msg_name, msg_content, use_long_time=False):
        strLongTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        strShortTime = datetime.now().strftime('%m-%d %H:%M:%S')
        msgData = {}
        msgData['type'] = 'status'
        msgData['data'] = {}
        msgData['data']["monitor_id"] = monitor_id
        msgData['data']["msg_level"] = msg_level
        msgData['data']["msg_title"] = msg_name
        msgData['data']["msg_content"] = msg_content
        msgData['data']["short_time"] = strShortTime
        msgData['data']["long_time"] = strLongTime
        msgData['data']["use_long_time"] = use_long_time

        try:
            dataStr = json.dumps(msgData).encode()
            base64Data = base64.b64encode(dataStr)
            r = requests.post(url=CTYLB_Log.MonitorURL, data=base64Data, timeout=CTYLB_Log.PostTimeout)
        except Exception as e:
            # print("[!]Error:Send monitor data failed:{}".format(e))
            pass

    @staticmethod
    def ShowMonitorTable(table_id, row, column, value, table_type=MONITOR_TABLE_TYPE_UNMAN_STATUS):
        msgData = {}
        msgData['type'] = table_type
        msgData['data'] = []
        table = {}
        table['id'] = table_id
        table['row'] = row
        table['col'] = column
        table['value'] = value
        msgData['data'].append(table)

        try:
            dataStr = json.dumps(msgData).encode()
            base64Data = base64.b64encode(dataStr)
            r = requests.post(url=CTYLB_Log.MonitorURL, data=base64Data, timeout=CTYLB_Log.PostTimeout)
        except Exception as e:
            # print("[!]Error:Send monitor data failed:{}".format(e))
            pass


# 命令单元，设置命令内容，获得命令内容
# start by sk. 160503
# update by sk. 170429. 支持 python3, 可输入字符串或者字节流
class CTY_CmdUnit:

    # 初始化
    def __init__(self, iMainCmd=0, iSubCmd=0, strContent=''):
        self.s_iMainCmd = 0    # 主命令
        self.s_iSubCmd = 0    # 子命令
        self.s_strContent = ''    # 内容
        self.SetContent(iMainCmd, iSubCmd, strContent)

    # 释放类对象
    def __del__(self):
        pass

    # 设置内容
    def SetContent(self, iMainCmd, iSubCmd, strContent):
        self.s_iMainCmd = iMainCmd    # 主命令
        self.s_iSubCmd = iSubCmd    # 子命令
        self.s_strContent = strContent    # 内容

    # 数据包是否为空
    # start by sk. 170216
    def IsCmdUnitEmpty(self):
        bRetValue = False
        if( not self.s_strContent):
            bRetValue = True
        return bRetValue


# 对命令进行封装和分解
# start by sk. 160502
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# update by sk. 180314. to json格式
# old name: CTY_CmdPack_bytes
class CTY_CmdPack_Json:
    g_ustrCmdPackTimeFormat = u'%Y-%m-%d_%H:%M:%S'
    # 初始化
    def __init__(self, strMyUserID=''):
        self.s_strMyUserID = ''
        self.SetMyUserID( strMyUserID)
        pass

    # 释放类对象
    def __del__(self):
        pass

    # 设置我的用户ID
    def SetMyUserID(self, strUserID):
        self.s_strMyUserID = strUserID

    # 判断这个用户ID是否我的
    def CheckIsUserIDMe(self, strCheckUserID):
        bRetValue = False
        if (self.s_strMyUserID == strCheckUserID):
            bRetValue = True
        return bRetValue

    g_strSign_strSign = 'str_sign'
    g_strSign_strMyUserID = 'str_myid'
    g_strSign_strDestUserID = 'str_destid'
    g_strSign_iMainCmd = 'i_maincmd'
    g_strSign_iSubCmd = 'i_subbcmd'
    g_strSign_strTime = 'str_time'
    g_strSign_strContent = 'str_content'
    # 获得组合数据包。
    # 数据格式：$# 标志$# 来自用户ID $# 目标用户ID $# 主命令 $# 子命令  $# 发送时间 $# 命令内容 $#
    # 返回值： strFormat, strBuffer --- 封装的数据格式，字符串缓冲数据
    def GetCombindData(self, strDestUserID, tyCmdUnit):
        exJsonDict = {}
        exJsonDict[CTY_CmdPack_Json.g_strSign_strSign] = g_chCmdPackSign
        exJsonDict[CTY_CmdPack_Json.g_strSign_strMyUserID] = self.s_strMyUserID
        exJsonDict[CTY_CmdPack_Json.g_strSign_strDestUserID] = strDestUserID
        exJsonDict[CTY_CmdPack_Json.g_strSign_iMainCmd] = tyCmdUnit.s_iMainCmd
        exJsonDict[CTY_CmdPack_Json.g_strSign_iSubCmd] = tyCmdUnit.s_iSubCmd

        curTime = datetime.now()
        exJsonDict[CTY_CmdPack_Json.g_strSign_strTime] = curTime.strftime(self.g_ustrCmdPackTimeFormat)
        exJsonDict[CTY_CmdPack_Json.g_strSign_strContent] = CTYLB_MainSys_MiscFunc.SafeGetUnicode(tyCmdUnit.s_strContent)

        strTotal = json.dumps(exJsonDict, ensure_ascii=False)
        return strTotal

    # 分解组合数据包
    # strFormat --- 数据格式
    # strBuffer --- 经过封装的缓冲内容
    # 返回值：bool, strFromUser, strDestUser, iMainCmd, iSubCmd, cmdBuildTime, strCmdContent
    def ExactCombindData(self, strBuffer):
        retTyCmdUnit = None  # 初始化返回值
        strFromUser = ''
        strDestUser = ''
        retBuildTime = datetime.now()

        try:
            origJsonDict = json.loads(strBuffer)

            strFromUser = origJsonDict[CTY_CmdPack_Json.g_strSign_strMyUserID]
            strDestUser = origJsonDict[CTY_CmdPack_Json.g_strSign_strDestUserID]
            iMainCmd = int(origJsonDict[CTY_CmdPack_Json.g_strSign_iMainCmd])
            iSubCmd = int(origJsonDict[CTY_CmdPack_Json.g_strSign_iSubCmd])

            retBuildTime = datetime.strptime(origJsonDict[CTY_CmdPack_Json.g_strSign_strTime], CTY_CmdPack_Json.g_ustrCmdPackTimeFormat)
            strCmdContent = origJsonDict[CTY_CmdPack_Json.g_strSign_strContent]

            if( origJsonDict[CTY_CmdPack_Json.g_strSign_strSign] == g_chCmdPackSign):
                retTyCmdUnit = CTY_CmdUnit(iMainCmd, iSubCmd, strCmdContent)
        except:
            pass

        return retTyCmdUnit, strFromUser, strDestUser, retBuildTime  # Web客户端数据包封装单元


# Web客户端数据包处理
# update to python3, by sk. 170429
# upgrade to V3. by sk. 修改输入输出内容为 str格式
class CTY_WebClientPacket:
    s_strContentLengthSign_bytes = b'Content-Length:'
    s_g_strUniqueIndexSign_bytes = b'Key:'
    s_strLineEnter_bytes = b'\r\n'
    s_g_strTwoLineEnter_bytes = b'\r\n\r\n'

    # 对数据包进行封装，提交进行压缩。作为Post协议的数据
    @staticmethod
    def Client_Data_To_SendPostPacket(strUniqueIndex, strOrigData):
        strSendHeader_bytes = b'xxxxxxxPOST /sample.Jsp HTTPSDFD/1.1\r\n' + \
                        b'Accept:image/gif.image/jpeg,*/*\r\n' + \
                        b'Accept-Language:en-us\r\n' + \
                        b'Connection:Keep-Alive\r\n' + \
                        b'Host:localhost\r\n' + \
                        b'User-Agent:Mozila/4.0(compatible;MSIE5.01;Window NT5.0)\r\n' + \
                        b'Accept-Encoding:gzip,deflate\r\n'

        strUniqueIndex_bytes = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strUniqueIndex)
        strUniqueIndexFrame_bytes = CTY_WebClientPacket.s_g_strUniqueIndexSign_bytes + strUniqueIndex_bytes + CTY_WebClientPacket.s_strLineEnter_bytes

        # 对内容进行压缩，打包
        inmemZip = CTY_InMemoryZip()
        strCompressData_bytes = inmemZip.CompressData(strOrigData)
        strBase64_bytes = base64.encodebytes( strCompressData_bytes)

        strLen_Bytes = str(len(strBase64_bytes)).encode()
        strActualContentLength_bytes = CTY_WebClientPacket.s_strContentLengthSign_bytes + strLen_Bytes + CTY_WebClientPacket.s_strLineEnter_bytes

        strRetData_bytes = strSendHeader_bytes + strActualContentLength_bytes + strUniqueIndexFrame_bytes + CTY_WebClientPacket.s_strLineEnter_bytes + strBase64_bytes
        return strRetData_bytes

    # 完整从队列中解压出web数据，数据队列中，可能存在错误的数据位置
    # start by sk. 170211
    @staticmethod
    def CompleteExactPopOneHttpSessionFromBuffArray( strRecvBuff_bytesArray):
        # 首先看web数据头是否正确
        strRetData_bytes = b''
        strNotHandleBuff_bytes = b''

        iRecvBuffArrayLength = len(strRecvBuff_bytesArray)
        iCurRetrivePos = 0   # 当前取出的数据位置
        iNeedPopDataPos = 0  # 需要弹出的数据位置
        strHandleAnalyPacket_bytes = b''
        bContinueHandleNextPacket = True if (iRecvBuffArrayLength > 0) else False
        while(bContinueHandleNextPacket):
            # 将当前数据缓冲放入要处理的分析包
            strNextPacket_bytes = strRecvBuff_bytesArray[iCurRetrivePos]
            iCurRetrivePos += 1
            strHandleAnalyPacket_bytes += strNextPacket_bytes

            # 判断当前分析包符合 数据头正确？
            iValidContentLength = CTY_WebClientPacket.__ExactGetContentLength( strHandleAnalyPacket_bytes)
            if( iValidContentLength > 0):
                # 其次看内容是否包含在content-length中
                iCurPacketLength = len( strHandleAnalyPacket_bytes)
                iContentPos = strHandleAnalyPacket_bytes.find( CTY_WebClientPacket.s_g_strTwoLineEnter_bytes)
                if( iContentPos > 0):
                    iContentPos += len( CTY_WebClientPacket.s_g_strTwoLineEnter_bytes)
                    iLeftNotHandlePos = iContentPos + iValidContentLength   # 剩下未处理的位置
                    if( iLeftNotHandlePos <= iCurPacketLength):
                        # 内容长度足够，可以输出了
                        strRetData_bytes = strHandleAnalyPacket_bytes[:iLeftNotHandlePos]
                        strNotHandleBuff_bytes = strHandleAnalyPacket_bytes[iLeftNotHandlePos:]
                        bContinueHandleNextPacket = False
                        iNeedPopDataPos = iCurRetrivePos
                        pass
            if( iCurRetrivePos >= iRecvBuffArrayLength):
                break

        if( iCurRetrivePos > 1):
            pass

        for iRemove in range(iNeedPopDataPos):
            strRecvBuff_bytesArray.pop(0)
        # 看是否还存在剩余下个数据包的数据，放入未取队列
        if( len(strNotHandleBuff_bytes) > 0):
            strRecvBuff_bytesArray.insert(0, strNotHandleBuff_bytes)

        return strRetData_bytes

    # 对接收到的数据包进行web解压
    # 如果包含多个 http包，则下个指针包含未处理缓冲
    @staticmethod
    def Srv_Exact_From_RecvPostPacket(strOrigRecvPacket_bytes):
        strRetData_bytes = b''
        strRetNotHandleNextPacket_bytes = b''

        strRecvPacket_bytes = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strOrigRecvPacket_bytes)

        strRetUniqueSign_bytes = CTY_WebClientPacket.__ExactGetUniqueSign( strRecvPacket_bytes)
        iValidContentLength = CTY_WebClientPacket.__ExactGetContentLength( strRecvPacket_bytes)
        iContentPos = strRecvPacket_bytes.find( CTY_WebClientPacket.s_g_strTwoLineEnter_bytes)
        if( iContentPos > 0):
            iContentPos += len(CTY_WebClientPacket.s_g_strTwoLineEnter_bytes)
            iLeftNotHandlePos = iContentPos + iValidContentLength   # 剩下未处理的位置
            strOrigBase64Data_bytes = strRecvPacket_bytes[ iContentPos:iLeftNotHandlePos]
            strRetNotHandleNextPacket_bytes = strRecvPacket_bytes[iLeftNotHandlePos:]

            inmemZip = CTY_InMemoryZip()
            try:
                strOrigCompress_bytes = base64.decodebytes( strOrigBase64Data_bytes)
                # 解压数据
                strRetData_bytes = inmemZip.DeCompressData(strOrigCompress_bytes)
            except Exception as e:
                strSampleData_bytes = strOrigBase64Data_bytes
                if( len(strSampleData_bytes) > 20):
                    strSampleData_bytes = strSampleData_bytes[:20]
                strSampleData = strSampleData_bytes.decode()
                CTYLB_Log.ShowLog(1, 'CmdPack_SrvEx', 'base64 or unzip error [%s], orig data len %d, sample:[%s]' % (str(e), len(strRecvPacket_bytes), strSampleData))

        strRetData = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRetData_bytes)
        strRetUniqueSign = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRetUniqueSign_bytes)
        return strRetData, strRetUniqueSign, strRetNotHandleNextPacket_bytes

    # 获得content-length后面的长度数据内容
    @staticmethod
    def __ExactGetContentLength(strPacket_bytes):
        iRetDataLength = 0

        iDataLengthPos = strPacket_bytes.find(CTY_WebClientPacket.s_strContentLengthSign_bytes)
        if (iDataLengthPos != -1):  # 查找标志字符串
            iDataLengthPos += len( CTY_WebClientPacket.s_strContentLengthSign_bytes)
            iLengthEndPos = strPacket_bytes.find( CTY_WebClientPacket.s_strLineEnter_bytes, iDataLengthPos, iDataLengthPos+10)
            if( iLengthEndPos != -1):
                strLength_bytes = strPacket_bytes[iDataLengthPos: iLengthEndPos]
                iRetDataLength = int(strLength_bytes)

        return iRetDataLength

    # 获得unique_id后面的字符串内容
    @staticmethod
    def __ExactGetUniqueSign(strPacket_bytes):
        strReqUniqueIndex = ''

        iUniqueSignPos = strPacket_bytes.find(CTY_WebClientPacket.s_g_strUniqueIndexSign_bytes)
        if (iUniqueSignPos != -1):  # 查找标志字符串
            iUniqueSignPos += len( CTY_WebClientPacket.s_g_strUniqueIndexSign_bytes)
            iUniqueEndPos = strPacket_bytes.find( CTY_WebClientPacket.s_strLineEnter_bytes, iUniqueSignPos, iUniqueSignPos+40)
            if( iUniqueEndPos != -1):
                strReqUniqueIndex = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPacket_bytes[iUniqueSignPos: iUniqueEndPos])

        return strReqUniqueIndex

    # 对数据包进行封装，作为Web http reply协议的数据
    @staticmethod
    def Srv_Data_To_WebReplyPacket(strUniqueIndex, strOrigData):
        strSendFormat_bytes = b'wfasdferasdfHTTP/1.1 23asdf200 werasdfOK\r\n' + \
                        b'Server:Apache Tomcat/5.0.12\r\n' + \
                        b'Date:Mon,6Oct2003 13:23:42 GMT\r\n'

        strUniqueIndex_bytes = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strUniqueIndex)
        strUniqueIndexFrame_bytes = CTY_WebClientPacket.s_g_strUniqueIndexSign_bytes + strUniqueIndex_bytes + CTY_WebClientPacket.s_strLineEnter_bytes
        # 压缩要发送的内容
        inmemZip = CTY_InMemoryZip()
        strCompressData_bytes = inmemZip.CompressData(strOrigData)
        strBase64_bytes = base64.encodebytes( strCompressData_bytes)

        strLenBase64_bytes = str(len(strBase64_bytes)).encode()
        strContentLengthFrame_bytes = CTY_WebClientPacket.s_strContentLengthSign_bytes + strLenBase64_bytes + CTY_WebClientPacket.s_strLineEnter_bytes

        strRetData_bytes = strSendFormat_bytes + strContentLengthFrame_bytes + strUniqueIndexFrame_bytes + CTY_WebClientPacket.s_strLineEnter_bytes + strBase64_bytes
        return strRetData_bytes

    # 客户端解压数据
    @staticmethod
    def Client_Exact_From_RecvWebReplyPacket(strRecvPacket):
        strRetData = ''
        strNotHandleContent_bytes = b''

        strRecvPacket_bytes = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strRecvPacket)

        strRetUniqueSign = CTY_WebClientPacket.__ExactGetUniqueSign( strRecvPacket_bytes)
        iValidContentLength = CTY_WebClientPacket.__ExactGetContentLength(strRecvPacket_bytes)
        if (iValidContentLength < 100000000):
            strTwoEnter_bytes = CTY_WebClientPacket.s_strLineEnter_bytes + CTY_WebClientPacket.s_strLineEnter_bytes
            iContentPos = strRecvPacket_bytes.find(strTwoEnter_bytes)
            if (iContentPos > 0):
                iContentPos += len(strTwoEnter_bytes)
                iNotHandleContentPos = iContentPos + iValidContentLength
                strOrigBase64Data_bytes = strRecvPacket_bytes[iContentPos:iNotHandleContentPos]
                strNotHandleContent_bytes = strRecvPacket_bytes[iNotHandleContentPos:]

                inmemZip = CTY_InMemoryZip()
                try:
                    strOrigCompress_bytes = base64.decodebytes(strOrigBase64Data_bytes)
                    # 解压数据
                    strRetData_bytes = inmemZip.DeCompressData(strOrigCompress_bytes)
                    strRetData = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strRetData_bytes)
                except Exception as e:
                    strSampleData_bytes = strOrigBase64Data_bytes
                    if( len(strSampleData_bytes) > 20):
                        strSampleData = strSampleData_bytes[:20]
                    CTYLB_Log.ShowLog(1, 'CmdPack CliEx', 'base64 or unzip error [%s], orig data len %d, sample:[%s]' %
                                      (str(e), len(strRecvPacket_bytes), strSampleData_bytes.decode() ))
                del inmemZip

        return strRetData, strRetUniqueSign, strNotHandleContent_bytes

##############################################################
# 操作Yaml配置文件的类
# start by pxk. 171213.
##############################################################
class CTY_YamlFile:
    def __init__(self, filename):
        self.filename = filename
        self.config = None

    def load_configs(self, config_file=None):
        if config_file:
            self.filename = config_file
        with open(self.filename, 'r') as f:
            self.config = yaml.load(f)

    def get_config(self, key, default=None):
        if not self.config:
            self.load_configs()
        try:
            keys = key.split('.')
            temp = self.config
            for i in range(len(keys)):
                temp = temp[keys[i]]
            value = temp
        except:
            value = default
        return value


# TCP监听线程
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTCPListenThread( threading.Thread):
    def __init__(self, strThreadName, paramQueue, iListenPort):
        threading.Thread.__init__(self, name=strThreadName)
        self.s_MyQueue = paramQueue
        self.s_strMyName = strThreadName
        self.s_iMyPort = iListenPort
        self.g_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_bThreadRunning = True

        if( self.g_ExecMutex.acquire()):
            self.s_clientConnectArray = []
            self.s_clientAddressArray = []
            self.g_ExecMutex.release()
        self.s_myListenSocket = None

    def __del__(self):
        self.CloseListenSocket()
        pass

    # 关闭监听管套
    def CloseListenSocket(self):
        if( self.s_myListenSocket != None):
            self.s_myListenSocket.close()
            self.s_myListenSocket = None

    # 运行，进行监听
    def run(self):
        self.s_MyQueue.get()  # get one exec queue unit

        if( self.s_iMyPort > 0):
            CTCPListenThread.ShowLog(0, 'tcp listen [%d] starting' % (self.s_iMyPort))
            self.s_myListenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.s_myListenSocket.bind(('0.0.0.0', self.s_iMyPort))
                self.s_myListenSocket.listen(10)
            except:
                CTCPListenThread.ShowLog(1, 'Listen Port Failure. maybe port %d been occupy' % (self.s_iMyPort))
                self.s_bThreadRunning = False
        else:
            self.s_myListenSocket = None

        while self.s_bThreadRunning:
            if( self.s_myListenSocket):
                try:
                    connection, address = self.s_myListenSocket.accept()
                    if( self.s_bThreadRunning):
                        if (self.g_ExecMutex.acquire() ):
                            self.s_clientConnectArray.append( connection)
                            self.s_clientAddressArray.append( address)
                            self.g_ExecMutex.release()
                except Exception as e:
                    print(e)
            else:
                time.sleep(0.01)

        self.s_MyQueue.task_done()   # finish queue unit
        CTCPListenThread.ShowLog(0, 'tcp listen [%d] sock exit' % (self.s_iMyPort))
        pass

    def SafeStop(self):
        if (self.g_ExecMutex.acquire()):
            self.s_bThreadRunning = False
            self.g_ExecMutex.release()
        if( self.s_myListenSocket):
            listenAddr = ('localhost', self.s_iMyPort)
            newSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                newSock.connect(listenAddr)
                newSock.close()
            except Exception as e:
                pass
        self.CloseListenSocket()

    # 获得客户端地址
    def SafeGetNewClientConnec(self):
        retClientConnectSock = None
        retClientAddress = None
        if (self.g_ExecMutex.acquire()):
            if( len( self.s_clientConnectArray) > 0):
                retClientConnectSock = self.s_clientConnectArray[0]
                self.s_clientConnectArray.remove( retClientConnectSock)
                retClientAddress = self.s_clientAddressArray[0]
                self.s_clientAddressArray.remove( retClientAddress)
            self.g_ExecMutex.release()

        return retClientConnectSock, retClientAddress

    @staticmethod
    def ShowLog( iWarnLevel, strMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'Listen Thread', strMsg)

# 执行管套单元
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CExecSockUnit_bytes:
    def __init__(self, execConnectSocket, parentMutex):
        self.s_mySocket = execConnectSocket
        self.s_parentMutex = parentMutex
        self.s_bPeerActiveClose = False
        self.s_recvBuffArray_bytes = []
        self.s_toBeSendBuffArray_bytes = []
        self.s_iLastSameErrorCount = 0    # 上次同样错误的计数
        self.s_iLastErrorCode = 0       # 上次错误的值
        self.s_firstSameErrorTime = datetime.now()   # 同样错误代码的第一次发生时间

    def SafeAddRecvDataToList(self, strData_bytes):
        if (self.s_parentMutex.acquire()):
            self.s_recvBuffArray_bytes.append(strData_bytes)
            self.s_parentMutex.release()

    def PopRecvData(self):
        # 此处不应该进入资源锁，因为上级函数已经调用锁定了.
        if( len(self.s_recvBuffArray_bytes) > 1):
            pass
        strRet_bytes = CTY_WebClientPacket.CompleteExactPopOneHttpSessionFromBuffArray( self.s_recvBuffArray_bytes)
        return strRet_bytes

    def Safe_QueryNeedSendData(self):
        retData_bytes = None
        if (self.s_parentMutex.acquire()):
            if( len(self.s_toBeSendBuffArray_bytes) > 0):
                retData_bytes = self.s_toBeSendBuffArray_bytes[0]
            self.s_parentMutex.release()
        return retData_bytes

    def Safe_InsertUnSendDataToHead(self, strLeftData_bytes):
        retData = None
        if (self.s_parentMutex.acquire()):
            if( len(self.s_toBeSendBuffArray_bytes) > 0):
                self.s_toBeSendBuffArray_bytes.insert(0, strLeftData_bytes)
                print('insert back data to head link %d' % (len(strLeftData_bytes)))
            else:
                self.s_toBeSendBuffArray_bytes.append(strLeftData_bytes)
            self.s_parentMutex.release()
        return retData

    def Safe_PopDataToBeSend(self):
        retData_bytes = None
        if (self.s_parentMutex.acquire()):
            if( len(self.s_toBeSendBuffArray_bytes) > 0):
                retData_bytes = self.s_toBeSendBuffArray_bytes.pop(0)
            self.s_parentMutex.release()
        return retData_bytes

    def Safe_QueryNeedSendCount(self):
        iRetLen = 0
        if (self.s_parentMutex.acquire()):
            iRetLen = len(self.s_toBeSendBuffArray_bytes)
            self.s_parentMutex.release()
        return iRetLen

    def Safe_PromptDataToBeSend(self, strData):
        if (self.s_parentMutex.acquire()):
            strData_bytes = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strData)
            self.s_toBeSendBuffArray_bytes.append( strData_bytes)
            self.s_parentMutex.release()

    def SafeSendData(self, strData_bytes):
        if (self.s_parentMutex.acquire()):
            try:
                self.s_mySocket.sendall( strData_bytes)
                print('                                   sock sendall:%d' % (len(strData_bytes)))
            except Exception as e:
                self.s_bPeerActiveClose = True
                print('impossible as calling low level-socket-sendall')
            self.s_parentMutex.release()

    def ResetBuffer(self):
        if (self.s_parentMutex.acquire()):
            self.s_recvBuffArray_bytes = []
            self.s_parentMutex.release()
        self.SetLastError(0)

    # 设置上次错误的值。如果是同一个错误，增加错误计数
    # start by sk. 170512
    def SetLastError(self, iErrorCode):
        if( iErrorCode > 0):
            if( self.s_iLastErrorCode == iErrorCode):
                self.s_iLastSameErrorCount += 1
            else:
                self.s_iLastErrorCode = iErrorCode
                self.s_firstSameErrorTime = datetime.now()
                self.s_iLastSameErrorCount = 0
        else:
            self.s_iLastErrorCode = 0
            self.s_iLastSameErrorCount = 0

    # 检查是否错误发生时间足够长，发生次数足够多
    # start by sk. 170512
    def CheckErrorTimeCount(self, iErrorCodeArray, iMaxOccureCount, iOccureTick):
        bRetValue = False
        for iErrorCode in iErrorCodeArray:
            if( iErrorCode == self.s_iLastErrorCode):
                if( self.s_iLastSameErrorCount >= iMaxOccureCount):
                    if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_firstSameErrorTime, iOccureTick)):
                        bRetValue = True
                        break
        return bRetValue


# TCP已经连接的管套线程
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTCPConnectedSocketThread_bytes( threading.Thread):
    def __init__(self, strThreadName, paramQueue):
        threading.Thread.__init__(self, name=strThreadName)
        self.s_MyQueue = paramQueue
        self.s_strMyName = strThreadName

        self.g_ExecMutex = threading.Lock()  # 线程执行同步锁
        self.s_bThreadRunning = True
        self.s_bPeerClose = True

        self.s_myExecSocketArray = None
        self.s_execOpSockUnitArray = None
        self.s_disconnectSockArray = None
        if( self.g_ExecMutex.acquire()):
            self.s_myExecSocketArray = []
            self.s_execOpSockUnitArray = []
            self.s_disconnectSockArray = []
            self.g_ExecMutex.release()

    def __del__(self):
        self.CloseAllExecSocket()
        pass

    # 关闭管套
    def CloseAllExecSocket(self):
        if( self.g_ExecMutex.acquire()):
            for eachSockUnit in self.s_execOpSockUnitArray:
                eachSockUnit.s_mySocket.close()
            self.s_execOpSockUnitArray = []
            self.s_myExecSocketArray = []

            self.g_ExecMutex.release()

    # 关闭其中一个客户端
    def CloseExecSocket(self, curSock):
        if (self.g_ExecMutex.acquire()):
            for eachSockUnit in self.s_execOpSockUnitArray:
                if( eachSockUnit.s_mySocket == curSock):
                    self.s_execOpSockUnitArray.remove( eachSockUnit)
                    self.s_myExecSocketArray.remove( curSock)
                    curSock.close()
                    self.s_disconnectSockArray.append( curSock)
                    break

            self.g_ExecMutex.release()

    # 增加客户端管套
    def AddClientSocket(self, curSock, existRecvBuffArray_bytes):
        if (self.g_ExecMutex.acquire()):
            newOpSockUnit = CExecSockUnit_bytes( curSock, self.g_ExecMutex)
            self.s_execOpSockUnitArray.append( newOpSockUnit)
            self.s_myExecSocketArray.append( curSock)
            if( existRecvBuffArray_bytes):
                newOpSockUnit.s_recvBuffArray_bytes.extend( existRecvBuffArray_bytes)
            self.g_ExecMutex.release()
            curSock.setblocking(0)

    # 获得接受到的数据
    def SafePopRecvPacketUnit(self):
        retRecvData_bytes = None
        retExecSockUnit = None

        if (self.g_ExecMutex.acquire()):
            for eachSockUnit in self.s_execOpSockUnitArray:
                strRetData_bytes = eachSockUnit.PopRecvData()
                if( strRetData_bytes):
                    retRecvData_bytes = strRetData_bytes
                    retExecSockUnit = eachSockUnit
                    break
            self.g_ExecMutex.release()
        return retRecvData_bytes, retExecSockUnit

    # 提交数据进行发送
    def SafePromptDataToSend(self, execSocket, strData_bytes):
        sockOpUnit = self.SearchOpUnitBySocket(execSocket)
        if( sockOpUnit):
            sockOpUnit.Safe_PromptDataToBeSend( strData_bytes)

    # 获得已经断开连接关闭的客户端
    def SafePopDisconnectClosedSocket(self):
        retDestSocket = None

        if (self.g_ExecMutex.acquire()):
            if( len( self.s_disconnectSockArray) > 0):
                retDestSocket = self.s_disconnectSockArray.pop(0)
            self.g_ExecMutex.release()
        return retDestSocket

    # 运行，用recv的方式
    def run(self):
        iFreeCount = 0
        self.s_MyQueue.get()
        while( self.s_bThreadRunning):
            bTaskBusy = False
            for eachSock in self.s_myExecSocketArray:
                bCloseSocket = False

                bContinueRecv = True
                opSockUnit = None
                while( bContinueRecv):
                    try:
                        strData_bytes = eachSock.recv(512000)
                    except socket.error as e:
                        bCloseSocket, bNoErrorNeedSkip = CTYLB_MainSys_MiscFunc.CheckSockErrorCode(e)
                        strData_bytes = None

                    if (strData_bytes):
                        bTaskBusy = True
                        if( not opSockUnit):
                            opSockUnit = self.SearchOpUnitBySocket(eachSock)
                        strStoreData_bytes = strData_bytes
                        if (opSockUnit):
                            opSockUnit.SafeAddRecvDataToList(strStoreData_bytes)
                        else:
                            # A readable client socket has data
                            CTCPConnectedSocketThread_bytes.ShowLog( 1, 'not exist client received "%s"' % (strStoreData_bytes.decode()))
                    else:
                        bContinueRecv = False

                if (bCloseSocket):
                    self.CloseExecSocket( eachSock)
                pass

            # 调度数据包进行发送
            needSkipUnitArray = []
            while( True):
                bOneHaveContent = False    # 至少有一个有内容
                for eachOpUnit in self.s_execOpSockUnitArray:
                    # 是否需要跳过?
                    if( eachOpUnit in needSkipUnitArray):
                        pass
                    else:
                        strToBeSendData_bytes = eachOpUnit.Safe_QueryNeedSendData()
                        if( strToBeSendData_bytes):
                            bOneHaveContent = True
                            try:
                                iExecLen = len(strToBeSendData_bytes)
                                iSendDataLen = eachOpUnit.s_mySocket.send( strToBeSendData_bytes)
                                if( iSendDataLen < iExecLen):
                                    bTaskBusy = False

                                    # 有数据尚未发送
                                    if( iSendDataLen > 0):
                                        CTCPConnectedSocketThread_bytes.ShowLog(1, 'send data part. [%d ~ %d]' % ( iExecLen, iSendDataLen))
                                        strLeftData_bytes = strToBeSendData_bytes[iSendDataLen:]
                                        # 将原来的移除，把未发送的插入
                                        _ = eachOpUnit.Safe_PopDataToBeSend()
                                        eachOpUnit.Safe_InsertUnSendDataToHead( strLeftData_bytes)
                                    else:
                                        CTCPConnectedSocketThread_bytes.ShowLog(1, 'no send data. orig size:[%d]' % (iExecLen))
                                else:
                                    # 成功发送，删除原来的
                                    _ = eachOpUnit.Safe_PopDataToBeSend()
                            except Exception as e:
                                eachOpUnit.SetLastError( e.errno)
                                # 检查，是否10035错误超过8次以上，超过5秒钟？
                                if( eachOpUnit.CheckErrorTimeCount( [35, 10035], 8, 5)):
                                    CTCPConnectedSocketThread_bytes.ShowLog(1, 'error timecount occure. reset-connect. %s' % (str(e)))
                                    bCloseSocket = True
                                else:
                                    CTCPConnectedSocketThread_bytes.ShowLog(1, 'send maybe error. %s' % (str(e)))
                                    bCloseSocket, bNoErrorNeedSkip = CTYLB_MainSys_MiscFunc.CheckSockErrorCode(e)
                                    if( bNoErrorNeedSkip):
                                        iNeedSendCount = eachOpUnit.Safe_QueryNeedSendCount()
                                        if (iNeedSendCount > 1):
                                            pass
                                            CTCPConnectedSocketThread_bytes.ShowLog(1, 'sending block. %d to be send' % ( iNeedSendCount))
                                        needSkipUnitArray.append( eachOpUnit)
                                if( bCloseSocket):
                                    eachOpUnit.s_bPeerActiveClose = True
                                    needSkipUnitArray.append( eachOpUnit)
                # 没有一个单元有内容，跳出循环
                if( not bOneHaveContent):
                    break

            for eachOpUnit in self.s_execOpSockUnitArray:
                if( eachOpUnit.s_bPeerActiveClose):
                    self.CloseExecSocket(eachOpUnit.s_mySocket)
                    break
            if( not bTaskBusy):
                iFreeCount += 1
                if(iFreeCount > g_iMaxExecIdleCount):
                    time.sleep(0.01)
            else:
                iFreeCount = 0

        self.s_MyQueue.task_done()   # finish queue unit
        pass

    def SafeStop(self):
        if (self.g_ExecMutex.acquire()):
            self.s_bThreadRunning = False
            self.g_ExecMutex.release()
        self.CloseAllExecSocket()

    # 根据管套值搜索操作单元
    def SearchOpUnitBySocket(self, execSocket):
        retOpSockUnit = None
        if (self.g_ExecMutex.acquire()):
            for eachOpUnit in self.s_execOpSockUnitArray:
                if( eachOpUnit.s_mySocket == execSocket):
                    retOpSockUnit = eachOpUnit
                    break
            self.g_ExecMutex.release()
        return retOpSockUnit

    @staticmethod
    def ShowLog( iWarnLevel, strMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'Connect Thread', strMsg)

# 单个执行管套单元
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CExecConnectSockUnit_bytes:
    s_g_iMaxRetryWaitSecond = 100    # 最长重试时间
    s_g_iMaxConnectTime = 10        # 最长连接等待时间

    s_g_iStatus_None = 0
    s_g_iStatus_Connecting = 1
    s_g_iStatus_Connect_Fail = 2
    s_g_iStatus_Connect_Succ = 3
    s_g_iStatus_Succ_MoveOut = 4
    s_g_iStatus_PrepareWait_Connect = 5
    s_g_iStatus_AutoConnect_Fail = 6

    def __init__(self, remoteAddr):
        self.s_remoteAddr = remoteAddr
        self.s_execSocket = None
        self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_None
        self.s_bStatusUpdateNeedNotify = False
        self.s_lastReConnectTime = datetime.now()
        self.s_iCurWaitSecond = 3
        self.s_tmpSaveRecvBuffArray_bytes = []

    def __del__(self):
        self.StopSocket()

    def StopSocket(self):
        if( self.s_execSocket):
            self.s_execSocket.close()
            self.s_execSocket = None

    def StartExecConnect(self):
        self.s_tmpSaveRecvBuffArray = []   # 清空旧的缓冲
        strMsg = 'exec connect: %s' % (str(self.s_remoteAddr))
        CExecConnectSockUnit_bytes.ShowLog( 0, strMsg)

        self.StopSocket()   # 先把旧的管套关闭
        self.s_execSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_execSocket.setblocking(0)
        try:
            self.s_execSocket.connect( self.s_remoteAddr)
        except Exception as e:
            pass
        self.s_iCurStatus = self.s_g_iStatus_Connecting

    def TimerCheck(self):
        bRetValue = False
        # 当正在连接，这里进行检测。
        if( self.s_iCurStatus == self.s_g_iStatus_Connecting):
            bCloseSocket = False
            try:
                strData_bytes = self.s_execSocket.recv(10240000)
            except socket.error as e:
                if( e.errno == 10057):  # 特别处理，等待连接成功
                    pass
                elif( e.errno == 57):  # 特别处理，等待连接成功
                    pass
                else:
                    bCloseSocket, bNoErrorNeedSkip = CTYLB_MainSys_MiscFunc.CheckSockErrorCode(e)
                    if( bNoErrorNeedSkip):  # 35, 10035, 11
                        self.s_bStatusUpdateNeedNotify = True
                        self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_Connect_Succ
                strData_bytes = None
            if (strData_bytes):
                self.s_bStatusUpdateNeedNotify = True
                self.s_tmpSaveRecvBuffArray_bytes.append(strData_bytes)
                self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_Connect_Succ
                bRetValue = True

            if( CTYLB_MainSys_MiscFunc.CheckIdleTime( self.s_lastReConnectTime, self.s_g_iMaxConnectTime)):
                bCloseSocket = True

            if( bCloseSocket):
                self.SetSockAutoConnectFailClosed()
        else:
            bRetValue = self.ExecAutoScheduleConnect()
        return bRetValue

    # 执行自动调度进行连接
    def ExecAutoScheduleConnect(self):
        bExecAction = False

        if( self.s_iCurStatus == CExecConnectSockUnit_bytes.s_g_iStatus_None):
            self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_PrepareWait_Connect
            self.s_lastReConnectTime = datetime.now()
            self.s_iCurWaitSecond = random.randint(2,5)
        elif( self.s_iCurStatus == CExecConnectSockUnit_bytes.s_g_iStatus_PrepareWait_Connect):
            nowTime = datetime.now()
            timeDiff = nowTime-self.s_lastReConnectTime
            if( timeDiff.seconds > self.s_iCurWaitSecond):
                bExecAction = True
                self.StartExecConnect()
                self.s_lastReConnectTime = nowTime
        elif( self.s_iCurStatus == CExecConnectSockUnit_bytes.s_g_iStatus_AutoConnect_Fail):
            self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_PrepareWait_Connect
            self.s_iCurWaitSecond *= 2
            if( self.s_iCurWaitSecond > CExecConnectSockUnit_bytes.s_g_iMaxRetryWaitSecond):
                self.s_iCurWaitSecond = CExecConnectSockUnit_bytes.s_g_iMaxRetryWaitSecond
        return bExecAction

    # 管套调度连接自动失败
    def SetSockAutoConnectFailClosed(self):
        self.s_lastReConnectTime = datetime.now()
        self.s_execSocket = None
        self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_AutoConnect_Fail

    # 管套被外部关闭
    def SetSockBeenClosed(self):
        self.s_execSocket = None
        self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_None

    # 获取状态更改通知标识
    def RetriveStatusNotify(self):
        bRetValue = False
        if( self.s_bStatusUpdateNeedNotify):
            self.s_bStatusUpdateNeedNotify = False
            bRetValue = True
        return bRetValue

    # 获取状态更改通知标识
    def SetSockMonitorByOtherThread(self):
        self.s_iCurStatus = CExecConnectSockUnit_bytes.s_g_iStatus_Succ_MoveOut
        self.s_tmpSaveRecvBuffArray_bytes = []

    @staticmethod
    def ShowLog( iWarnLevel, strMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'Sock_Connect', strMsg)

# TCP监听管套实现
# start by sk. 170123
class CTCPListenSock:
    # s_iListenPort = 8000
    # s_myListenThread = None
    # s_exGlobalTaskQueue = None

    def __init__(self, iPort, taskQueue):
        self.s_iListenPort = iPort
        self.s_exGlobalTaskQueue = taskQueue
        self.s_myListenThread = None

    def __del__(self):
        pass

    def Stop(self):
        if( self.s_myListenThread != None):
            self.s_myListenThread.SafeStop()

    def Start(self):
        self.s_exGlobalTaskQueue.put(1)
        self.s_myListenThread = CTCPListenThread( "tcp-listen-thread", self.s_exGlobalTaskQueue, self.s_iListenPort)
        self.s_myListenThread.setDaemon( True)
        self.s_myListenThread.start()
        pass

    def TimerCheck(self):
        pass

# 执行连接管套管理实现
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CExecConnectSockMang_bytes:

    def __init__(self, remoteAddrArray):
        self.s_execConnectSockArray = []
        for eachAddr in remoteAddrArray:
            newConnectSockUnit = CExecConnectSockUnit_bytes( eachAddr)
            self.s_execConnectSockArray.append( newConnectSockUnit)

    def __del__(self):
        for eachUnit in self.s_execConnectSockArray:
            eachUnit.StopSocket()

    def TimerCheck_Auto_Connect(self):
        for eachUnit in self.s_execConnectSockArray:
            eachUnit.TimerCheck()
        pass

    def GetLastSuccConnectSock(self):
        retUnit = None

        for eachUnit in self.s_execConnectSockArray:
            if( eachUnit.RetriveStatusNotify()):
                if( eachUnit.s_iCurStatus == CExecConnectSockUnit_bytes.s_g_iStatus_Connect_Succ):
                    retUnit = eachUnit
                    break

        return retUnit

    def DestSockClosed(self, destClosedSocket):
        retUnit = self.SearchUnitBySock( destClosedSocket)
        if( retUnit):
            retUnit.SetSockBeenClosed()

    def SearchUnitBySock(self, destSocket):
        retUnit = None
        for eachUnit in self.s_execConnectSockArray:
            if( eachUnit.s_execSocket == destSocket):
                retUnit = eachUnit
                break
        return retUnit

# TCP接收管套实现
# start by sk. 170123
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTCPAcceptConnectMangClient_bytes:
    def __init__(self, exTaskQueue):
        self.s_myExecConnectSocketThread = None
        self.s_exGlobalTaskQueue = exTaskQueue

    def __del__(self):
        pass

    def Stop(self):
        if (self.s_myExecConnectSocketThread != None):
            self.s_myExecConnectSocketThread.SafeStop()

    def Start(self):
        self.s_exGlobalTaskQueue.put(1)
        self.s_myExecConnectSocketThread = CTCPConnectedSocketThread_bytes( "tcp-accept-connect-socket", self.s_exGlobalTaskQueue)
        self.s_myExecConnectSocketThread.setDaemon(True)
        self.s_myExecConnectSocketThread.start()
        pass

    def TimerCheck(self):
        pass
pass


# 网络基本定义
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Ct_NetBase_bytes:
    s_iSockType_Accept = 1   # 网络类型，监听接受的连接
    s_iSockType_Connect = 2   # 网络类型，主动连接对方

    s_iReply_NotMySock = 0  # 不是我的管套范围
    s_iReply_WebHTTP_Answner_CombedData = 1
    s_iReply_Invalid_Protocol = 2
    s_iReply_ProtocolOK_NotNeedReply = 3

    s_iComb_MainType_NegoHand = 1
    s_iComb_SubType_NegoHand_SendMyName = 1
    s_iComb_SubType_NegoHand_ReplyOK = 2

    s_g_iIdleBusySendRecvSecond = 2   # 两秒内空闲，当作不空闲
    s_g_iMaxSimulateUniqueCount = 1  # 最大并发交互队列数

    def __init__(self, socketValue, iSockType, peerNetAddr):
        self.s_destSockValue = socketValue
        self.s_peerAddress = peerNetAddr

        self.s_strUnitName = ''
        self.s_iSockType = iSockType
        self.s_bDataFormatBadClose = False    # 是否协议格式错误操作失败？
        self.s_lastSendHandTime = datetime.now()

        self.s_lastRecvContentTime = datetime(2017,1,1)  # 上次接收内容的时间。
        self.s_lastSendContentTime = datetime(2017,1,1)  # 设置上次发送内容时间。
        self.s_iLastSendContentCount = 0  # 上次连续发送内容计数
        self.s_iLastRecvContentCount = 0  # 上次连续接收内容计数
        self.s_strToBeSendBuffArray_bytes = []   # 等待发送队列
        self.s_SimulateUniqueArray = []   # 并发交互会话唯一标识存储队列
        self.s_iLastUniqueIndex = 0   # 最后唯一标识值
        pass

    # 执行连接的动作标记
    # start by sk. 170218
    def Set_ExecSendAction_Flag(self):
        self.s_lastSendHandTime = datetime.now()

    def TempShort_ExecSendPacket(self, strPacket_bytes):
        bRetSucc = False

        if( self.s_bDataFormatBadClose):
            pass
        else:
            try:
                iNeedSendLen = len(strPacket_bytes)
                iExecLen = self.s_destSockValue.send(strPacket_bytes)
                if( iExecLen < iNeedSendLen):
                    print('  !!! error. netbase want to send %d, but actually %d' % (iNeedSendLen, iExecLen))
                else:
                    pass
                    # self.s_destSockValue.sendall(strPacket)
                # 设置状态为新的等待状态
                self.s_lastSendHandTime = datetime.now()
                bRetSucc = True
            except socket.error as e:
                bCloseSocket, bNoErrorNeedSkip = CTYLB_MainSys_MiscFunc.CheckSockErrorCode(e)
                if( bCloseSocket):
                    self.SetDataFormatBadClose()
                    print('  !!! net direct send error.:%s' % (str(e)))
                pass
        return bRetSucc

    # 数据包格式错误，连接失败
    # start by sk. 170125
    def SetDataFormatBadClose(self):
        self.s_bDataFormatBadClose = True

    # 获得下一步可以立刻发送的所需条件, 包括 标识符
    # start by sk. 170313
    def Viul_GetNextSendResource(self, iMaxIdleTime, iMaxSignBusyStillCheckTime):
        bCanExecSend = False
        strRetTransUniqueSign = ''

        # 若无数据内容提交，主动发送握手包。可能服务端会有数据回应
        if (self.CanActiveSendNow(iMaxIdleTime)):
            strRetTransUniqueSign = self.Request_Free_SessionUniqueSign()  # 申请会话占用符
            if (strRetTransUniqueSign):
                bCanExecSend = True
            else:
                # 如果还是繁忙，那么，依然发送心跳包
                if( self.Is_LastSend_IdleTime_LargeThan( iMaxSignBusyStillCheckTime)):
                    bCanExecSend = True
                    # 清空
                    self.s_SimulateUniqueArray = []
        return bCanExecSend, strRetTransUniqueSign

    # 现在是否可以发送。按照上面的规则。如果刚才有发送，则继续发送。如果无发送，则等待最长时间。
    # start by sk. 170216
    def CanActiveSendNow(self, iMaxIdleTime):
        bCanSend = False

        bLastAction = False
        lastActionDiff = None

        nowTime = datetime.now()

        if( self.s_iLastSendContentCount > 0):  # 上次连续发送内容计数
            bLastAction = True
            lastActionDiff = nowTime - self.s_lastSendContentTime
        elif( self.s_iLastRecvContentCount > 0):  # 上次连续接收内容计数
            bLastAction = True
            lastActionDiff = nowTime - self.s_lastRecvContentTime
        else:
            timeDiff = nowTime - self.s_lastSendHandTime
            if( timeDiff.microseconds > iMaxIdleTime):  # 改成毫秒
                bCanSend = True
            else:
                pass

        # 刚接收和发送过，要继续发。每0.2秒发一次
        if( bLastAction):
            if( lastActionDiff and (lastActionDiff.microseconds>1)):  # 改成毫秒
                bCanSend = True
            else:
                pass
        return bCanSend

    # 设置上次网络活动时间，有内容，还是空内容
    # start by sk. 170216
    def Set_LastNetContent_ActionTime_HaveOrEmpty( self, bSendOrRecv, bHaveContent):
        if( bHaveContent):
            # 有内容
            nowTime = datetime.now()
            if( bSendOrRecv):
                self.s_lastSendContentTime = nowTime
                self.s_iLastSendContentCount += 1
            else:
                self.s_lastRecvContentTime = nowTime
                self.s_iLastRecvContentCount += 1
        else:
            curTime = datetime.now()
            # 没有内容，空数据
            if( bSendOrRecv):
                timeDiff = curTime - self.s_lastSendContentTime
                if( timeDiff.seconds >= self.s_g_iIdleBusySendRecvSecond):
                    self.s_iLastSendContentCount = 0
            else:
                timeDiff = curTime - self.s_lastRecvContentTime
                if( timeDiff.seconds >= self.s_g_iIdleBusySendRecvSecond):
                    self.s_iLastRecvContentCount = 0
    pass

    # 设置名字
    # start by sk. 170130
    def SetUnitName(self, strName):
        self.s_strUnitName = strName

    # 获得名字
    # start by sk. 170130
    def GetUnitName(self):
        return self.s_strUnitName

    # 返回 上次发送后的等待时间超过某值
    # start by sk. 170126
    def Is_LastSend_IdleTime_LargeThan(self, iSecondTick):
        bRetValue = False
        timeDiff = datetime.now() - self.s_lastSendHandTime
        if (timeDiff.seconds >= iSecondTick):
            bRetValue = True
        return bRetValue

    # 申请可用的唯一会话标识，返回空表示已经用完了
    # start by sk. 170219
    def Request_Free_SessionUniqueSign(self):
        strRetUniqueSign = b''
        if( len(self.s_SimulateUniqueArray) < self.s_g_iMaxSimulateUniqueCount):
            strRetUniqueSign = str(self.s_iLastUniqueIndex)
            self.s_iLastUniqueIndex += 1
            # strRetUniqueSign = CTYLB_Mang_BusisUnit_Base.GenerateUniqueKeyStr()
            self.s_SimulateUniqueArray.append( strRetUniqueSign)
        return strRetUniqueSign

    # 归还，去除占用的唯一会话标识
    # start by sk. 170219
    def GiveBack_SessionUniqueSign(self, strUniqueSign):
        if( strUniqueSign in self.s_SimulateUniqueArray):
            self.s_SimulateUniqueArray.remove( strUniqueSign)
        else:
            pass
            # CTYLB_Log.ShowLog(1, 'NetBase', 'Error, UnExist session unique sign %s.' % (strUniqueSign))


# 网络基本定义
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_ShakeHand_NetBase_bytes(CTYLB_Ct_NetBase_bytes):
    # s_iShakeHandStepStatus = 0  # 握手步骤

    # 服务器和节点之间，握手的状态值
    s_iShakeHand_None = 0
    s_iShakeHand_OK = 1
    s_iShakeHand_Fail = 2
    s_iShakeHand_PeerClose = 3

    s_iClientHand_Accept_Send1 = 6
    s_iClientHand_Accept_RecvPeer = 7
    s_iClientHand_Connect_Send1 = 8

    def __init__(self, socketValue, iSockType, peerNetAddr):
        CTYLB_Ct_NetBase_bytes.__init__( self, socketValue, iSockType, peerNetAddr)
        self.s_iShakeHandStepStatus = CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_None
        pass

    def __del__(self):
        pass

    def SetShakeHandResult(self, bProtocolFit):
        self.s_iShakeHandStepStatus = CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_OK if bProtocolFit else\
            CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_Fail
    pass

# 全局传输参数块
# start by sk. 170217
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Global_UnivTrans_Param:
    def __init__(self, dbConn=None, onlineCLientMang=None, srvUnitMang=None, strMyIDName='', connSockThread=None):
        self.s_u_DbConn = dbConn
        self.s_u_OnLineClientUnitMang = onlineCLientMang
        self.s_u_SrvUnitMang = srvUnitMang
        self.s_u_strMySelfIDName = strMyIDName
        self.s_u_connSockThread = connSockThread
        pass

# 管理需要执行的业务单元－基本类
# start by sk. 170124
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_Mang_BusisUnit_Base_bytes:
    s_iMaxWaitHandSecond = 60  # 握手空闲最长等待时间.
    s_iMaxSvCtCheckSecond = 1  # 服务端和客户端之间检查时间
    s_g_iMaxBusyStillCheckTick = 240  # 服务端很繁忙，或者由于网络原因，对方的网络连接断开，而本地未收到。需要做的检查
    s_g_iMaxWaitComuInvalidIdleSecond = 600  # 最长通信等待时间，超过15分钟，没有数据包发送接收，即停止此会话连接

    def __init__(self, strName):
        self.s_mangUnitArray = []
        self.s_strMySelfName = strName
        self.s_iTotalSend = 0
        self.s_iTotalRecv = 0
        pass

    def __del__(self):
        pass

    # 需要重载 － 新建客户端单元, 单元为 CTYLB_Ct_NetBase 的子类
    @staticmethod
    def _Viul_CreateNewUnit(socketValue, iSockType, peerAddress):
        # newUnit = CTYLB_Ct_NetBase(socketValue, iSockType, peerAddress)
        return None

    # 增加新的管套单元
    def NewSockUnitArrive(self, socketValue, bIsAccept):
        iSockType = CTYLB_Ct_NetBase_bytes.s_iSockType_Accept if bIsAccept else CTYLB_Ct_NetBase_bytes.s_iSockType_Connect
        try:
            destAddr = socketValue.getpeername()
        except Exception as e:
            destAddr = ('', 0)
        newServerUnit = self._Viul_CreateNewUnit(socketValue, iSockType, destAddr)
        self.s_mangUnitArray.append(newServerUnit)
        return newServerUnit

    # 根据管套值，找对应单元
    def SearchUnitBySockValue(self, socketValue):
        retUnit = None
        for eachUnit in self.s_mangUnitArray:
            if (eachUnit.s_destSockValue == socketValue):
                retUnit = eachUnit
                break
        return retUnit

    # 管套接收数据调度
    # modify by sk. 170217. 修改第一个参数为 CTYLB_Global_UnivTrans_Param
    def _Viul_HandleSockRecvPacket(self, mangClientUnivealParam, socketValue, strRecvData_bytes):
        iDataLen = len(strRecvData_bytes)
        self.s_iTotalRecv += iDataLen

        iReplyCode = CTYLB_Ct_NetBase_bytes.s_iReply_Invalid_Protocol
        strReplyContent_bytes = b''

        return iReplyCode, strReplyContent_bytes

    # 检查是否需要发送数据
    def _Viul_TimerCheckSockSendPacket(self, mangClientUnivealParam):
        bRetValue = False
        for eachUnit in self.s_mangUnitArray:
            pass
        return bRetValue

    # 判断是否单元被对方主动关闭
    def Pop_ClosedByPeer_Unit(self):
        retUnit = None
        for eachUnit in self.s_mangUnitArray:
            if( eachUnit.s_iShakeHandStepStatus == CTYLB_ShakeHand_NetBase_bytes.s_iShakeHand_PeerClose):
                self.s_mangUnitArray.remove( eachUnit)
                retUnit = eachUnit
                break

        return retUnit

    # 判断是否单元出错需要主动关闭
    def Pop_ClosedByError_Unit(self):
        retUnit = None
        for eachUnit in self.s_mangUnitArray:
            if( eachUnit.s_bDataFormatBadClose):
                self.s_mangUnitArray.remove( eachUnit)
                retUnit = eachUnit
                break

        return retUnit

    # 外部管套关闭了，触发本身处理
    def ExecHandleSockClose(self, destSockClosed):
        destUnit = self.SearchUnitBySockValue(destSockClosed)
        if (destUnit):
            self.s_mangUnitArray.remove(destUnit)

    # 从数据包中，分析命令单元
    # start by sk. 170125
    # update sk，处理分析字符串结果为unicode
    @staticmethod
    def AnalySingleExactCmdUnitFromPacket(strHttpPacket_bytes, bHttp_SendPost_or_RecvReply):
        bRetExactResult = True
        retTyCmdUnit, strRetFromUser, strRetDestUser, retBuildTime = None, '', '', datetime.now()

        if (bHttp_SendPost_or_RecvReply):  # 是Post数据
            # 解包对方发送的post内容，如果正确，我回应 http结果
            strOrigPacket, strRetUniqueSign, strNotHandleContent_bytes = CTY_WebClientPacket.Srv_Exact_From_RecvPostPacket(
                strHttpPacket_bytes)
            if (len(strOrigPacket) > 0):
                cmdPack = CTY_CmdPack_Json()
                retTyCmdUnit, strRetFromUser, strRetDestUser, retBuildTime = cmdPack.ExactCombindData(strOrigPacket)
                if (retTyCmdUnit):
                    bRetExactResult = True
                else:
                    CTYLB_Mang_BusisUnit_Base_bytes.ShowLog(1, '1-Exact_HTTP_Comb_Error')
        else:
            # 解包对方发送的post内容，如果正确，我回应 http结果
            strOrigPacket, strRetUniqueSign, strNotHandleContent_bytes = CTY_WebClientPacket.Client_Exact_From_RecvWebReplyPacket(
                strHttpPacket_bytes)
            if (len(strOrigPacket) > 0):
                cmdPack = CTY_CmdPack_Json()
                retTyCmdUnit, strRetFromUser, strRetDestUser, retBuildTime = cmdPack.ExactCombindData(strOrigPacket)
                if (retTyCmdUnit):
                    bRetExactResult = True
                else:
                    CTYLB_Mang_BusisUnit_Base_bytes.ShowLog(1, '2-Exact_HTTP_Comb_Error')
            pass
        return bRetExactResult, strRetUniqueSign, retTyCmdUnit, strRetFromUser, strRetDestUser, retBuildTime, strNotHandleContent_bytes

    # 整合完整输出包，作为格式
    # start by sk. 170125
    @staticmethod
    def BuildFullPacketWithCmdUnit( strUniqueIndex, iMainCmd, iSubCmd, strFromUser, strDestUser,
                                    strCmdExData, bHttp_SendPost_or_RecvReply):
        if( not strCmdExData):
            strCmdExData = ' '

        replyCmdUnit = CTY_CmdUnit( iMainCmd, iSubCmd, strCmdExData)
        cmdPack = CTY_CmdPack_Json( strFromUser)
        strReplyCombData = cmdPack.GetCombindData(strDestUser, replyCmdUnit)

        webClientPack = CTY_WebClientPacket()
        if( bHttp_SendPost_or_RecvReply):
            strReplyContent_bytes = webClientPack.Client_Data_To_SendPostPacket( strUniqueIndex, strReplyCombData)
        else:
            strReplyContent_bytes = webClientPack.Srv_Data_To_WebReplyPacket( strUniqueIndex, strReplyCombData)

        return strReplyContent_bytes

    # 调整，唯一用户上线了。要把其他旧用户挤下去
    # start by sk. 170201
    def UniqueUserOnlineAdjust(self, clientUnit):
        for eachUnit in self.s_mangUnitArray:
            if( eachUnit == clientUnit):
                pass
            elif( eachUnit.GetUnitName() == clientUnit.GetUnitName()):
                eachUnit.SetDataFormatBadClose()
        pass

    # 生成唯一序列号
    # start by sk. 170219
    @staticmethod
    def GenerateUniqueKeyStr():
        iRand1 = random.randint(10000, 1000000)
        iRand2 = random.randint(1000, 1000000)
        strRetUnique = u'%s_%d_%d' % ( str(time.time()), iRand1, iRand2 )
        return strRetUnique

    @staticmethod
    def ShowLog( iWarnLevel, strMsg):
        CTYLB_Log.ShowLog( iWarnLevel, 'MangBusiUnitBase', strMsg)

# 管理客户端之间，服务器之间，互相之间－命令定义
# start by sk. 170129
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
class CTYLB_SvClt_Cmd_Base_bytes:
    s_g_strConsoleName = 'tp_console'
    # 对外输出的会话的状态
    s_iSession_OutStatus_Free = 0
    s_iSession_OutStatus_Handling = 1
    s_iSession_OutStatus_Finish = 2

    # 接收到的会话的状态，正在读取，接收完成，接收后，其他程序已经读取
    s_iSession_RecvStatus_Recving = 0
    s_iSession_RecvStatus_Recv_Finish = 1
    s_iSession_RecvStatus_Recv_Finish_Readed = 2

    s_iSessionRecType_SendOut = 0
    s_iSessionRecType_Recv = 1
    s_iSessionRecType_NeedPeerReSend = 2    # 需要对方重新发送命令
    s_iSessionRecType_NeedSelfExecReSend = 3    # 自身需要执行重新发送的命令
    s_iSessionRecType_NeedPeer_ReSend_Range = 4  # 需要对方重新发送范围
    s_iSessionRecType_NeedSelfExec_ReSend_Range = 5  # 需要对方重新发送范围

    # tasktype 由10以下作为保留类型
    s_iSession_TaskType_Unknown = 10
    s_iSession_TaskType_ChatText = 11
    s_iSession_TaskType_FileTrans = 12
    s_iSession_TaskType_RePeerSendSessionData = 13
    s_iSession_TaskType_SelfExecResendSessionData = 14
    s_iSession_TaskType_BadSessionIDValue = 15
    s_iSession_TaskType_RePeerSend_Range_SessionData = 16  # 请求重发范围数据
    s_iSession_TaskType_SelfExec_RePeerSend_Range_SessionData = 17  # 执行重发范围数据

    s_iPackType_TaskType_MultiLayer = 0
    s_iPackType_TaskType_NullFiller = 1
    s_iPackType_TaskType_NotKnown = 2

    s_iPackCmd_CtSv_SvCt_SvSv_Empty = 0    # 空的数据包
    # 不能小于10，否则与服务端 CTYLB_PsvPsv_BaseCmd 的子命令冲突
    s_iPackType_Ct_Sv_ChatText_Orig = 10  # 客户端到服务端，聊天文字
    s_iPackCmd_Ct_Sv_RequestRearchAbleClientList = 11  # 请求可到达的客户端列表。数据格式：无
    s_iPackCmd_Sv_Ct_RequestRearchAbleClientList_Reply = 12  # 服务端到客户端，我到达的客户端列表。数据格式为： ＃客户端名字#客户端名字＃
    s_iPackCmd_SubCmd_DirectSrvExec = 13  # 子命令，直接发给服务端执行
    s_iPackType_Ct_Ct_ChatText = 14  # 客户端到客户端，聊天文字
    s_iPackCmd_Ct_Ct_Db_Session_Trans = 15 # 客户端传输会话数据
    s_iPackCmd_SubCmd_BCast_OnLine = 16   # 客户端广播在线
    s_iPackCmd_SubCmd_Request_Newer_SessionID = 17   # 申请读取更加新的记录内容
    s_iPackCmd_Ct_Sv_RequestNeedRearchClientList = 18  # 请求需要到达的客户端列表。数据格式：无
    s_iPackCmd_Sv_Ct_RequestNeedRearchClientList_Reply = 19  # 服务端到客户端，我到达的客户端列表。数据格式为： ＃客户端名字#客户端名字＃
    s_iPackCmd_Ct_Ct_MidBalance_Db_Session_Trans = 20   # 经过中间平衡的数据包单元传输

    s_g_iInOutType_SystemNotify = 3    # 系统通知，用于inout表

    s_chClientName_Seperate ='@#$='

    # 构建客户端列表数据包。
    # 数据格式： ＃客户端名字，经过服务器个数#客户端名字，经过服务器个数＃
    @staticmethod
    def Comb_MultiClientNameList_Packet( strClientNameArray):
        strRet = CTYLB_SvClt_Cmd_Base_bytes.s_chClientName_Seperate.join( strClientNameArray)
        return strRet

    # 解开客户端列表内容
    # 数据格式： ＃客户端名字，经过服务器个数#客户端名字，经过服务器个数＃
    @staticmethod
    def Exact_MultiClientNameList_Packet( strBuffer_array):
        strRetArray = strBuffer_array.split( CTYLB_SvClt_Cmd_Base_bytes.s_chClientName_Seperate)
        return strRetArray
    pass

# 业务数据包单元
# start by sk. 170128
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# update to v3, by sk. 180314. to Json 格式
class CTYLB_Busis_Packet:
    s_iMyCombPack_Base_Size = 30  # 数据包基本大小
    s_strSign = 'faw3'

    def __init__(self, iCmd, iSessionID, iSubIndex, iLastPacket, strContent=''):
        self.s_iBusiCmdID = int(iCmd)
        self.s_strContent = strContent
        self.s_iSessionID = int(iSessionID)
        self.s_iSubIndex = int(iSubIndex)
        self.s_iLastPacket = int(iLastPacket)
        pass

    s_g_Sign_strSign = 'str_sign'
    s_g_Sign_iCmdID = 'iCmdID'
    s_g_Sign_iSessionID = 'iSessionID'
    s_g_Sign_iSubIndex = 'iSubIndex'
    s_g_Sign_iLastPacket = 'iLastPacket'
    s_g_Sign_strContent = 'strContent'

    # 获得组合数据包。
    # 数据格式：$# 标志$# 命令ID $# 命令内容 $#
    def GetCombindData( self):
        exJson = {}

        if( not isinstance(self.s_iBusiCmdID, int)):
            CTYLB_Log.ShowLog(1, 'error', 'int64???')

        exJson[CTYLB_Busis_Packet.s_g_Sign_strSign] = CTYLB_Busis_Packet.s_strSign
        exJson[CTYLB_Busis_Packet.s_g_Sign_iCmdID] = int(self.s_iBusiCmdID)
        exJson[CTYLB_Busis_Packet.s_g_Sign_iSessionID] = int(self.s_iSessionID)
        exJson[CTYLB_Busis_Packet.s_g_Sign_iSubIndex] = int(self.s_iSubIndex)
        exJson[CTYLB_Busis_Packet.s_g_Sign_iLastPacket] = int(self.s_iLastPacket)
        exJson[CTYLB_Busis_Packet.s_g_Sign_strContent] = self.s_strContent

        try:
            strTotal = json.dumps(exJson, ensure_ascii=False)
        except Exception as e:
            CTYLB_Log.ShowLog(1, 'error', str(e))
            strTotal = ''

        return strTotal

    # 分解组合数据包
    # strFormat --- 数据格式
    # strBuffer --- 经过封装的缓冲内容
    def ExactCombindData(self, strBuffer):
        bRetValue = False


        self.s_iBusiCmdID = 0
        self.s_iSessionID = 0
        self.s_iSubIndex = 0
        self.s_iLastPacket = 0
        self.s_strContent = ''

        strOrigBuff = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strBuffer)
        try:
            origJsonDict = json.loads(strOrigBuff)

            if(origJsonDict[CTYLB_Busis_Packet.s_g_Sign_strSign] == CTYLB_Busis_Packet.s_strSign):
                bRetValue = True
                self.s_iBusiCmdID = int(origJsonDict[CTYLB_Busis_Packet.s_g_Sign_iCmdID])
                self.s_iSessionID = int(origJsonDict[CTYLB_Busis_Packet.s_g_Sign_iSessionID])
                self.s_iSubIndex = int(origJsonDict[CTYLB_Busis_Packet.s_g_Sign_iSubIndex])
                self.s_iLastPacket = int(origJsonDict[CTYLB_Busis_Packet.s_g_Sign_iLastPacket])
                self.s_strContent = origJsonDict[CTYLB_Busis_Packet.s_g_Sign_strContent]
        except:
            pass

        return bRetValue  # Web客户端数据包封装单元

    # 大概计算数据包大小
    def NearCalcTransLength(self):
        retSize = CTYLB_Busis_Packet.s_iMyCombPack_Base_Size
        retSize += len( self.s_strContent)

        return retSize


# 对业务单元进行组合
# start by sk. 170129
# update by sk. 170430, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式
# update to v3, by sk. 180314. to Json 格式
class CTYLB_Comb_PackArray:
    s_strContainLayerPackSign = 'fpmx'  # 多层内容包
    s_iEachPackArrayCount = 4  # 每个包包含子层数目

    def __init__(self):
        pass

    s_g_Key_StrSign = 'strSign'
    s_g_Key_Str_1 = "str_1"
    s_g_Key_Str_2 = "str_2"
    s_g_Key_Str_3 = "str_3"
    s_g_Key_Str_0 = "str_0"

    # 获得组合数据包。递归调用。如果输入大于4个，分成4个分组，再进行封包，如果不足4个，则用空包填充。
    # 数据格式：$# 第一个数据包 # 第二个数据包 $# 。。。 $#
    @staticmethod
    def GetCombindData( busisPackArray):
        iPackCount = len(busisPackArray)

        # 每次分成 分包的个数，保证数字小于4
        if( iPackCount > CTYLB_Comb_PackArray.s_iEachPackArrayCount):
            iEachSplitPackCount = int( (iPackCount + CTYLB_Comb_PackArray.s_iEachPackArrayCount - 1) / \
                                       CTYLB_Comb_PackArray.s_iEachPackArrayCount)
            iCurIndex = 0
            eachPackArray = []
            midTotPackUnitArray = []
            for iEachIndex in range(iPackCount):
                eachPackArray.append( busisPackArray[iEachIndex])
                iCurIndex += 1
                # 当前是否充足？
                if( iCurIndex >= iEachSplitPackCount):
                    # 填充足够，分成一个综合包
                    strEachTotal_bytes = CTYLB_Comb_PackArray.GetCombindData( eachPackArray)
                    newPackUnit = CTYLB_Busis_Packet( CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_MultiLayer,
                                                      0, 0, 0, strEachTotal_bytes)
                    midTotPackUnitArray.append( newPackUnit)
                    # 重新清0
                    eachPackArray = []
                    iCurIndex = 0
            if( (iCurIndex > 0) and ( iCurIndex < iEachSplitPackCount)):
                for iLeftSubIndex in range(iCurIndex, iEachSplitPackCount):
                    # 不够数量，用空包进行填充
                    newPackUnit = CTYLB_Busis_Packet( CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_NullFiller,
                                                      0, 0, 0, ' ')
                    eachPackArray.append( newPackUnit)
                # 填充足够，组合成综合包
                strEachTotal = CTYLB_Comb_PackArray.GetCombindData(eachPackArray)
                newPackUnit = CTYLB_Busis_Packet(CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_MultiLayer,
                                                 0, 0, 0, strEachTotal)
                midTotPackUnitArray.append(newPackUnit)

            strMultiTotal = CTYLB_Comb_PackArray.GetCombindData(midTotPackUnitArray)
        else:
            # 数量足够吗？如果不够，填充到4个，进行封装组合
            fitCountArray = []
            fitCountArray.extend( busisPackArray)
            if( iPackCount < CTYLB_Comb_PackArray.s_iEachPackArrayCount):
                for iLeftSubIndex in range(iPackCount, CTYLB_Comb_PackArray.s_iEachPackArrayCount):
                    newPackUnit = CTYLB_Busis_Packet( CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_NullFiller,
                                                      0, 0, 0, ' ')
                    fitCountArray.append( newPackUnit)

            # 获得每个大小
            strEachContentArray = []
            iContentLenArray = []
            for eachPackUnit in fitCountArray:
                strEach = eachPackUnit.GetCombindData()
                strEachContentArray.append(strEach)
                iContentLenArray.append( len(strEach))

            exJson = {}
            exJson[CTYLB_Comb_PackArray.s_g_Key_StrSign] = CTYLB_Comb_PackArray.s_strContainLayerPackSign
            exJson[CTYLB_Comb_PackArray.s_g_Key_Str_0] = strEachContentArray[0]
            exJson[CTYLB_Comb_PackArray.s_g_Key_Str_1] = strEachContentArray[1]
            exJson[CTYLB_Comb_PackArray.s_g_Key_Str_2] = strEachContentArray[2]
            exJson[CTYLB_Comb_PackArray.s_g_Key_Str_3] = strEachContentArray[3]

            strMultiTotal = json.dumps(exJson, ensure_ascii=False)

        return strMultiTotal

    # 分解组合数据包
    # strFormat --- 数据格式
    # strBuffer --- 经过封装的缓冲内容
    @staticmethod
    def ExactCombindData(strBuffer):
        retBusisPackArray = []

        strOrigBuffer = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strBuffer)
        try:
            origJson = json.loads(strOrigBuffer)

            if( origJson[CTYLB_Comb_PackArray.s_g_Key_StrSign] == CTYLB_Comb_PackArray.s_strContainLayerPackSign):

                strEachContentArray = []

                strEachContentArray.append(origJson[CTYLB_Comb_PackArray.s_g_Key_Str_0])
                strEachContentArray.append(origJson[CTYLB_Comb_PackArray.s_g_Key_Str_1])
                strEachContentArray.append(origJson[CTYLB_Comb_PackArray.s_g_Key_Str_2])
                strEachContentArray.append(origJson[CTYLB_Comb_PackArray.s_g_Key_Str_3])

                for eachContent in strEachContentArray:
                    newBusisPackUnit = CTYLB_Busis_Packet( CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_NotKnown,
                                                           0, 0, 0, '')
                    if( newBusisPackUnit.ExactCombindData( eachContent)):
                        if( newBusisPackUnit.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_NullFiller):
                            pass
                        elif( newBusisPackUnit.s_iBusiCmdID == CTYLB_SvClt_Cmd_Base_bytes.s_iPackType_TaskType_MultiLayer):
                            subUnitUnPackArray = CTYLB_Comb_PackArray.ExactCombindData( newBusisPackUnit.s_strContent)
                            retBusisPackArray.extend( subUnitUnPackArray)
                        else:
                            retBusisPackArray.append( newBusisPackUnit)
                    else:
                        CTYLB_Log.ShowLog(1, 'PackArray',  'Error, exact data error.')
        except Exception as e:
            CTYLB_Log.ShowLog(1, 'PackArray2', str(e))
            pass

        return retBusisPackArray

# 主系统，杂项功能
# start by sk. 170204
class CTYLB_MainSys_MiscFunc:
    s_g_iSysType_Win = 1
    s_g_iSysType_Linux = 2
    s_g_iSysType_Other = 3
    # 设置控制台的兼容性
    # start by sk. 170204
    @staticmethod
    def SetConsoleCompatible():
        import sys, codecs, locale

        strStdoutEncode = sys.stdout.encoding
        strStderrEncoding = sys.stderr.encoding
        strGetPerferEncode = locale.getpreferredencoding()
        print(u'Console:[%s,%s,%s]' % (strStdoutEncode, strStderrEncoding, strGetPerferEncode))

        if strStdoutEncode.upper() != u'UTF-8':
            try:
                sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
            except Exception as e:
                print(u'setting stdout, Other unknown error %s' % (str(e)))
        if strStderrEncoding.upper() != u'UTF-8':
            try:
                sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf8', buffering=1)
            except Exception as e:
                print(u'setting stderr, Other unknown error %s' % (str(e)))
        pass

    # 检查管套的错误代码
    # start by sk. 170219
    @staticmethod
    def CheckSockErrorCode( errorException):
        bRetNeedCloseSocket = False
        bRetJustBusyNoError = False

        if (errorException.errno == 11):  # linux resource temporarily unavailable
            bRetJustBusyNoError = True
            pass
        elif (errorException.errno == 32):  # linux Broken pipe
            bRetNeedCloseSocket = True
            pass
        elif (errorException.errno == 35):  # connect ok. but no data
            # mac下ok，连接成功后处于此处ok
            bRetJustBusyNoError = True
        elif (errorException.errno == 50):  # network is down
            bRetNeedCloseSocket = True
            pass
        elif (errorException.errno == 54):  # reset by peer
            bRetNeedCloseSocket = True
            pass
        elif (errorException.errno == 57):  # socket connect not succ
            bRetNeedCloseSocket = True
            pass
        elif (errorException.errno == 60):  # operation timeout
            bRetNeedCloseSocket = True
        elif (errorException.errno == 61):  # connect refuse
            bRetNeedCloseSocket = True
        elif (errorException.errno == 104):  # linux, connect reset by peer.
            bRetNeedCloseSocket = True
        elif (errorException.errno == 110):  # linux, connect time out.
            bRetNeedCloseSocket = True
        elif (errorException.errno == 111):  # connect refuse
            bRetNeedCloseSocket = True
        elif (errorException.errno == 10035):
            bRetJustBusyNoError = True
        elif (errorException.errno == 10053):  # win, recv error.
            bRetNeedCloseSocket = True
        elif (errorException.errno == 10054):  # win, remote closed
            bRetNeedCloseSocket = True
        elif (errorException.errno == 10057):  # win, sock is not connected.
            bRetNeedCloseSocket = True
        else:
            bRetNeedCloseSocket = True
            CTYLB_Log.ShowLog(1, 'MiscFunc', 'unknown SocketEvent [%d] error:[%s]' % (errorException.errno, str(errorException)))

        return bRetNeedCloseSocket, bRetJustBusyNoError

    # 检查是否休眠足够时间
    # start by sk. 170226
    @staticmethod
    def CheckIdleTime( lastCheckTime, iIdleCount):
        bRetValue = False
        nowTime = datetime.now()
        timeDiff = nowTime-lastCheckTime
        if( timeDiff.seconds >= iIdleCount):
            bRetValue = True
        return bRetValue

    # 检查是否Win操作系统
    # start by sk. 170312
    @staticmethod
    def GetSystemType():
        import platform
        iRetSysType = 0
        sysstr = platform.system()
        if (sysstr == "Windows"):
            iRetSysType = CTYLB_MainSys_MiscFunc.s_g_iSysType_Win
        elif (sysstr == "Linux"):
            iRetSysType = CTYLB_MainSys_MiscFunc.s_g_iSysType_Linux
        else:
            iRetSysType = CTYLB_MainSys_MiscFunc.s_g_iSysType_Other
        return iRetSysType

    # 转成utf8字符串
    # start by sk. 170502
    @staticmethod
    def SafeGetUTF8(strOrigAllType):
        bstrRetUTF8 = strOrigAllType
        if( type(bstrRetUTF8) == str):
            bstrRetUTF8 = bstrRetUTF8.encode()
        return bstrRetUTF8

    # 转成unicode字符串
    # start by sk. 170502
    @staticmethod
    def SafeGetUnicode(strOrigAllType):
        bstrRetUnicode = strOrigAllType
        if( type(bstrRetUnicode) == bytes):
            bstrRetUnicode = bstrRetUnicode.decode()
        return bstrRetUnicode

    # 转成utf8字符串
    # start by sk. 170502
    @staticmethod
    def SafeGetUTF8Array(strOrigAllTypeArray):
        retUTF8Array = []
        for eachItem in strOrigAllTypeArray:
            bstrEachItem = CTYLB_MainSys_MiscFunc.SafeGetUTF8(eachItem)
            retUTF8Array.append(bstrEachItem)
        return retUTF8Array

    # 转成unicode字符串
    # start by sk. 170502
    @staticmethod
    def SafeGetUnicodeArray(strOrigAllTypeArray):
        retUnicodeArray = []
        for eachItem in strOrigAllTypeArray:
            ustrEachItem = CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachItem)
            retUnicodeArray.append(ustrEachItem)
        return retUnicodeArray

    # 比较两个不同类型字符串的值是否相等
    # start by sk. 170503
    @staticmethod
    def SafeCompareAnyStrValue(strAnyType1, strAnyType2):
        bRetValue = False
        type1 = type(strAnyType1)
        type2 = type(strAnyType2)
        if( type1 == type2):
            bRetValue = True if(strAnyType1 == strAnyType2) else False
        else:
            strUnicode1 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strAnyType1)
            strUnicode2 = CTYLB_MainSys_MiscFunc.SafeGetUnicode(strAnyType2)
            bRetValue = True if(strUnicode1 == strUnicode2) else False

        return bRetValue

    # 安全转换为base64的字符串
    # start by sk. 170929
    @staticmethod
    def SafeConvertStrToBase64(strOrigStr):
        ustrOrigStr = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strOrigStr)
        bstrBase64 = base64.b64encode(ustrOrigStr)
        ustrBase64Result = CTYLB_MainSys_MiscFunc.SafeGetUnicode(bstrBase64)
        return ustrBase64Result

    # 安全恢复 为base64 以前的字符串
    # start by sk. 170929
    @staticmethod
    def SafeRestoreFromBase64(strBase64Str, bExportUnicode=True):
        ustrOrigBase64Str = CTYLB_MainSys_MiscFunc.SafeGetUTF8(strBase64Str)
        bstrOrigStr = base64.b64decode(ustrOrigBase64Str)

        if( bExportUnicode):
            strResult = CTYLB_MainSys_MiscFunc.SafeGetUnicode(bstrOrigStr)
        else:
            strResult = bstrOrigStr
        return strResult

    # 显示详细的错误信息
    # start by sk. 170929
    @staticmethod
    def ShowExceptionInfo(exception_content):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("*** print sys.exc_info:")
        print('exc_type is: %s, exc_value is: %s, exc_traceback is: %s' % (exc_type, exc_value, exc_traceback))
        print("-" * 100)

        print("*** print_tb:")
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        print("-" * 100)

        print("*** print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
        print("-" * 100)

        print("*** print_exc:")
        traceback.print_exc()
        print("-" * 100)
        pass

    # 获得日期时间的字符串
    # start by sk. 171031
    @staticmethod
    def GetStr_From_DateTime(destDateTime, strHourSeperate='_'):
        strFormat = '%Y-%m-%d %H' + strHourSeperate + '%M' + strHourSeperate + '%S'
        datestr = destDateTime.strftime(strFormat)
        return datestr


    # 获得日期字符串对应的日期单元
    # start by sk. 171031
    @staticmethod
    def GetDateTime_From_Str(strDateTime):
        retDateTime = datetime.now()
        if( isinstance(strDateTime, datetime)):
            retDateTime = strDateTime
        else:
            strFormat = ''

            iLowLine_Pos = strDateTime.find('_')
            if( iLowLine_Pos == -1):
                iSeperateDot_Pos = strDateTime.find(':')
                if( iSeperateDot_Pos == -1):
                    pass
                else:
                    strFormat = '%Y-%m-%d %H:%M:%S'
            else:
                strFormat = '%Y-%m-%d %H_%M_%S'

            if(strFormat):
                try:
                    retDateTime = datetime.strptime(strDateTime, strFormat)
                except Exception as e:
                    pass
        return retDateTime
