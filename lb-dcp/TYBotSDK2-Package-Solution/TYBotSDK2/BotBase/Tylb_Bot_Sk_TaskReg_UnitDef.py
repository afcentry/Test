# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Sk_TaskReg_UnitDef.py 任务通信共享 定义
#
# start by sk. 170213
# start by sk. 180315. 升级到V3，采用json方式处理

from datetime import datetime

from .Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_ExCall_SubClient import CTYLB_P2P_ContentUnit_Base
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_MainSys_MiscFunc
import json

class CTYLB_TaskReg_Cmd_BaseDef:
    s_g_iSubCmd_Sample = 101  # 请求主机状态

# ################################################################################################
#   重写 内容单元类，客户端内容自定义
#    通用的数据格式,  主命令，s_g_iMainCmd_CommonTask_SingleData
#           s_g_iSubCmd_CommonTask_SingleData # 子命令。
#   命令包含：数据格式类型，数据值
# start by sk. 170220
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_CommonData(CTYLB_P2P_ContentUnit_Base):
    # s_iRunPluginID = 0  # 要运行的插件ID, 在 code_bot_exec／Sk_LB_Cfg_RemoteClient.py 的 CSkLB_Config_RemoteClient_BaseDef 中定义
    s_g_iType_Unknown = 0
    s_g_iType_int = 1
    s_g_iType_string = 2
    s_g_iType_IntArray = 3
    s_g_iType_StrArray = 4

    # 下面是不同节点之间，传递的通用Int值，value的不同含义。
    s_g_iIntValue_Task_Start_Run = 1  # [插件执行主机->任务中心->提交者] 任务启动, strParam1=任务标识串
    s_g_iIntValue_Task_Finish = 2  # [插件执行主机->任务中心->提交者] 任务完成, strParam1=任务标识串
    s_g_iIntValue_Task_BCast_Fail_No_Host = 3  # [任务中心->提交者] 广播任务失败，没有主机可以执行, strParam1=任务标识串
    s_g_iIntValue_Task_Finish_Fail = 4  # [插件执行主机->任务中心->提交者] 任务完成，但是失败了 strParam1=任务标识串
    s_g_iIntValue_Query_PluginID_Run_ParamBlock_Count = 5  # [提交者->任务中心] 查询插件ID可以发送执行的参数个数. strParam1=插件ID
    s_g_iIntValue_Reply_PluginID_Run_ParamBlock_Count = 6  # [任务中心->提交者] 插件ID可以执行的参数个数. strParam1=插件ID， strParam2=参数个数
    s_g_iIntValue_Query_DExecHost_Send_Result_Count = 7         # [任务中心->执行插件主机] 查询完成的结果单元个数。strParam1=最大可发送个数。
    s_g_iIntValue_Reply_DExecHost_Contain_Result = 8    # [执行插件主机->任务中心] 回复我现有的结果单元个数, strParam1=还剩下的结果个数, strParam2=请求包的标识
    s_g_iIntValue_Request_TaskCenter_Send_Promptor_Result_Count = 9        # [提交者->任务中心] 查询我的结果单元个数. strParam1=最大申请个数。－1表示不限
    s_g_iIntValue_Reply_TaskCenter_Send_Promptor_Result_Finish = 10        # [任务中心->提交者] 返回当前提交者的结果个数。strParam1=结果个数, strParam2=请求包标识符

    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_CommonTask_SingleData, CTYLB_Bot_BaseDef.s_g_iSubCmd_CommonTask_SingleData)
        self.s_iType = CTYBot_CTUnit_CommonData.s_g_iType_Unknown  # 数据类型
        self.s_strValue = ''
        self.s_iValue = 0
        self.s_strParam1 = ''   # 附加参数1
        self.s_strParam2 = ''   # 附加参数2
        pass

    def SetIntData(self, iValue):
        self.s_iType = CTYBot_CTUnit_CommonData.s_g_iType_int
        self.s_iValue = iValue

    def SetStrData(self, strValue):
        self.s_iType = CTYBot_CTUnit_CommonData.s_g_iType_string
        self.s_strValue = strValue

    def SetParam(self, strParam1, strParam2):
        self.s_strParam1 = strParam1
        self.s_strParam2 = strParam2


    s_g_strUniqueSign = '@@32!234ka'

    s_g_Key_iType = 'iType'
    s_g_Key_strValue = 'strValue'
    s_g_Key_iValue = 'iValue'
    s_g_Key_strParam1 = 'strParam1'
    s_g_Key_strParam2 = 'strParam2'
    s_g_Key_strSign = 'strSign'
    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[CTYBot_CTUnit_CommonData.s_g_Key_strSign] = self.s_g_strUniqueSign
        exDict[CTYBot_CTUnit_CommonData.s_g_Key_iType] = self.s_iType
        exDict[CTYBot_CTUnit_CommonData.s_g_Key_strValue] = self.s_strValue
        exDict[CTYBot_CTUnit_CommonData.s_g_Key_strParam1] = self.s_strParam1
        exDict[CTYBot_CTUnit_CommonData.s_g_Key_strParam2] = self.s_strParam2
        exDict[CTYBot_CTUnit_CommonData.s_g_Key_iValue] = self.s_iValue

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)


    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if( exDict[CTYBot_CTUnit_CommonData.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iType = exDict[CTYBot_CTUnit_CommonData.s_g_Key_iType]
                self.s_strValue = exDict[CTYBot_CTUnit_CommonData.s_g_Key_strValue]
                self.s_strParam1 = exDict[CTYBot_CTUnit_CommonData.s_g_Key_strParam1]
                self.s_strParam2 = exDict[CTYBot_CTUnit_CommonData.s_g_Key_strParam2]
                self.s_iValue = exDict[CTYBot_CTUnit_CommonData.s_g_Key_iValue]

        except:
            pass
        pass

# tylb－p2p的 实际调用，新建通用数据单元
# start by sk. 170220
def CTYBot_CTUnit_Common_CreateNewUnit_CommonData():
    newContentUnit = CTYBot_CTUnit_CommonData()
    return newContentUnit

# ################################################################################################
#   重写 定义新的内容单元，实现 任务注册中心－获得分配web主机名块－任务 输入调用
#    任务登记中心数据类型,  主命令，登记我状态，现在跑了多少了。s_g_iMainCmd_TaskRegCenter_ReportMyStatus
#           s_g_iSubCmd_TaskRegCenter_ReportMyStatus_None # 子命令，登记状态。
# ################################################################################################
# tylb－p2p的 实际调用，新建实际使用的P2P内容单元 CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock
# start by sk. 170221
def CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignWebNameBlock():
    newContentUnit = CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock()
    return newContentUnit

# ################################################################################################
#   重写 内容单元类，客户端内容自定义
#    任务参数分配Web队列,  主命令，s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock
#           s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock # 子命令。
#   命令包含：插件ID，web名字队列
# start by sk. 170220
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_TaskRegCenter_Assign_WebNameBlock(CTYLB_P2P_ContentUnit_Base):
    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Assign_WebNameBlock, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Assign_WebNameBlock)
        self.s_iRunPluginID = 0  # 要运行的插件ID, 在 code_bot_exec／Sk_LB_Cfg_RemoteClient.py 的 CSkLB_Config_RemoteClient_BaseDef 中定义
        self.s_strDomainNameArray = []  # 域名队列
        pass

    s_g_strUniqueSign = '@@3kkk34ka'

    s_g_Key_iRunPluginID = 'iPluginID'
    s_g_Key_strDomainNameArray = 'strDomainArray'
    s_g_Key_strSign = 'strSign'

    s_g_strDomainJoin = '___##___'

    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign
        exDict[self.s_g_Key_iRunPluginID] = self.s_iRunPluginID
        exDict[self.s_g_Key_strDomainNameArray] = self.s_g_strDomainJoin.join(self.s_strDomainNameArray)

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iRunPluginID = exDict[self.s_g_Key_iRunPluginID]
                self.s_g_strDomainJoin = exDict[self.s_g_Key_strDomainNameArray].split(self.s_g_strDomainJoin)
        except:
            pass
        pass

# ################################################################################################
#   重写 内容单元类，客户端内容自定义
#    回复Web名字的字符串结果,  主命令，s_g_iMainCmd_TaskRegCenter_Reply_WebName_Result_StrBlock
#           s_g_iSubCmd_TaskRegCenter_Reply_WebName_Result_StrBlock # 子命令。
#   命令包含：插件ID，web名字队列
# start by sk. 170220
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_TaskRegCenter_Reply_WebName_Result_StrBlock(CTYLB_P2P_ContentUnit_Base):
    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Reply_WebName_Result_StrBlock, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Reply_WebName_Result_StrBlock)
        self.s_iRunPluginID = 0  # 当前运行的插件ID, 在 code_bot_exec／Sk_LB_Cfg_RemoteClient.py 的 CSkLB_Config_RemoteClient_BaseDef 中定义
        self.s_strRequestDomain = ''   # 执行的域名
        self.s_strExecResult = ''  # 结果内容
        pass


    s_g_strUniqueSign = '@@3kss34ka'

    s_g_Key_iRunPluginID = 'iPluginID'
    s_g_Key_strRequestDomain = 'strRequestDomain'
    s_g_Key_strExecResult = 'strExecResult'
    s_g_Key_strSign = 'strSign_raw234123x'

    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign
        exDict[self.s_g_Key_iRunPluginID] = self.s_iRunPluginID
        exDict[self.s_g_Key_strRequestDomain] = self.s_strRequestDomain
        exDict[self.s_g_Key_strExecResult] = self.s_strExecResult

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iRunPluginID = exDict[self.s_g_Key_iRunPluginID]
                self.s_strRequestDomain = exDict[self.s_g_Key_strRequestDomain]
                self.s_strExecResult = exDict[self.s_g_Key_strExecResult]
        except:
            pass
        pass

# ################################################################################################
#   重写 内容单元类，客户端内容自定义
#    任务登记中心数据类型,  主命令，登记我状态，现在跑了多少了。s_g_iMainCmd_TaskRegCenter_ReportMyStatus
#           s_g_iSubCmd_TaskRegCenter_ReportMyStatus_None # 子命令，登记状态。
#   命令包含：支持运算ID，能够接收的命令数，当前正在运算的数量
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_TaskRegCenter_ReportMyStatus(CTYLB_P2P_ContentUnit_Base):
    s_g_strPluginIDSplit = '$#'
    s_g_strFormatDateTime = '%y-%m-%d %H:%M:%S'

    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportMyStatus, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportMyStatus_None)
        self.s_iSupportPluginIDArray = []  # 当前支持的插件ID
        self.s_iCanRecvTaskCount = 0  # 可以接收的任务数
        self.s_iCurRunCount = 0  # 当前正在运算的数量
        self.s_iCurWaitCount = 0  # 当前等待的个数
        self.s_curSendDateTime = datetime.now()
        pass

    # 把插件ID队列转成str
    def __ConvPluginIDArrayStr(self):
        strIDArray = []
        for iEachID in self.s_iSupportPluginIDArray:
            strIDArray.append( str(iEachID))

        strTotalIDArray = self.s_g_strPluginIDSplit.join(strIDArray)
        return strTotalIDArray

    # 把字符串还原成插件ID
    def __SetPluginIDArrayFromStr(self, strTotalID):
        self.s_iSupportPluginIDArray = []

        strIDArray = strTotalID.split(self.s_g_strPluginIDSplit)
        for eachStr in strIDArray:
            self.s_iSupportPluginIDArray.append( int(eachStr))

    s_g_strUniqueSign = '@@3kss34ka_taskCenterReportStatus'

    s_g_Key_iSupportPluginIDArray = 'iSupportPluginIDArray'
    s_g_Key_iCanRecvTaskCount = 'iCanRecvTaskCount'
    s_g_Key_iCurRunCount = 'iCurRunCount'
    s_g_Key_iCurWaitCount = 'iCurWaitCount'
    s_g_Key_strCurSendDateTime = 'strCurSendDateTime'

    s_g_Key_strSign = 'strSign_taskCenterReportStatus'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_iSupportPluginIDArray] = self.__ConvPluginIDArrayStr()
        exDict[self.s_g_Key_iCanRecvTaskCount] = self.s_iCanRecvTaskCount
        exDict[self.s_g_Key_iCurRunCount] = self.s_iCurRunCount
        exDict[self.s_g_Key_iCurWaitCount] = self.s_iCurWaitCount
        exDict[self.s_g_Key_strCurSendDateTime] = self.s_curSendDateTime.strftime( self.s_g_strTimeTransFormat)

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.__SetPluginIDArrayFromStr( exDict[self.s_g_Key_iSupportPluginIDArray])
                self.s_iCanRecvTaskCount = int(exDict[self.s_g_Key_iCanRecvTaskCount])
                self.s_iCurRunCount = int(exDict[self.s_g_Key_iCurRunCount])
                self.s_iCurWaitCount = int(exDict[self.s_g_Key_iCurWaitCount])
                self.s_curSendDateTime = datetime.strptime(exDict[self.s_g_Key_strCurSendDateTime],self.s_g_strTimeTransFormat)
        except:
            pass
        pass

    # 判断此单元是否 相同的值
    def IsUnitSameCountValue(self, checkUnit):
        bSame = False

        if( self.s_iCanRecvTaskCount == checkUnit.s_iCanRecvTaskCount):
            if (self.s_iCurRunCount == checkUnit.s_iCurRunCount):
                if (self.s_iCurWaitCount == checkUnit.s_iCurWaitCount):
                    bSame = True
        return bSame

    # 从单元中复制值
    def CopyValueFromUnit(self, destEquUnit):
        self.s_iSupportPluginIDArray = []  # 当前支持的插件ID
        self.s_iSupportPluginIDArray.extend( destEquUnit.s_iSupportPluginIDArray)
        self.s_iCanRecvTaskCount = destEquUnit.s_iCanRecvTaskCount  # 可以接收的任务数
        self.s_iCurRunCount = destEquUnit.s_iCurRunCount  # 当前正在运算的数量
        self.s_iCurWaitCount = destEquUnit.s_iCurWaitCount  # 当前等待的个数
        self.s_curSendDateTime = destEquUnit.s_curSendDateTime
        pass

# tylb－p2p的 实际调用，新建实际使用的P2P内容单元
# start by sk. 170310
def CTYBot_CTUnit_CreateNew_ReportMyStatus():
    newContentUnit = CTYBot_CTUnit_TaskRegCenter_ReportMyStatus()
    return newContentUnit


# ################################################################################################
#   重写 内容单元类，分配任务参数
#    任务登记中心数据类型,  主命令，分配任务。s_g_iMainCmd_TaskRegCenter_AssignTask
#           s_g_iSubCmd_TaskRegCenter_AssignTask_Multi # 子命令，分配任务。
#   命令包含：分配任务，任务类型，参数内容
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_TaskRegCenter_AssignTaskParam(CTYLB_P2P_ContentUnit_Base):

    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_AssignTask, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_AssignTask_Param)
        self.s_iCmdType = 0
        self.s_iPluginID_PathType = 0
        self.s_strFileName = ''
        self.s_strContent = ''
        self.s_strOrigRequester = ''
        pass

    s_g_strUniqueSign = '@@3kss34ka_taskRegCenter_assignTaskParam'

    s_g_Key_iCmdType = 'iCmdType'
    s_g_Key_iPluginID_PathType = 'iPluginID_PathType'
    s_g_Key_strFileName = 'strFileName'
    s_g_Key_strContent = 'strContent'
    s_g_Key_strOrigRequester = 'strOrigRequester'

    s_g_Key_strSign = 'strSign_taskRegCenter_assignTaskParam'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_iCmdType] = self.s_iCmdType
        exDict[self.s_g_Key_iPluginID_PathType] = self.s_iPluginID_PathType
        exDict[self.s_g_Key_strFileName] = self.s_strFileName
        exDict[self.s_g_Key_strContent] = self.s_strContent
        exDict[self.s_g_Key_strOrigRequester] = self.s_strOrigRequester

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iCmdType = int(exDict[self.s_g_Key_iCmdType])
                self.s_iPluginID_PathType = int(exDict[self.s_g_Key_iPluginID_PathType])
                self.s_strFileName = exDict[self.s_g_Key_strFileName]
                self.s_strContent = exDict[self.s_g_Key_strContent]
                self.s_strOrigRequester = exDict[self.s_g_Key_strOrigRequester]
        except:
            pass
        pass


# tylb－p2p的 实际调用，新建实际使用的P2P内容单元
# start by sk. 170310
def CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_AssignTaskParam():
    newContentUnit = CTYBot_CTUnit_TaskRegCenter_AssignTaskParam()
    return newContentUnit


# ################################################################################################
#   重写 内容单元类，报告结果
#    任务登记中心数据类型,  主命令，分配任务。s_g_iMainCmd_TaskRegCenter_ReportResult
#           s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl # 子命令，分配任务。
#   命令包含：分配任务，任务类型，参数内容
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_TaskRegCenter_ReportResult(CTYLB_P2P_ContentUnit_Base):
    def __init__(self, iPluginID=0, strRunResult='', strDomainName='', strOrigTaskUniqueSign=''):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl)
        self.s_iExecPluginID = iPluginID    # 执行插件ID
        self.s_strRunResult = strRunResult   # 运行结果内容
        self.s_strExecDomainName = strDomainName  # 任务运行的主机单元
        self.s_strOrigTaskUniqueSign = strOrigTaskUniqueSign  # 源开始任务的唯一标识
        pass


    s_g_strUniqueSign = '@@3kss34ka_taskRegCenter_reportResult'

    s_g_Key_s_iExecPluginID = 's_iExecPluginID'
    s_g_Key_s_strRunResult = 's_strRunResult'
    s_g_Key_s_strExecDomainName = 's_strExecDomainName'
    s_g_Key_s_strOrigTaskUniqueSign = 's_strOrigTaskUniqueSign'

    s_g_Key_strSign = 'strSign_taskRegCenter_reportResult'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_s_iExecPluginID] = self.s_iExecPluginID
        exDict[self.s_g_Key_s_strRunResult] = self.s_strRunResult
        exDict[self.s_g_Key_s_strExecDomainName] = self.s_strExecDomainName
        exDict[self.s_g_Key_s_strOrigTaskUniqueSign] = self.s_strOrigTaskUniqueSign

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iExecPluginID = int(exDict[self.s_g_Key_s_iExecPluginID])
                self.s_strRunResult = exDict[self.s_g_Key_s_strRunResult]
                self.s_strExecDomainName = exDict[self.s_g_Key_s_strExecDomainName]
                self.s_strOrigTaskUniqueSign = exDict[self.s_g_Key_s_strOrigTaskUniqueSign]
        except:
            pass
        pass


# ################################################################################################
#   重写 内容单元类，报告结果, 一个单元内有多个结果内容
#    任务登记中心数据类型,  主命令，分配任务。s_g_iMainCmd_TaskRegCenter_ReportResult
#           s_g_iSubCmd_TaskRegCenter_ReportResult_PingTraceWebCrawl # 子命令，分配任务。
#   命令包含：分配任务，任务类型，参数内容
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################

# 子结果单元，支持对字符串的转换，和读入
# start by sk. 170223
class CTYBot_ReportResultV2_SubResultUnit:
    def __init__(self, iPluginID=0, strRunResult='', strDomainName=''):
        self.s_iExecPluginID = iPluginID  # 执行插件ID
        self.s_strRunResult = strRunResult  # 运行结果内容
        self.s_strExecDomainName = strDomainName  # 任务运行的主机单元


    s_g_strUniqueSign = '@@3kss34ka_subResultUnit'

    s_g_Key_s_iExecPluginID = 's_iExecPluginID'
    s_g_Key_s_strRunResult = 's_strRunResult'
    s_g_Key_s_strExecDomainName = 's_strExecDomainName'

    s_g_Key_strSign = 'strSign_subResultUnit'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def ToTotalString(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_s_iExecPluginID] = self.s_iExecPluginID
        exDict[self.s_g_Key_s_strRunResult] = self.s_strRunResult
        exDict[self.s_g_Key_s_strExecDomainName] = self.s_strExecDomainName

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def ReadFromTotalString(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iExecPluginID = int(exDict[self.s_g_Key_s_iExecPluginID])
                self.s_strRunResult = exDict[self.s_g_Key_s_strRunResult]
                self.s_strExecDomainName = exDict[self.s_g_Key_s_strExecDomainName]
        except:
            pass
        pass

# 结果报告单元V2，支持多个子单元
# start by sk. 170223
# start by sk. 180315. 升级到V3，采用json方式处理
class CTYBot_CTUnit_TaskRegCenter_ReportResult_V2(CTYLB_P2P_ContentUnit_Base):
    s_g_strItemSplit = '_#@as#47pk+2_'  # 每个单元之间联合的内容

    def __init__(self, strOrigTaskUniqueSign=''):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_ReportResult_V2, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_ReportResult_V2_PingTraceWebCrawl)
        self.s_strOrigTaskUniqueSign = strOrigTaskUniqueSign  # 源开始任务的唯一标识
        self.s_subResultUnitArray = []  # 结果单元队列
        pass

    # 把单元队列转成字符串
    def ConvertSubResultUnitToTotalString(self):
        strSubUnitArray = []
        for eachUnit in self.s_subResultUnitArray:
            strEach = eachUnit.ToTotalString()
            strSubUnitArray.append( strEach)
        strExUnitTotal = self.s_g_strItemSplit.join( strSubUnitArray)
        return strExUnitTotal

    # 增加结果单元
    def AddSubResultUnit(self, iPluginID, bstrDomain, bstrResult):
        strNewUnit = CTYBot_ReportResultV2_SubResultUnit( iPluginID, bstrResult, bstrDomain)
        self.s_subResultUnitArray.append( strNewUnit)


    s_g_strUniqueSign = '@@3kss34ka_taskRegCenter_reportResult_v2'

    s_g_Key_s_subResultUnitArray = 's_subResultUnitArray'
    s_g_Key_s_strOrigTaskUniqueSign = 's_strOrigTaskUniqueSign'

    s_g_Key_strSign = 'strSign_taskRegCenter_reportResult_v2'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_s_subResultUnitArray] = self.ConvertSubResultUnitToTotalString()
        exDict[self.s_g_Key_s_strOrigTaskUniqueSign] = self.s_strOrigTaskUniqueSign

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_strOrigTaskUniqueSign = exDict[self.s_g_Key_s_strOrigTaskUniqueSign]
                self.s_subResultUnitArray = []

                strSubUnitArray = exDict[self.s_g_Key_s_subResultUnitArray].split(self.s_g_strItemSplit)
                for strEachSubUnit in strSubUnitArray:
                    newSubUnit = CTYBot_ReportResultV2_SubResultUnit()
                    if( newSubUnit.ReadFromTotalString( strEachSubUnit)):
                        self.s_subResultUnitArray.append( newSubUnit)
        except:
            pass
        pass

# tylb－p2p的 实际调用，新建实际使用的P2P内容单元
# start by sk. 170223
def CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_V2_ReportResult():
    newContentUnit = CTYBot_CTUnit_TaskRegCenter_ReportResult_V2()
    return newContentUnit

# tylb－p2p的 实际调用，新建实际使用的P2P内容单元
# start by sk. 170213
def CTYBot_CTUnit_TaskRegCenter_CreateNewUnit_ReportResult():
    newContentUnit = CTYBot_CTUnit_TaskRegCenter_ReportResult()
    return newContentUnit

# ################################################################################################
#   任务管理中心，状态查询
#    任务登记中心数据类型,  主命令，分配任务。s_g_iMainCmd_TaskRegCenter_ReportMangStatus
#           s_g_iSubCmd_TaskRegCenter_ReportMangStatus # 子命令，分配任务。
#   命令包含：分配任务，任务类型，参数内容
# start by sk. 180315. 升级到V3，采用json方式处理
# ################################################################################################
class CTYBot_CTUnit_TaskRegCenter_ReportMangStatus(CTYLB_P2P_ContentUnit_Base):
    def __init__(self):
        CTYLB_P2P_ContentUnit_Base.__init__(self, CTYLB_Bot_BaseDef.s_g_iDataType_TaskRegCenter_sk_v1)
        self.self_SetCmd( CTYLB_Bot_BaseDef.s_g_iMainCmd_TaskRegCenter_Reply_ReportMangStatus, CTYLB_Bot_BaseDef.s_g_iSubCmd_TaskRegCenter_Reply_ReportMangStatus)
        self.s_iTotalFreeCount = 0  # 总的自由任务数量
        self.s_iOnLineTotalHostCount = 0  # 总的在线主机个数
        self.s_iTotalWaitCount = 0  # 总的等待运行个数
        pass


    s_g_strUniqueSign = '@@3kss34ka_TaskRegCenter_ReportMangStatus'

    s_g_Key_s_iTotalFreeCount = 's_iTotalFreeCount'
    s_g_Key_s_iOnLineTotalHostCount = 's_iOnLineTotalHostCount'
    s_g_Key_s_iTotalWaitCount = 's_iTotalWaitCount'

    s_g_Key_strSign = 'strSign_TaskRegCenter_ReportMangStatus'


    # 子类必须重写，被基类调用 － 把自身数据，封装输出到外部单元
    # restart by sk. 180315
    def subClass_Call_BuildExWriteContent(self):
        exDict = {}
        exDict[self.s_g_Key_strSign] = self.s_g_strUniqueSign

        exDict[self.s_g_Key_s_iTotalFreeCount] = self.s_iTotalFreeCount
        exDict[self.s_g_Key_s_iOnLineTotalHostCount] = self.s_iOnLineTotalHostCount
        exDict[self.s_g_Key_s_iTotalWaitCount] = self.s_iTotalWaitCount

        self.s_strExternalContent = json.dumps(exDict, ensure_ascii=False)

    # 子类必须重写，被基类调用 － 从接收到的内容，填充自身内容
    # restart by sk. 180315
    def subClassReWrite_Call_FillContent(self, strExJsonContent):
        try:
            exDict = json.loads(strExJsonContent)

            if (exDict[self.s_g_Key_strSign] == self.s_g_strUniqueSign):
                self.s_iTotalFreeCount = int(exDict[self.s_g_Key_s_iTotalFreeCount])
                self.s_iOnLineTotalHostCount = exDict[self.s_g_Key_s_iOnLineTotalHostCount]
                self.s_iTotalWaitCount = exDict[self.s_g_Key_s_iTotalWaitCount]
        except:
            pass
        pass
