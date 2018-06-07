# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_p2p_share.py p2p功能的基本共享文件
#
# start by sk. 170123
# update by sk. 170429, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式

from datetime import datetime
import struct
import socket
import time
import base64
import json
import requests
import sys, traceback

g_chCmdPackSign_bytes = 'PW'.encode()  # 命令包的标志
# start by sk. 160502
g_strDataStartSign_bytes = '$#memat-dekl$#'.encode()
g_iMaxExecIdleCount = 50  # 最大的执行休眠次数

# 日志信息显示
# start by sk. 170203
class CTYLB_Log:
    MonitorConsoleURL="http://localhost:8889"
    MonitorURL="http://localhost:8889"
    PostTimeout = 1
    MONITOR_TABLE_TYPE_UNMAN_STATUS="status-table"
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
        strShowTotalUnicode = u'%s <%s> [%s] %s' % (strShowPrefix, strUnicodeRangeName, strTime, strUnicodeMsg)

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
    def ShowMonitorTable(table_id, row, column, value,table_type=MONITOR_TABLE_TYPE_UNMAN_STATUS):
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

    @staticmethod
    def ShowWebCMDResult(result_type, result_text):
        msgData = {}
        msgData['type'] = 'unman-web-cmd-result'
        msgData['data'] = {}
        msgData['data']["result_type"] = result_type
        msgData['data']["result_text"] = result_text
        try:
            dataStr = json.dumps(msgData).encode()
            base64Data = base64.b64encode(dataStr)
            r = requests.post(url=CTYLB_Log.MonitorURL, data=base64Data, timeout=CTYLB_Log.PostTimeout)
        except Exception as e:
            # print("[!]Error:Send monitor data failed:{}".format(e))
            pass

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


    # 检查是否休眠足够休眠时间
    # start by sk. 180414
    @staticmethod
    def CheckIdleMilSecondTime( lastCheckTime, iIdleMilSecondCount):
        bRetValue = False
        nowTime = datetime.now()
        timeDiff = nowTime-lastCheckTime
        if( timeDiff.microseconds >= iIdleMilSecondCount):
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

    # 获得两个时间的差别
    @staticmethod
    def GetTwoDateTimeDiffNum(datetime_new, datetime_old):
        timeDiff = datetime_new - datetime_old
        hour = timeDiff.seconds / 3600
        mins = timeDiff.seconds % 3600
        min = mins / 60
        sec = mins % 60

        return hour, min, sec, timeDiff.seconds

    # 执行调度过程中的休息。返回是否要退出
    # start by sk. 171210
    @staticmethod
    def ExecRunRelax( iExecSleepRunCount, bTaskBusy, funcIsGlobalExit):
        bContinueRunning = True
        retiExecSleepRunCount = iExecSleepRunCount

        # 空闲，等待1秒钟，随时可以中断退出
        if (bTaskBusy):
            retiExecSleepRunCount += 1
            if ((iExecSleepRunCount % 100) == 0):
                time.sleep(0.1)
        else:
            retiExecSleepRunCount = 0
            waitCheckTime = datetime.now()

            bRunning = True
            while (bRunning):
                if (funcIsGlobalExit and funcIsGlobalExit()):
                    bContinueRunning = False
                    break
                if (CTYLB_MainSys_MiscFunc.CheckIdleTime(waitCheckTime, 1)):
                    break
                time.sleep(0.1)

        return retiExecSleepRunCount, bContinueRunning

    # 将IP值转成字符串
    #  iIP --- 目标IP值
    # -- 返回值: str IP的字符串
    # start by sk. 160403
    @staticmethod
    def GetIP_Str(iIP):
        iIntIP = int(iIP)
        strIP = socket.inet_ntoa(struct.pack("!I", iIntIP))  # IP int to string
        return strIP

    # 将字符串转成数值
    #  strIP --- 目标IP值
    # -- 返回值: int IP
    # start by sk. 171011
    @staticmethod
    def GetIP_Int(strIP):
        iIP = 0

        try:
            iIP = socket.ntohl(struct.unpack("I", socket.inet_aton(strIP))[0])  # ip address to int
        except Exception as e:
            print('convert ip %s error' % (strIP))
            CTYLB_MainSys_MiscFunc.ShowExceptionInfo(e)
        return iIP



class CSkBot_Common_Share():
    def __init__(self):
        pass

    # 对时间进行检查
    # start by sk. 1880406
    class CSkBot_TimeIdentify():
        def __init__(self, iShowSecond=5):
            self.s_initStartTime = datetime.now()
            self.s_lastCheckTime = datetime.now()
            self.s_iShowSecond = iShowSecond

        def CheckShow(self):
            bRetValue = False
            if (CTYLB_MainSys_MiscFunc.CheckIdleTime(self.s_lastCheckTime, self.s_iShowSecond)):
                self.s_lastCheckTime = datetime.now()
                bRetValue = True
            return bRetValue

        def CheckTimeDiff(self):
            return self.CheckShow()

        def ResetToNow(self):
            self.s_lastCheckTime = datetime.now()

        def GetStartTimeDiff(self):
            return datetime.now() - self.s_initStartTime

    # 对时间进行毫秒级检查
    # start by sk. 180414
    class CSkBot_MilTimeIdentify():
        def __init__(self, iDiffMilSecond=1000):
            self.s_initStartTime = datetime.now()
            self.s_lastCheckTime = datetime.now()
            self.s_iDiffMilSecond = iDiffMilSecond

        def CheckTimeDiff(self):
            bRetValue = False
            if (CTYLB_MainSys_MiscFunc.CheckIdleMilSecondTime(self.s_lastCheckTime, self.s_iDiffMilSecond)):
                self.s_lastCheckTime = datetime.now()
                bRetValue = True
            return bRetValue

        def ResetToNow(self):
            self.s_lastCheckTime = datetime.now()

        def GetStartTimeDiff(self):
            return datetime.now() - self.s_initStartTime
