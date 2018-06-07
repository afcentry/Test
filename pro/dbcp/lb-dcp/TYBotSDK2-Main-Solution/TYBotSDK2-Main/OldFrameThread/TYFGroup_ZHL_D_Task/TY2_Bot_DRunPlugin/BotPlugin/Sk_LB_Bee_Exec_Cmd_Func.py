# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_Bee_Exec_Cmd_Func.py
# 蜜蜂执行命令功能实现
#
# start by sk. 170105

import os
import platform
from datetime import datetime
import socket
import urllib.request
import struct
import re
from .Sk_LB_Cfg_RemoteClient import CSkLB_Config_RemoteClient_BaseDef
from .routeTracerManager import RouteTracerManager
from .dnsTracerManager import DnsTracerManager
from .domainIPDig import DomainIPDiger
from .NmapScaner import NmapScaner


def MyExecPrint(format, *args):
    try:
        print(format % args)
    except Exception as e:
        pass


class CTYLB_Sk_Plugin_BeeExecCmd:
    # 蜜蜂执行实现Ping结果
    # In [6]: Bee_Exec_PingCmd(['www.sina.com.cn','www.sohu.com','www.163.com'])
    # PING ara.sina.com.cn (58.63.236.248): 56 data bytes
    # 64 bytes from 58.63.236.248: icmp_seq=0 ttl=57 time=8.423 ms
    # --- ara.sina.com.cn ping statistics ---
    # 1 packets transmitted, 1 packets received, 0.0% packet loss
    # round-trip min/avg/max/stddev = 8.423/8.423/8.423/0.000 ms
    # True
    # PING fgz.a.sohu.com (14.18.240.6): 56 data bytes
    # 64 bytes from 14.18.240.6: icmp_seq=0 ttl=57 time=7.194 ms
    # start by sk. 170105
    @staticmethod
    def Bee_Exec_PingCmd(strDestHostArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for eachHost in strDestHostArray:
            if (IsGlobalStopExitFunc()):
                break

            strFilter = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes(eachHost)
            eachHost = strFilter
            if (len(eachHost) > 0):
                strResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_PingCmd_EachHost(eachHost)
                strExResultLineArray.append(strResult)
        return strExResultLineArray

    @staticmethod
    def Bee_Exec_PingCmd_EachHost(strHostName):
        strResult = ''
        if (len(strHostName) > 0):
            timeout = 500
            count = 1
            is_windows = platform.system() == "Windows"
            timeout = timeout if is_windows else timeout / 1000.0

            command = "ping -n %d -w %d %s" if is_windows else "ping -c %d -i %f %s"
            output = os.popen(command % (count, timeout, strHostName))
            strResult = output.read()
        return strResult

    @staticmethod
    def Bee_Exec_DnsDig(strDestHostArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for eachHost in strDestHostArray:
            if (IsGlobalStopExitFunc()):
                break

            strResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_DnsDig_EachHost(eachHost)
            strExResultLineArray.append(strResult)
        return strExResultLineArray

    @staticmethod
    def Bee_Exec_DnsDig_EachHost(strExecHost):
        dns = DnsTracerManager()
        jsonData = dns.trace(strExecHost)
        exactDnsInfo = dns.result_parse_json(jsonData)
        strResult = str(exactDnsInfo)
        return strResult

    # 蜜蜂执行实现爬虫结果
    #  格式为： --<>--http://orig.url/param--<>--exec-time--<>--
    #         --<<>>--urlline1--<<>>--
    #         另外一块数据
    # start by sk. 170107
    @staticmethod
    def Bee_Exec_WebCrawl(strDestURLArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for strEachURL in strDestURLArray:
            if (IsGlobalStopExitFunc()):
                break
            try:
                execTime = datetime.now()
                strExecTime = execTime.strftime('%Y-%m-%d %H:%M:%S')

                MyExecPrint('[%s] exec [%s]', strExecTime, strEachURL)

                iHTTPResponseStatus, strOrigWebServerType, strOrigContentType, strOrigCurURLTitle, iCurURLContentLength, \
                res_html1 = CSkNet1_Share_CrawlFunc.ExecCrawlURL(strEachURL)

                link_list = re.findall(r"(?<=href=\").+?(?=\")|(?<=href=\').+?(?=\')", res_html1)

                strWebServerType = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes(strOrigWebServerType)
                strContentType = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes(strOrigContentType)
                strCurURLTitle = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes(strOrigCurURLTitle)

                strCrawCMDContentArray = [CSkLB_Config_RemoteClient_BaseDef.g_str_CrawURL_Cmd_Line_Sign,
                                          str(len(link_list)),
                                          strExecTime, strEachURL, str(iHTTPResponseStatus), strWebServerType,
                                          strContentType,
                                          strCurURLTitle, str(iCurURLContentLength)]
                CSkNet1_Share_CrawlFunc.SkNetCraw_WriteArrayToContentLine(strExResultLineArray, strCrawCMDContentArray,
                                                                          CSkLB_Config_RemoteClient_BaseDef.g_str_CrawURL_Cmd_Seperate)
                urlArray = [CSkLB_Config_RemoteClient_BaseDef.g_str_CrawURL_Cmd_Result_Line_Sign]

                for url in link_list:
                    strFilter = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes(url)
                    urlArray.append(strFilter)
                CSkNet1_Share_CrawlFunc.SkNetCraw_WriteArrayToContentLine(strExResultLineArray, urlArray,
                                                                          CSkLB_Config_RemoteClient_BaseDef.g_str_CrawURL_Cmd_Result_Seperate)
            except Exception as e:  # EOFError
                print(e.message)
        return strExResultLineArray

    # 蜜蜂执行实现路由跟踪结果
    # start by sk. 170110
    @staticmethod
    def Bee_Exec_TraceRoute(strDestTraceRouteArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for eachHost in strDestTraceRouteArray:
            if (IsGlobalStopExitFunc()):
                break
            strFilter = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes(eachHost)
            eachHost = strFilter
            if (len(eachHost) > 0):
                curTime = datetime.now()
                strTime = curTime.strftime('%Y-%m-%d %H:%M:%S')

                MyExecPrint('[%s] exec Trace [%s]', strTime, eachHost)

                strTraceArray = [CSkLB_Config_RemoteClient_BaseDef.g_str_CrawURL_Cmd_Line_Sign, eachHost, strTime]
                CSkNet1_Share_CrawlFunc.SkNetCraw_WriteArrayToContentLine(strExResultLineArray, strTraceArray,
                                                                          CSkLB_Config_RemoteClient_BaseDef.g_str_CrawURL_Cmd_Seperate)
                managet = RouteTracerManager()
                # 执行路由跟踪任务
                strResult = managet.trace(eachHost)
                strExResultLineArray.append(strResult)
        return strExResultLineArray

    # 蜜蜂执行实现路由跟踪结果
    # start by sk. 170110
    @staticmethod
    def Bee_Exec_TraceRoute_EachHost(strHostName):
        managet = RouteTracerManager()
        # 执行路由跟踪任务
        strResult = managet.trace(strHostName)
        return strResult

    # 蜜蜂执行子域名挖掘结果
    # pk 2017年3月30日16:42:59
    @staticmethod
    def Bee_Exec_SubdomainDig(strDestTraceRouteArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for eachHost in strDestTraceRouteArray:
            if (IsGlobalStopExitFunc()):
                break
            strResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_SubdomainDig_EachHost(eachHost)
            strExResultLineArray.append(strResult)
        return strExResultLineArray

    # 蜜蜂执行子域名挖掘结果
    # pk 2017年3月30日16:42:59
    @staticmethod
    def Bee_Exec_SubdomainDig_EachHost(strHostName):
        # 执行子域名挖掘
        strResult = DomainIPDiger.GetSubdomain(domain=strHostName)
        return strResult

    # 蜜蜂执行域名解析IP结果
    # pk 2017年3月30日16:42:59
    @staticmethod
    def Bee_Exec_DomainIP(strDestTraceRouteArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for eachHost in strDestTraceRouteArray:
            if (IsGlobalStopExitFunc()):
                break
            strResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_DomainIP_EachHost(eachHost)
            strExResultLineArray.append(strResult)
        return strExResultLineArray

    # 蜜蜂执行域名解析IP结果
    # pk 2017年3月30日16:42:59
    @staticmethod
    def Bee_Exec_DomainIP_EachHost(strHostName):
        # 执行域名解析IP
        strResult = DomainIPDiger.GetIp(domain=strHostName)
        return strResult

    # 蜜蜂执行nmap扫描IP结果
    # 2017-05-10
    @staticmethod
    def Bee_Exec_NmapPortService(strArray, IsGlobalStopExitFunc):
        strExResultLineArray = []
        for eachIP in strArray:
            if (IsGlobalStopExitFunc()):
                break
            strResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_NmapPortService_EachHost(eachIP)
            strExResultLineArray.append(strResult)
        return strExResultLineArray

    # 蜜蜂执行nmap扫描IP结果
    # 2017-05-10
    @staticmethod
    def Bee_Exec_NmapPortService_EachHost(strIP):
        # 执行Nmap扫描
        strResult = NmapScaner.Scan(strIP)
        return strResult


# 爬虫共享功能
# start by sk. 170107
class CSkNet1_Share_CrawlFunc:
    # 获得本地网络主机名，和对外IP，物理地址描述
    #  ---
    # -- 返回值: 主机名，对外IP，物理地址
    # start by sk. 160409
    @staticmethod
    def SkNetCraw_GetLocalNetName():
        strHostName = socket.gethostname()
        strExIP = ''
        strExAddr = ''

        try:
            # 您的IP是：[113.99.102.205] 来自：广东省深圳市 电信</center></body></html>
            rep = urllib.request.urlopen('http://1212.ip138.com/ic.asp', timeout=30)
            data = rep.read()

            dataU = data.decode('gbk')
            iStartPos = dataU.find('[')
            if (iStartPos != -1):
                iEndPos = dataU.find(']', iStartPos)
                if (iEndPos != -1):
                    strExIP = dataU[iStartPos + 1: iEndPos]

                    # 在当前IP后面获取内容
                    strFind = u'来自：'
                    iStartPos = dataU.find(strFind)
                    iFindLen = len(strFind)
                    if (iStartPos != -1):
                        iEndPos = dataU.find('<', iStartPos)
                        if (iEndPos == -1):
                            strExAddr = dataU[iStartPos + iFindLen:]
                        else:
                            print('%d' % (iEndPos))
                            strExAddr = dataU[iStartPos + iFindLen: iEndPos]
                    # strExAddr = strExAddr.decode('gbk')
                    print(dataU)
                    print(strExAddr)
        except Exception as e:
            print(e)

        return strHostName, strExIP, strExAddr

    # 以行的方式，写入数组内容入文件
    #  fileDestWrite --- 目标文件
    #  arrLineArray --- 数组队列
    #  charSplit --- 分割的字符串
    # -- 返回值: 无
    # start by sk. 160409
    @staticmethod
    def SkNetCraw_WriteArrayToContentLine(virtualFileStrArray, arrLineArray, charSplit):
        strLine = charSplit.join(arrLineArray)
        try:
            strLine = strLine.encode('UTF-8', 'ignore')  # 避免出现编码错误
        except Exception as e:
            pass
        virtualFileStrArray.append(strLine)

    # 执行Ping命令
    #  strDomainName --- 域名的名字
    # -- 返回值: 主机名，IP字符串，IP值，返回时间，TTL。如果IP字符串长度=0，表示失败
    # start by sk. 160409
    @staticmethod
    def SkNetCraw_ExecPingCmd(strDomainName):
        strRetIP = ''
        strRetHostName = ''
        iRetTTL = 0
        iRetAverTime = 0
        iRetIP = 0

        timeout = 3
        is_windows = platform.system() == "Windows"
        timeout = timeout if is_windows else timeout / 1000.0
        command = "ping -n %d -w %d %s" if is_windows else "ping -c %d -i %f %s"
        output = os.popen(command % (2, timeout, strDomainName))
        strExec = output.read()

        # 格式有两种,
        iNameEnd = -1
        # 中文: 正在 Ping ara.sina.com.cn [121.14.1.189] 具有 32 字节的数据
        # 英文: Pinging www.hostname [1.1.1.1] with ...
        iPingPos = strExec.find('Pinging ')
        if (iPingPos != -1):  # 英文?
            iPingPos = strExec.find(' ') + 1
            iNameEnd = strExec.find(' ', iPingPos)
        else:
            iPingPos = strExec.find('Ping ')  # 中文?
            if (iPingPos != -1):
                iPingPos = iPingPos + 5
                iNameEnd = strExec.find(' ', iPingPos)

        if (iNameEnd != -1):
            strIPOrHostName = ""
            if (iNameEnd != -1):
                strIPOrHostName = strExec[iPingPos:iNameEnd]
            iQuotaStart = strExec.find('[', iNameEnd)
            if (iQuotaStart != -1):
                iQuotaEnd = strExec.find(']', iQuotaStart)
                if (iQuotaEnd != -1):
                    strRetIP = strExec[iQuotaStart + 1: iQuotaEnd]
                    strRetHostName = strIPOrHostName
            else:  # 没有 [ ]
                strRetIP = strIPOrHostName

                # 找TTL
                iTTLPos = strExec.find('TTL=', iNameEnd)
                if (iTTLPos != -1):
                    iLineEnd = strExec.find('\n', iTTLPos)
                    if (iLineEnd != -1):
                        strTTL = strExec[iTTLPos + 4: iLineEnd]
                        strTTL.replace('\r', '')
                        iRetTTL = int(strTTL)

                        iAverTimePos = strExec.rfind('ms')
                        if (iAverTimePos != -1):
                            iEquPos = strExec.rfind('=')
                            if (iEquPos != -1):
                                strAverTime = strExec[iEquPos + 1: iAverTimePos]
                                iRetAverTime = int(strAverTime)

        if (len(strRetIP) > 0):
            print('Name:[' + strRetHostName + '] IP:' + strRetIP)
            iRetIP, iReverseIP = CSkNet1_Share_CrawlFunc.SkNetDB_ConvertStrToIPReverseIP(strRetIP);

        return strRetHostName, strRetIP, iRetIP, iRetAverTime, iRetTTL

    # 将字符串 转成 IP 和反转IP值
    #  strIP --- 要操作的字符串
    # -- 返回值: IP值，和反转IP值
    # start by sk. 160402
    @staticmethod
    def SkNetDB_ConvertStrToIPReverseIP(strIP):
        iRetIP = 0
        iReverseIP = 0
        try:
            iRetIP = socket.ntohl(struct.unpack("I", socket.inet_aton(strIP))[0])  # ip address to int
            iReverseIP = socket.ntohl(iRetIP)
        except Exception as e:
            print(e)
            print('str to ip err:' + strIP)

        return iRetIP, iReverseIP

    # 执行爬取URL，获得各种结果值
    # start by sk. 170109
    @staticmethod
    def ExecCrawlURL(strURL):
        req1 = urllib2.Request(strURL)
        req1.add_header('User-Agent',
                        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0')
        # 执行，获得URL内容
        iHTTPResponseStatus = 0
        strCurURLTitle = ""
        res_html1 = ""

        try:
            res1 = urllib2.urlopen(req1, timeout=30)
            res_html1 = res1.read()
        except urllib2.HTTPError as e:
            iHTTPResponseStatus = e.code
        except urllib2.URLError as e:
            iHTTPResponseStatus = 400
        except Exception as e:  # unknown
            iHTTPResponseStatus = 400

        try:
            strWebServerType = res1.headers['server']
            strContentType = res1.headers['content-type']
        except Exception as e:
            strWebServerType = ''
            strContentType = ''

        strUpperURLData = res_html1.upper()
        iTitleStartPos = strUpperURLData.find('<TITLE>')
        if (iTitleStartPos != -1):
            iTitleStartPos = iTitleStartPos + 7
            iTitleEndPos = strUpperURLData.find('</TITLE>', iTitleStartPos)
            if (iTitleEndPos != -1):
                strCurURLTitle = res_html1[iTitleStartPos: iTitleEndPos]
        iCurURLContentLength = len(res_html1)

        return iHTTPResponseStatus, strWebServerType, strContentType, strCurURLTitle, iCurURLContentLength, res_html1

    pass
