# -*- coding:UTF-8 -*- 放到第一行标记
# Sk_LB_Cfg_RemoteClient.py
# 配置相关，远程客户端定义
#
# start by sk. 170105

import configparser
import io

##############################################################
# 操作Ini文件的雷
# start by sk. 160430. copy from internet
##############################################################
class CTY_IniFile:
    def __init__(self, filename):
        self.filename = filename
        self.initflag = False
        self.cfg = None
        self.readhandle = None

    def __del__(self):
        self.UnInit()

    def Init(self):
        self.cfg = ConfigParser.ConfigParser()
        try:
            self.readhandle = open(self.filename, 'r')
            self.cfg.readfp(self.readhandle)
            self.initflag = True
        except:
            self.initflag = False
        return self.initflag

    def UnInit(self):
        if self.initflag:
            self.readhandle.close()

    def GetValue(self, Section, Key, Default = ""):
        try:
            value = self.cfg.get(Section, Key)
        except:
            value = Default
        return value
    '''
    def SetValue(self, Section, Key, Value):
        try:
            self.cfg.set(Section, Key, Value)
        except:
            self.cfg.add_section(Section)
            self.cfg.set(Section, Key, Value)
            self.cfg.write(self.writehandle)
    '''

# 远程客户端配置。
# start by sk. 170105
class CSkLB_Config_RemoteClient_BaseDef:
    g_str_CrawURL_Cmd_Seperate = '--<>--'  # 爬取url命令的间隔
    g_str_CrawURL_Cmd_Result_Seperate = '-<><>@@#<><>-'  # 爬取url结果命令的间隔
    g_str_CrawURL_Cmd_Line_Sign = '!!##$$Craw$$##!!'   # 爬取URL命令的开始字符串
    g_str_CrawURL_Cmd_Result_Line_Sign = '%#@!^^%##@@MFR##'   # 爬取URL命令结果的开始字符串

    s_iExec_PingCmd = 1  # 需要执行Ping命令
    s_iExec_PingCmd_Reply = 2  # 执行Ping命令 回复
    s_iExec_Web_Crawl = 3   # 需要执行Web爬虫
    s_iExec_Web_Crawl_Reply = 4   # 需要执行Web爬虫  回复
    s_iExec_Tracert = 5   # 需要执行路由跟踪
    s_iExec_Tracert_Reply = 6   # 需要执行路由跟踪 回复
    s_iExec_DigDNS = 7   # 执行dns获取
    s_iExec_DigDNS_Reply = 8   # 执行dns获取 回复

    s_iExec_Enterprise_Name = 100   #获取企业名称
    s_iExec_Enterprise_Name_Reply = 101    #获取企业名称 回复
    s_iExec_Enterprise_Domain_Name = 102    #根据企业名称获取企业域名
    s_iExec_Enterprise_Domain_Name_Reply = 103    #根据企业名称获取企业域名 回复


    s_iExec_SubdomainDig=501   #子域名挖掘
    s_iExec_SubdomainDig_Reply=502   #子域名挖掘 回复

    s_iExec_DomainIP=503   #域名获取IP
    s_iExec_DomainIP_Reply=504   #域名获取IP 回复

    s_strEachUnit_Split = "#@@#"

    s_strFileFirstLineSeperate = "=@#$%"   # 文件第一行间隔
    s_strCmdLineSign = "$$%~##"
    s_strNeedExecHeaderSign = "need_exec"   # 需要执行的文件头标记

    g_strZipPasswd = "3$3@3$AA-bbxCCddEE"

    s_strResultFile_FileLineSeperate = "%#@R$"   # 结果文件第一行标识
    s_g_LineEnter = '\r\n'

    # 获得命令文件第一行
    # start by sk, 170105
    @staticmethod
    def GetCmdFileFirstLine():
        return CSkLB_Config_RemoteClient_BaseDef.s_strFileFirstLineSeperate

    # 综合内容到一个数据包
    # start by sk, 170105
    @staticmethod
    def CombCmdContentToPacket(iEachRecID, iType, iSubPathType, strFileName, strContent):
        strExecLineContentArray = [CSkLB_Config_RemoteClient_BaseDef.s_strCmdLineSign, str(iEachRecID), str(iType),
                                   str(iSubPathType), strFileName, strContent]
        strFullLine = CSkLB_Config_RemoteClient_BaseDef.s_strFileFirstLineSeperate.join(strExecLineContentArray)
        return strFullLine

    # 判断数据包是否我们的命令文件格式
    # start by sk, 170105
    @staticmethod
    def IsFileMyCmdFormat( strFile):
        bRetValue = False
        with open(strFile, "r") as curFile:
            bRetValue = CSkLB_Config_RemoteClient_BaseDef.__RealCheck_IsFilePtrMyCmdFormat( curFile)
        return bRetValue

    # 判断数据包是否我们的命令文件格式
    # start by sk, 170105
    @staticmethod
    def IsBuffContent_MyCmdFormat( strContent):
        tmpFileIO = io.StringIO()
        tmpFileIO.write( strContent)
        bRetValue = CSkLB_Config_RemoteClient_BaseDef.__RealCheck_IsFilePtrMyCmdFormat(tmpFileIO)
        return bRetValue

    # 判断数据包是否我们的命令文件格式
    # start by sk, 170105
    @staticmethod
    def __RealCheck_IsFilePtrMyCmdFormat( fileObject):
        bRetValue = False
        strFirstLine = fileObject.readline()
        strAdjustFirstLine = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes( strFirstLine)
        if( strAdjustFirstLine == CSkLB_Config_RemoteClient_BaseDef.GetCmdFileFirstLine()):
            bRetValue = True
        return bRetValue


    # 去除一行字符串的回车等杂字符
    # start by sk, 170106
    @staticmethod
    def FilterLineStrEnterBytes( strLine):
        strRet = strLine.strip()
        strFilterChars = ['\r', '\n']
        for eachSubStr in strFilterChars:
            str2 = strRet.replace(eachSubStr, "")
            strRet = str2
        return strRet

    # 判断数据包是否我们的命令结果文件格式
    # start by sk, 170105
    @staticmethod
    def IsFileMyCmdResultFormat( strFile):
        bRetValue = False
        with open(strFile, "r") as curFile:
            strFirstLine = curFile.readline()
            strAdjustFirstLine = CSkLB_Config_RemoteClient_BaseDef.FilterLineStrEnterBytes( strFirstLine)
            if( strAdjustFirstLine == CSkLB_Config_RemoteClient_BaseDef.GetCmdResultFileFirstLine()):
                bRetValue = True
        return bRetValue

    # 从综合内容中提取数据包
    # start by sk, 170105
    @staticmethod
    def ExactCmdContentFromBuffer( strBuffContent):
        iRetEachRecID, iRetType, iRetSubPathType = 0, 0, 0
        strRetCurUnitName, strRetContent = '', ''

        if( CSkLB_Config_RemoteClient_BaseDef.IsBuffContent_MyCmdFormat( strBuffContent)):
            tmpFileIO = io.StringIO()
            tmpFileIO.write(strBuffContent)
            iRetEachRecID, iRetType, iRetSubPathType, strRetCurUnitName, strRetContent = CSkLB_Config_RemoteClient_BaseDef.__RealExec_ExactCmdContentFromOp(
                tmpFileIO)
        return iRetEachRecID, iRetType, iRetSubPathType, strRetCurUnitName, strRetContent

    # 从综合内容中提取数据包
    # start by sk, 170105
    @staticmethod
    def ExactCmdContentFromFile( strFile):
        iRetEachRecID, iRetType, iRetSubPathType = 0, 0, 0
        strRetCurUnitName, strRetContent = '', ''

        with open(strFile, "r") as curFile:
            if( CSkLB_Config_RemoteClient_BaseDef.IsFileMyCmdFormat(strFile)):
                iRetEachRecID, iRetType, iRetSubPathType, strRetCurUnitName, strRetContent = CSkLB_Config_RemoteClient_BaseDef.__RealExec_ExactCmdContentFromOp( curFile)
        return iRetEachRecID, iRetType, iRetSubPathType, strRetCurUnitName, strRetContent

    # 真正实现 提取内容命令
    # start by sk, 170213
    @staticmethod
    def __RealExec_ExactCmdContentFromOp( fileOpUnit):
        iRetEachRecID, iRetType, iRetSubPathType = 0, 0, 0
        strRetCurUnitName, strRetContent = '', ''

        strFirstLine = fileOpUnit.readline()
        strContentLine = fileOpUnit.readline()
        destSplitArray = strContentLine.split( CSkLB_Config_RemoteClient_BaseDef.s_strFileFirstLineSeperate)
        if( (len(destSplitArray) >= 6) and (destSplitArray[0] == CSkLB_Config_RemoteClient_BaseDef.s_strCmdLineSign)):
            iRetEachRecID = int(destSplitArray[1])
            iRetType = int(destSplitArray[2])
            iRetSubPathType = int(destSplitArray[3])
            strRetCurUnitName = destSplitArray[4]
            strRetContent = destSplitArray[5]
        return iRetEachRecID, iRetType, iRetSubPathType, strRetCurUnitName, strRetContent

    # 把执行命令数据包写入文件
    # start by sk, 170105
    @staticmethod
    def Write_ExecCmdPacket_To_File( strFullPathFileName, iRecID, iType, iSubPathType, strRandFileName, strContent):
        newFile = open(strFullPathFileName, "wb")
        newFile.write(CSkLB_Config_RemoteClient_BaseDef.GetCmdFileFirstLine())
        newFile.write(CSkLB_Config_RemoteClient_BaseDef.s_g_LineEnter)
        strPacketContent = CSkLB_Config_RemoteClient_BaseDef.CombCmdContentToPacket( iRecID, iType, iSubPathType, strRandFileName, strContent)
        newFile.write(strPacketContent)
        newFile.write(CSkLB_Config_RemoteClient_BaseDef.s_g_LineEnter)
        newFile.close()

    # 把执行命令结果数据包写入文件
    # start by sk, 170105
    @staticmethod
    def GetCmdResultFileFirstLine( ):
        return CSkLB_Config_RemoteClient_BaseDef.s_strResultFile_FileLineSeperate

    # 把执行命令结果数据包写入文件
    # start by sk, 170105
    @staticmethod
    def Write_ExecCmdResult_To_File( strFullPathFileName, iRecID, iType, iSubPathType, strRandFileName, strResultLineArray):
        with open(strFullPathFileName, "wb") as newFile:
            strFileContent = CSkLB_Config_RemoteClient_BaseDef.Write_ExecCmdResult_To_Buffer(iRecID, iType, iSubPathType, strRandFileName, strResultLineArray)
            newFile.write(strFileContent)
            newFile.close()
        pass

    # 把执行命令结果数据包写入缓冲
    # start by sk, 170215
    @staticmethod
    def Write_ExecCmdResult_To_Buffer( iRecID, iType, iSubPathType, strRandFileName, strResultLineArray):
        strRetBuff = ''
        strRetBuff += CSkLB_Config_RemoteClient_BaseDef.GetCmdResultFileFirstLine()
        strRetBuff += CSkLB_Config_RemoteClient_BaseDef.s_g_LineEnter
        strPacketContent = CSkLB_Config_RemoteClient_BaseDef.CombCmdContentToPacket( iRecID, iType, iSubPathType, strRandFileName, "")
        strRetBuff += strPacketContent
        strRetBuff += CSkLB_Config_RemoteClient_BaseDef.s_g_LineEnter
        for eachLine in strResultLineArray:
            strRetBuff += eachLine
            strRetBuff += CSkLB_Config_RemoteClient_BaseDef.s_g_LineEnter
        return strRetBuff

    # 从综合内容中提取数据包
    # start by sk, 170105
    @staticmethod
    def ExactCmdContentFromCmdResultFile( strFile):
        iRetEachRecID = 0
        iRetType = 0
        iRetSubPathType = 0
        strRetCurUnitName = ""
        strExecResultContent = ""

        if( CSkLB_Config_RemoteClient_BaseDef.IsFileMyCmdResultFormat(strFile)):
            with open(strFile, "r") as curFile:
                strFirstLine = curFile.readline()
                strContentLine = curFile.readline()
                strExecResultContent = curFile.read()
                destSplitArray = strContentLine.split( CSkLB_Config_RemoteClient_BaseDef.s_strFileFirstLineSeperate)
                if( (len(destSplitArray) >= 6) and (destSplitArray[0] == CSkLB_Config_RemoteClient_BaseDef.s_strCmdLineSign)):
                    iRetEachRecID = int(destSplitArray[1])
                    iRetType = int(destSplitArray[2])
                    iRetSubPathType = int(destSplitArray[3])
                    strRetCurUnitName = destSplitArray[4]
        return iRetEachRecID, iRetType, iRetSubPathType, strRetCurUnitName, strExecResultContent

