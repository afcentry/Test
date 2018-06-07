# FiberMangReal.py
# 纤程管理实现
# start by sk. 180413

from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CTYLB_MainSys_MiscFunc, CSkBot_Common_Share
import time, json, random

g_lLastInstanceID=0  # 最后的唯一ID

# 初始化消息
class Fiber_MessageID:
    FMID_Init=1  # 单元初始化
    FMID_Close=2  # 单元关闭
    FMID_RemoteReplyMsgExecResult=3  # 远端返回执行结果, strMsgParam=UID, strJsonParam=s_strRetValue=FiberMsgRet的json
    FMID_Ping=4  # 执行Ping.自动回应. 各个参数都返回

# 消息执行完后的返回结果
class FiberMsgRet:
    s_g_key_iExecResult="iExecResult"
    s_g_key_strRetValue="strRetValue"
    s_g_key_strRetJsonValue="strRetJsonValue"
    s_g_key_lRetValue="lRetValue"
    s_g_key_lRetValue2="lRetValue2"

    s_g_iExecResult_Fail=-1  # 失败
    s_g_iExecResult_Normal=0 # 正常运行，返回
    s_g_iExecResult_PostMessage=1 # 正常运行, PostMessage方式
    s_g_iExecResult_Remote_Wait_Reply=2 # 发送到远程，等待延迟返回。s_strRetValue=唯一ID
    s_g_iExecResult_Remote_Reply=3 # 远程返回。

    def __init__(self, iExecResult=0, strRetValue="", strRetJsonValue="", lRetValue=0, lRetValue2=0):
        self.s_iExecResult = iExecResult
        self.s_strRetValue = strRetValue
        self.s_strRetJsonValue = strRetJsonValue
        self.s_lRetValue = lRetValue
        self.s_lRetValue2 = lRetValue2

    @staticmethod
    def BuildUniqueStr(strFromName, strDestName):
        strRet="[%s]-[%s]-[%d]-[%d]" % (strFromName, strDestName, random.randint(10,10000000), random.randint(10,10000000))
        return strRet

    def SetResult_To_RemoteExec(self, strFromName, strDestName):
        self.s_iExecResult=self.s_g_iExecResult_Remote_Wait_Reply
        self.s_strRetValue=self.BuildUniqueStr(strFromName, strDestName)

    def ImportFromComuRunMsgUnit(self, runMessageUnit):
        self.s_iExecResult = runMessageUnit.s_iRunResult

        self.s_strRetValue, self.s_strRetJsonValue = runMessageUnit.RetriveOrigStrContent()

        self.s_lRetValue = runMessageUnit.s_lMsgParam1
        self.s_lRetValue2 = runMessageUnit.s_lMsgParam2

    def ExportToStr(self):
        exDict={
            self.s_g_key_iExecResult: self.s_iExecResult,
            self.s_g_key_strRetValue: self.s_strRetValue,
            self.s_g_key_strRetJsonValue:self.s_strRetJsonValue,
            self.s_g_key_lRetValue: self.s_lRetValue,

            self.s_g_key_lRetValue2: self.s_lRetValue2,
        }

        strTotal=json.dumps(exDict, ensure_ascii=True)
        return strTotal
        pass

    def ImportFromStr(self, strContent):
        bRet=False
        try:
            dictContent = json.loads(strContent)

            strTryKey = self.s_g_key_iExecResult
            if (strTryKey in dictContent.keys()):
                self.s_iExecResult = int(dictContent[strTryKey])
            strTryKey = self.s_g_key_strRetValue
            if (strTryKey in dictContent.keys()):
                self.s_strRetValue = dictContent[strTryKey]
            strTryKey = self.s_g_key_strRetJsonValue
            if (strTryKey in dictContent.keys()):
                self.s_strRetJsonValue = dictContent[strTryKey]
            strTryKey = self.s_g_key_lRetValue
            if (strTryKey in dictContent.keys()):
                self.s_lRetValue = int(dictContent[strTryKey])

            strTryKey = self.s_g_key_lRetValue2
            if (strTryKey in dictContent.keys()):
                self.s_lRetValue2 = int(dictContent[strTryKey])

            bRet=True
        except Exception as e:
            #CTYLB_Log.ShowLog(1, "comu-fiber-list load msg error", str(e))
            CTYLB_MainSys_MiscFunc.ShowExceptionInfo(e)

        return bRet


# 节点之间通信，运行消息的单元
class CUTRC_NATs_Comu_RunMessageUnit:
    s_g_str_strFromFbUnit_FullName = "strFromFbUnit_FullName"
    s_g_str_strFromFbUnit_StrParam = "strFromFbUnit_StrParam"
    s_g_str_lFromFbUnit_lParam1 = "lFromFbUnit_lParam1"
    s_g_str_lFromFbUnit_lParam2 = "lFromFbUnit_lParam2"

    s_g_str_strDestFbUnit_FullName = "strDestFbUnit_FullName"
    s_g_str_strDestFbUnit_StrParam = "strDestFbUnit_StrParam"
    s_g_str_lDestFbUnit_lParam1 = "lDestFbUnit_lParam1"
    s_g_str_lDestFbUnit_lParam2 = "lDestFbUnit_lParam2"

    s_g_str_strGlobalMsg_UID = "strGlobalMsg_UID"

    s_g_str_iRun_MessageID = "iRun_MessageID"

    s_g_str_iRunResult = "iRunResult"

    s_g_str_strMsgJsonParam_ExBase64 = "strMsgJsonParam_ExBase64"
    s_g_str_strMsgParam_ExBase64 = "strMsgParam_ExBase64"

    s_g_str_lMsgParam1 = "lMsgParam1"
    s_g_str_lMsgParam2 = "lMsgParam2"

    def __init__(self):
        self.Clear()
        pass

    def LoadFromStr(self, strContent):
        bRet=False
        self.Clear()

        try:
            dictContent = json.loads(strContent)

            strTryKey = self.s_g_str_strFromFbUnit_FullName
            if (strTryKey in dictContent.keys()):
                self.s_strFromFbUnit_FullName = dictContent[strTryKey]
            strTryKey = self.s_g_str_strFromFbUnit_StrParam
            if (strTryKey in dictContent.keys()):
                self.s_strFromFbUnit_StrParam = dictContent[strTryKey]
            strTryKey = self.s_g_str_lFromFbUnit_lParam1
            if (strTryKey in dictContent.keys()):
                self.s_lFromFbUnit_lParam1 = int(dictContent[strTryKey])
            strTryKey = self.s_g_str_lFromFbUnit_lParam2
            if (strTryKey in dictContent.keys()):
                self.s_lFromFbUnit_lParam2 = int(dictContent[strTryKey])

            strTryKey = self.s_g_str_strDestFbUnit_FullName
            if (strTryKey in dictContent.keys()):
                self.s_strDestFbUnit_FullName = dictContent[strTryKey]
            strTryKey = self.s_g_str_strDestFbUnit_StrParam
            if (strTryKey in dictContent.keys()):
                self.s_strDestFbUnit_StrParam = dictContent[strTryKey]
            strTryKey = self.s_g_str_lDestFbUnit_lParam1
            if (strTryKey in dictContent.keys()):
                self.s_lDestFbUnit_lParam1 = int(dictContent[strTryKey])
            strTryKey = self.s_g_str_lDestFbUnit_lParam2
            if (strTryKey in dictContent.keys()):
                self.s_lDestFbUnit_lParam2 = int(dictContent[strTryKey])

            strTryKey = self.s_g_str_iRun_MessageID
            if (strTryKey in dictContent.keys()):
                self.s_iRun_MessageID = int(dictContent[strTryKey])

            strTryKey = self.s_g_str_strMsgJsonParam_ExBase64
            if (strTryKey in dictContent.keys()):
                self.s_strMsgJsonParam_ExBase64 = dictContent[strTryKey]

            strTryKey = self.s_g_str_strMsgParam_ExBase64
            if (strTryKey in dictContent.keys()):
                self.s_strMsgParam_ExBase64 = dictContent[strTryKey]

            strTryKey = self.s_g_str_lMsgParam1
            if (strTryKey in dictContent.keys()):
                self.s_lMsgParam1 = int(dictContent[strTryKey])
            strTryKey = self.s_g_str_lMsgParam2
            if (strTryKey in dictContent.keys()):
                self.s_lMsgParam2 = int(dictContent[strTryKey])

            strTryKey = self.s_g_str_strGlobalMsg_UID
            if (strTryKey in dictContent.keys()):
                self.s_strGlobalMsg_UID = dictContent[strTryKey]
            strTryKey = self.s_g_str_iRunResult
            if (strTryKey in dictContent.keys()):
                self.s_iRunResult = int(dictContent[strTryKey])

            bRet=True
        except Exception as e:
            #CTYLB_Log.ShowLog(1, "comu-fiber-list load msg error", str(e))
            CTYLB_MainSys_MiscFunc.ShowExceptionInfo(e)

        return bRet


    def ExportToStr(self):
        exDict={
            self.s_g_str_strFromFbUnit_FullName: self.s_strFromFbUnit_FullName,
            self.s_g_str_strFromFbUnit_StrParam: self.s_strFromFbUnit_StrParam,
            self.s_g_str_lFromFbUnit_lParam1:self.s_lFromFbUnit_lParam1,
            self.s_g_str_lFromFbUnit_lParam2: self.s_lFromFbUnit_lParam2,

            self.s_g_str_strDestFbUnit_FullName: self.s_strDestFbUnit_FullName,
            self.s_g_str_strDestFbUnit_StrParam: self.s_strDestFbUnit_StrParam,
            self.s_g_str_lDestFbUnit_lParam1: self.s_lDestFbUnit_lParam1,
            self.s_g_str_lDestFbUnit_lParam2: self.s_lDestFbUnit_lParam2,

            self.s_g_str_iRun_MessageID: self.s_iRun_MessageID,
            self.s_g_str_strMsgJsonParam_ExBase64: self.s_strMsgJsonParam_ExBase64,
            self.s_g_str_strMsgParam_ExBase64: self.s_strMsgParam_ExBase64,

            self.s_g_str_lMsgParam1: self.s_lMsgParam1,
            self.s_g_str_lMsgParam2: self.s_lMsgParam2,

            self.s_g_str_strGlobalMsg_UID: self.s_strGlobalMsg_UID,
            self.s_g_str_iRunResult: self.s_iRunResult,
        }

        strTotal=json.dumps(exDict, ensure_ascii=True)
        return strTotal

    def Clear(self):
        self.s_strGlobalMsg_UID=""  # 全局唯一ID
        self.s_iRunResult = 0  # 运行结果

        self.s_strFromFbUnit_FullName = ""
        self.s_strFromFbUnit_StrParam=""
        self.s_lFromFbUnit_lParam1=0
        self.s_lFromFbUnit_lParam2=0

        self.s_strDestFbUnit_FullName = ""
        self.s_strDestFbUnit_StrParam=""
        self.s_lDestFbUnit_lParam1=0
        self.s_lDestFbUnit_lParam2=0

        self.s_iRun_MessageID = 0

        self.s_strMsgJsonParam_ExBase64=""
        self.s_strMsgParam_ExBase64=""
        self.s_lMsgParam1=0
        self.s_lMsgParam2=0

        self.s_strMsgJsonParam_Orig=""
        self.s_strMsgParam_Orig=""

        pass

    # 根据原有内容，和消息执行结果，构建返回内容
    def Build_From_Orig_MsgRetResult(self, fromComuUnit, msgRetResult):
        self.s_strGlobalMsg_UID = fromComuUnit.s_strGlobalMsg_UID  # 全局唯一ID

        self.s_strFromFbUnit_FullName = fromComuUnit.s_strFromFbUnit_FullName
        self.s_strFromFbUnit_StrParam = fromComuUnit.s_strFromFbUnit_StrParam
        self.s_lFromFbUnit_lParam1 = fromComuUnit.s_lFromFbUnit_lParam1
        self.s_lFromFbUnit_lParam2 = fromComuUnit.s_lFromFbUnit_lParam2

        self.s_strDestFbUnit_FullName = fromComuUnit.s_strDestFbUnit_FullName
        self.s_strDestFbUnit_StrParam = fromComuUnit.s_strDestFbUnit_StrParam
        self.s_lDestFbUnit_lParam1 = fromComuUnit.s_lDestFbUnit_lParam1
        self.s_lDestFbUnit_lParam2 = fromComuUnit.s_lDestFbUnit_lParam2

        self.s_iRun_MessageID = fromComuUnit.s_iRun_MessageID

        if(msgRetResult):
            self.s_iRunResult = msgRetResult.s_iExecResult  # 运行结果

            self.s_strMsgJsonParam_ExBase64 = CTYLB_MainSys_MiscFunc.SafeConvertStrToBase64(msgRetResult.s_strRetJsonValue)
            self.s_strMsgParam_ExBase64 = CTYLB_MainSys_MiscFunc.SafeConvertStrToBase64(msgRetResult.s_strRetValue)

            self.s_strMsgJsonParam_Orig = msgRetResult.s_strRetJsonValue
            self.s_strMsgParam_Orig = msgRetResult.s_strRetValue

            self.s_lMsgParam1 = msgRetResult.s_lRetValue
            self.s_lMsgParam2 = msgRetResult.s_lRetValue2
        else:
            self.s_iRunResult = 0
            self.s_strMsgJsonParam_ExBase64 = ""
            self.s_strMsgParam_ExBase64 = ""
            self.s_lMsgParam1 = 0
            self.s_lMsgParam2 = 0
        pass

    # 设置内容
    def SetContent_FromFiberUnit(self, fromFiberUnit):
        self.s_strFromFbUnit_FullName = fromFiberUnit.s_strFullTaskName
        self.s_strFromFbUnit_StrParam=fromFiberUnit.s_strTaskParam
        self.s_lFromFbUnit_lParam1=fromFiberUnit.s_lTaskParam1
        self.s_lFromFbUnit_lParam2=fromFiberUnit.s_lTaskParam2
        pass

    def SetContent_MsgContent(self, lMsgID, strJsonParam, strParam, lParam1, lParam2):
        self.s_iRun_MessageID = lMsgID

        self.s_strMsgJsonParam_ExBase64= CTYLB_MainSys_MiscFunc.SafeConvertStrToBase64(strJsonParam)
        self.s_strMsgParam_ExBase64=CTYLB_MainSys_MiscFunc.SafeConvertStrToBase64(strParam)

        self.s_strMsgJsonParam_Orig = strJsonParam
        self.s_strMsgParam_Orig = strParam

        self.s_lMsgParam1=lParam1
        self.s_lMsgParam2=lParam2

    def SetContent_DestFiberUnit(self, strDestFullName, strDestParam, lDestParam1, lDestParam2):
        self.s_strDestFbUnit_FullName = strDestFullName
        self.s_strDestFbUnit_StrParam=strDestParam
        self.s_lDestFbUnit_lParam1=lDestParam1
        self.s_lDestFbUnit_lParam2=lDestParam2

    # 导出原始内容。
    # start by sk. 180417
    def RetriveOrigStrContent(self):
        strOrigJson = CTYLB_MainSys_MiscFunc.SafeRestoreFromBase64(self.s_strMsgJsonParam_ExBase64)
        strOrigStrParam = CTYLB_MainSys_MiscFunc.SafeRestoreFromBase64(self.s_strMsgParam_ExBase64)

        return strOrigStrParam, strOrigJson


# 纤程单元的管理
class FiberMang:
    def __init__(self):
        self.s_dictUIDFiberTasks={}  # 唯一ID对应的任务字典。 key=long, 内容=FiberUnit_Base
        self.s_dictStrParamFiberTasks={} # 字符串纤程任务字典. key=string, 内容=FiberUnit_Base
        self.s_dictLongLongParamFiberTasks={}  # 长参数任务字典. key=string, 内容=FiberUnit_Base


        self.s_listPostMsgStore=[]  # postMessge的队列

        self.s_iMaxContinueFreeCount=10  # 空闲10次就大休眠一次
        self.s_iLastContinueFreeCount=0  # 上次连续休眠的时间
        self.s_iFreeIdleMilSecond=1000 # 休眠的等待时间
        self.s_bNeedSleep=False

        self.s_listFiberTaskUnit=[]  # 任务单元队列
        self.s_lastFreeMilTimeDiff=CSkBot_Common_Share.CSkBot_MilTimeIdentify(self.s_iFreeIdleMilSecond) # 空闲检查

        self.s_store_listNeedSendRemoteMsgTask=[]  # 存储需要发送到远程任务 CUTRC_NATs_Comu_RunMessageUnit
        self.s_bUnitDictModified=False # 单元字典有否改变?

        pass

    # PostMessage时，存储消息的对象
    class CMsgPostStoreUnit:
        def __init__(self, senderFiberUnit, lTaskUID, strDestTaskFullName,
                     strTaskParm, lTaskParam1, lTaskParam2,
                     lMessageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):

            self.s_senderRequestUnit = senderFiberUnit

            self.s_lDestTaskUID = lTaskUID
            self.s_strDestTaskFullName=strDestTaskFullName

            self.s_strTaskParam=strTaskParm
            self.s_lTaskParam1=lTaskParam1
            self.s_lTaskParam2=lTaskParam2

            self.s_lMessageID = lMessageID
            self.s_strMsgParam = strMsgParam
            self.s_lMsgParam1 = lMsgParam1
            self.s_lMsgParam2 = lMsgParam2
            self.s_strMsgJsonParam = strMsgJsonParam


            # 获得下一个可用的唯一ID


    @staticmethod
    def GetUniqueInstanceID():
        global g_lLastInstanceID

        g_lLastInstanceID+=1
        return g_lLastInstanceID

    # 获得总的Fb单元个数
    def GetTotalFbUnitCount(self):
        return len(self.s_dictUIDFiberTasks)

    # 增加运行单元
    def AddTaskToDict(self, fiberUnit):
        bUpdate=False

        if(fiberUnit.s_lUniqueID not in self.s_dictUIDFiberTasks.keys()):
            self.s_dictUIDFiberTasks[fiberUnit.s_lUniqueID] = fiberUnit
            bUpdate=False

        strStrParamKey, strStrLongParamKey = FiberMang.GetTaskKey(
            fiberUnit.s_strFullTaskName, fiberUnit.s_strTaskParam,
            fiberUnit.s_lTaskParam1, fiberUnit.s_lTaskParam2 )
        if(strStrParamKey):
            if(strStrParamKey not in self.s_dictStrParamFiberTasks.keys()):
                self.s_dictStrParamFiberTasks[strStrParamKey] = fiberUnit
                bUpdate=True
        if(strStrLongParamKey):
            if(strStrLongParamKey not in self.s_dictLongLongParamFiberTasks.keys()):
                self.s_dictLongLongParamFiberTasks[strStrLongParamKey]=fiberUnit
                bUpdate=True
        if(bUpdate):
            self.s_bUnitDictModified=True


    # 从队列中移除单元
    def RemoveTaskFromDict(self, fiberUnit):
        bUpdate=False

        if(fiberUnit.s_lUniqueID in self.s_dictUIDFiberTasks.keys()):
            self.s_dictUIDFiberTasks.pop( fiberUnit.s_lUniqueID)
            bUpdate=True

        strStrParamKey, strStrLongParamKey = FiberMang.GetTaskKey(
            fiberUnit.s_strFullTaskName, fiberUnit.s_strTaskParam,
            fiberUnit.s_lTaskParam1, fiberUnit.s_lTaskParam2 )

        if(strStrParamKey):
            if(strStrParamKey in self.s_dictStrParamFiberTasks.keys()):
                self.s_dictStrParamFiberTasks.pop(strStrParamKey)
                bUpdate=True

        if(strStrLongParamKey):
            if(strStrLongParamKey in self.s_dictStrParamFiberTasks.keys()):
                self.s_dictLongLongParamFiberTasks.pop(strStrLongParamKey)
                bUpdate=True
        if(bUpdate):
            self.s_bUnitDictModified=True

    # 获得并且重置上次修改的状态
    def Pop_Reset_LastModifyFlag(self):
        bRet=False

        if(self.s_bUnitDictModified):
            bRet=True
            self.s_bUnitDictModified=False
        return bRet

    def TimerCheck(self):
        bRetValue, bExecRunTask=False, False

        if(self.s_iLastContinueFreeCount>=self.s_iMaxContinueFreeCount):
            if(self.s_lastFreeMilTimeDiff.CheckTimeDiff()):
                bExecRunTask=True
            else:
                # 时间未到，继续休眠
                self.s_bNeedSleep=True
        else:
            bExecRunTask=True

        if(bExecRunTask):
            self.s_bNeedSleep=False
            for eachFbUnit in self.s_listFiberTaskUnit:
                if(eachFbUnit.TimerCheck()):
                    bRetValue=True

        if(len(self.s_listPostMsgStore)>0):
            self.ScheduleExecDelayPostMsg(500)
            # postMessage队列有内容？
            bRetValue=True
            pass

        if(not bRetValue):
            self.s_iLastContinueFreeCount+=1
        else:
            self.s_iLastContinueFreeCount=0
            self.s_lastFreeMilTimeDiff.ResetToNow()
            self.s_bNeedSleep=False

        return bRetValue

    # 检查和执行任务休眠
    def CheckTaskSleep(self, iDefMilSecond=1):
        if(self.s_bNeedSleep):
            time.sleep(iDefMilSecond/1000)

    # 增加任务
    def AddTask(self, fiberTaskUnit):
        self.s_listFiberTaskUnit.append(fiberTaskUnit)
        self.AddTaskToDict(fiberTaskUnit)

    # 调度执行延迟发送的消息
    def ScheduleExecDelayPostMsg(self, iMaxWaitMilSecond):
        bLooping=True
        maxWaitTimeCheck=CSkBot_Common_Share.CSkBot_MilTimeIdentify(iMaxWaitMilSecond)

        while(bLooping):
            # 队列有内容？
            if(len(self.s_listPostMsgStore)==0):
                bLooping=False
            else:
                # 时间超时?
                if(maxWaitTimeCheck.CheckTimeDiff()):
                    bLooping=False
                else:
                    # 此处对每个单元进行执行Send
                    nextMsgPostUnit=self.s_listPostMsgStore.pop(0)
                    if(nextMsgPostUnit.s_lDestTaskUID):
                        self.ExecTaskUnitMessage_UID(
                            fromSenderUnit=nextMsgPostUnit.s_senderRequestUnit, lTaskUID=nextMsgPostUnit.s_lDestTaskUID,
                            messageID=nextMsgPostUnit.s_lMessageID, bSendOrPost=True,
                            strMsgJsonParam=nextMsgPostUnit.s_strMsgJsonParam,
                            strMsgParam=nextMsgPostUnit.s_strMsgParam,
                            lMsgParam1=nextMsgPostUnit.s_lMsgParam1, lMsgParam2=nextMsgPostUnit.s_lMsgParam2)

                    elif(nextMsgPostUnit.s_strDestTaskFullName):
                        if(nextMsgPostUnit.s_strTaskParam):
                            self.ExecTaskUnitMessage_StrParam(
                                fromSenderUnit=nextMsgPostUnit.s_senderRequestUnit,
                                strFbUnitFullName=nextMsgPostUnit.s_strDestTaskFullName,
                                strDestTaskParam=nextMsgPostUnit.s_strTaskParam,
                                messageID=nextMsgPostUnit.s_lMessageID, bSendOrPost=True,
                                strMsgJsonParam=nextMsgPostUnit.s_strMsgJsonParam,
                                strMsgParam=nextMsgPostUnit.s_strMsgParam,
                                lMsgParam1=nextMsgPostUnit.s_lMsgParam1, lMsgParam2=nextMsgPostUnit.s_lMsgParam2)
                        else:
                            self.ExecTaskUnitMessage_LongParam(
                                fromSenderUnit=nextMsgPostUnit.s_senderRequestUnit,
                                strFbUnitFullName=nextMsgPostUnit.s_strDestTaskFullName,
                                lTaskParam1=nextMsgPostUnit.s_lTaskParam1,
                                lTaskParam2=nextMsgPostUnit.s_lTaskParam2,
                                messageID=nextMsgPostUnit.s_lMessageID, bSendOrPost=True,
                                strMsgJsonParam=nextMsgPostUnit.s_strMsgJsonParam,
                                strMsgParam=nextMsgPostUnit.s_strMsgParam,
                                lMsgParam1=nextMsgPostUnit.s_lMsgParam1, lMsgParam2=nextMsgPostUnit.s_lMsgParam2)

                    pass


    # 根据单元参数，搜索单元
    def SearchUnitByParams(self, lTaskUID, strFbUnitFullName, strDestTaskParam, lTaskParam1, lTaskParam2):
        retUnit=None

        if(lTaskUID):
            if(lTaskUID in self.s_dictUIDFiberTasks.keys()):
                retUnit=self.s_dictUIDFiberTasks[lTaskUID]
        else:
            if(strFbUnitFullName):
                strTaskParamStrKey, strTaskParamLongKey = self.GetTaskKey(strFbUnitFullName, strDestTaskParam,
                                                                          lTaskParam1, lTaskParam2)
                if(strTaskParamStrKey in self.s_dictStrParamFiberTasks.keys()):
                    retUnit=self.s_dictStrParamFiberTasks[strTaskParamStrKey]

                if(not retUnit):
                    if(strTaskParamLongKey in self.s_dictLongLongParamFiberTasks.keys()):
                        retUnit=self.s_dictLongLongParamFiberTasks[strTaskParamLongKey]

        return retUnit

    # 执行任务单元的消息
    def ExecTaskUnitMessage_UID(self, fromSenderUnit, lTaskUID, messageID, bSendOrPost,
                            strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        msgRetValue=None
        if(bSendOrPost):
            #处理sendmessage
            fiberUnit = self.SearchUnitByParams(lTaskUID=lTaskUID, strFbUnitFullName="", strDestTaskParam="",
                                                lTaskParam1=lMsgParam1, lTaskParam2=lMsgParam2)
            if(fiberUnit):
                msgRetValue =fiberUnit.v_HandleMessage(fromSenderUnit=fromSenderUnit, messageID=messageID,
                                          strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam,
                                          lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)
            pass
        else:
            self.AddDelayPostMsgToList(
                fromSenderUnit=fromSenderUnit,
                lTaskUID=lTaskUID, strFbUnitFullName="",
                strDestTaskParam="", lTaskParam1=0, lTaskParam2=0,
                messageID=messageID, strMsgJsonParam=strMsgJsonParam,
                strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        return msgRetValue

    # 执行任务单元的消息
    def ExecTaskUnitMessage_StrParam(self, fromSenderUnit, strFbUnitFullName,
                                     strDestTaskParam, messageID,  bSendOrPost,
                            strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        msgRetValue =FiberMsgRet(iExecResult=FiberMsgRet.s_g_iExecResult_Normal)
        if(bSendOrPost):
            #处理sendmessage
            fiberUnit = self.SearchUnitByParams(lTaskUID=0, strFbUnitFullName=strFbUnitFullName,
                                                strDestTaskParam=strDestTaskParam,
                                                lTaskParam1=0, lTaskParam2=0)
            if(fiberUnit):
                msgRetValue =fiberUnit.v_HandleMessage(fromSenderUnit=fromSenderUnit, messageID=messageID,
                                          strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam,
                                          lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)
            else:
                # 构建远程命令包。先存储，再发送
                msgRetValue.SetResult_To_RemoteExec(fromSenderUnit.s_strFullTaskName, strFbUnitFullName)
                self.Prompt_Store_RemoteExec(
                    fromSenderUnit=fromSenderUnit, strFbUnitFullName=strFbUnitFullName,
                    strDestTaskParam=strDestTaskParam, lTaskParam1=0, lTaskParam2=0,
                    messageID=messageID, strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam,
                    lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2, strExecMsgUID=msgRetValue.s_strRetValue)
                pass
            pass
        else:
            msgRetValue.s_iExecResult=FiberMsgRet.s_g_iExecResult_PostMessage
            self.AddDelayPostMsgToList(
                fromSenderUnit=fromSenderUnit,
                lTaskUID=0, strFbUnitFullName=strFbUnitFullName,
                strDestTaskParam=strDestTaskParam, lTaskParam1=0, lTaskParam2=0,
                messageID=messageID, strMsgJsonParam=strMsgJsonParam,
                strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)
        return msgRetValue

    # 执行任务单元的消息
    def ExecTaskUnitMessage_LongParam(self, fromSenderUnit, strFbUnitFullName,
                                      lTaskParam1, lTaskParam2, messageID,  bSendOrPost,
                            strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        msgRetValue =FiberMsgRet(iExecResult=FiberMsgRet.s_g_iExecResult_Normal)
        if(bSendOrPost):
            #处理sendmessage
            fiberUnit = self.SearchUnitByParams(lTaskUID=0, strFbUnitFullName=strFbUnitFullName,
                                                strDestTaskParam="",
                                                lTaskParam1=lTaskParam1, lTaskParam2=lTaskParam2)
            if(fiberUnit):
                msgRetValue =fiberUnit.v_HandleMessage(fromSenderUnit=fromSenderUnit, messageID=messageID,
                                          strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam,
                                          lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)
            else:
                msgRetValue.SetResult_To_RemoteExec(fromSenderUnit.s_strFullTaskName, strFbUnitFullName)
                # 构建远程命令包。先存储，再发送
                self.Prompt_Store_RemoteExec(
                    fromSenderUnit=fromSenderUnit, strFbUnitFullName=strFbUnitFullName,
                    strDestTaskParam="", lTaskParam1=lTaskParam1, lTaskParam2=lTaskParam2,
                    messageID=messageID, strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam,
                    lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2, strExecMsgUID=msgRetValue.s_strRetValue)
            pass
        else:
            msgRetValue.s_iExecResult=FiberMsgRet.s_g_iExecResult_PostMessage
            self.AddDelayPostMsgToList(
                fromSenderUnit=fromSenderUnit,
                lTaskUID=0, strFbUnitFullName=strFbUnitFullName,
                strDestTaskParam="", lTaskParam1=lTaskParam1, lTaskParam2=lTaskParam2,
                messageID=messageID, strMsgJsonParam=strMsgJsonParam,
                strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        return msgRetValue

    # 提交远程执行命令，存储，准备调度发送
    #start by sk. 180414
    def Prompt_Store_RemoteExec(self, fromSenderUnit, strFbUnitFullName, strDestTaskParam, lTaskParam1, lTaskParam2,
                                messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2, strExecMsgUID):
        remoteRunUnit = CUTRC_NATs_Comu_RunMessageUnit()
        remoteRunUnit.SetContent_FromFiberUnit(fromSenderUnit)
        remoteRunUnit.SetContent_DestFiberUnit(strFbUnitFullName, strDestTaskParam, 0, 0)
        remoteRunUnit.SetContent_MsgContent(messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2)
        remoteRunUnit.s_strGlobalMsg_UID=strExecMsgUID
        self.s_store_listNeedSendRemoteMsgTask.append(remoteRunUnit)

    # 处理接收到的命令
    # start by sk. 180414
    def HandleExRemoteExecCmd(self, utrcComuRunMsgUnit):
        retComuExecMsgUnit = CUTRC_NATs_Comu_RunMessageUnit()
        msgExecResult = None

        localFiberUnit = self.SearchUnitByParams(lTaskUID=0, strFbUnitFullName=utrcComuRunMsgUnit.s_strDestFbUnit_FullName,
                                                 strDestTaskParam=utrcComuRunMsgUnit.s_strDestFbUnit_StrParam,
                                                 lTaskParam1=utrcComuRunMsgUnit.s_lDestFbUnit_lParam1,
                                                 lTaskParam2=utrcComuRunMsgUnit.s_lDestFbUnit_lParam2)
        if(localFiberUnit):
            tmpSimuRemoteFiber=FiberUnit_Base(strFullTaskName=utrcComuRunMsgUnit.s_strFromFbUnit_FullName,
                                              strTaskParam=utrcComuRunMsgUnit.s_strFromFbUnit_StrParam,
                                              lTaskParam1=utrcComuRunMsgUnit.s_lFromFbUnit_lParam1,
                                              lTaskParam2=utrcComuRunMsgUnit.s_lFromFbUnit_lParam2)

            strParamContent, strJsonParam = utrcComuRunMsgUnit.RetriveOrigStrContent()

            if (utrcComuRunMsgUnit.s_strDestFbUnit_StrParam):
                msgExecResult = self.ExecTaskUnitMessage_StrParam(
                    fromSenderUnit=tmpSimuRemoteFiber,
                    strFbUnitFullName=utrcComuRunMsgUnit.s_strDestFbUnit_FullName,
                    strDestTaskParam=utrcComuRunMsgUnit.s_strDestFbUnit_StrParam,
                    messageID=utrcComuRunMsgUnit.s_iRun_MessageID, bSendOrPost=True,
                    strMsgJsonParam=strJsonParam,
                    strMsgParam=strParamContent,
                    lMsgParam1=utrcComuRunMsgUnit.s_lMsgParam1, lMsgParam2=utrcComuRunMsgUnit.s_lMsgParam2)
            else:
                msgExecResult = self.ExecTaskUnitMessage_LongParam(
                    fromSenderUnit=tmpSimuRemoteFiber,
                    strFbUnitFullName=utrcComuRunMsgUnit.s_strDestFbUnit_FullName,
                    lTaskParam1=utrcComuRunMsgUnit.s_lDestFbUnit_lParam1,
                    lTaskParam2=utrcComuRunMsgUnit.s_lDestFbUnit_lParam2,
                    messageID=utrcComuRunMsgUnit.s_iRun_MessageID, bSendOrPost=True,
                    strMsgJsonParam=strJsonParam,
                    strMsgParam=strParamContent,
                    lMsgParam1=utrcComuRunMsgUnit.s_lMsgParam1, lMsgParam2=utrcComuRunMsgUnit.s_lMsgParam2)

        retComuExecMsgUnit.Build_From_Orig_MsgRetResult(utrcComuRunMsgUnit, msgExecResult)

        return retComuExecMsgUnit

    # 处理接收到 的 远端执行命令结果
    # start by sk. 180414
    def HandleExReplyRemoteExecResult(self, utrcComuRunReplyMsgResult):
        localFiberUnit = self.SearchUnitByParams(lTaskUID=0, strFbUnitFullName=utrcComuRunReplyMsgResult.s_strFromFbUnit_FullName,
                                                 strDestTaskParam=utrcComuRunReplyMsgResult.s_strFromFbUnit_StrParam,
                                                 lTaskParam1=utrcComuRunReplyMsgResult.s_lFromFbUnit_lParam1,
                                                 lTaskParam2=utrcComuRunReplyMsgResult.s_lFromFbUnit_lParam2)
        if(localFiberUnit):
            tmpSimuRemoteFiber=FiberUnit_Base(strFullTaskName=utrcComuRunReplyMsgResult.s_strDestFbUnit_FullName,
                                              strTaskParam=utrcComuRunReplyMsgResult.s_strDestFbUnit_StrParam,
                                              lTaskParam1=utrcComuRunReplyMsgResult.s_lDestFbUnit_lParam1,
                                              lTaskParam2=utrcComuRunReplyMsgResult.s_lDestFbUnit_lParam2,
                                              bTemporyUse=True)

            delayExecResult = FiberMsgRet()
            delayExecResult.ImportFromComuRunMsgUnit(utrcComuRunReplyMsgResult)

            # 发送接收到的消息。
            self.AddDelayPostMsgToList(
                fromSenderUnit=tmpSimuRemoteFiber,
                lTaskUID=0, strFbUnitFullName=utrcComuRunReplyMsgResult.s_strFromFbUnit_FullName,
                strDestTaskParam=utrcComuRunReplyMsgResult.s_strFromFbUnit_StrParam,
                lTaskParam1=utrcComuRunReplyMsgResult.s_lFromFbUnit_lParam1,
                lTaskParam2=utrcComuRunReplyMsgResult.s_lFromFbUnit_lParam2,
                messageID=Fiber_MessageID.FMID_RemoteReplyMsgExecResult,

                strMsgJsonParam=delayExecResult.ExportToStr(),
                strMsgParam=utrcComuRunReplyMsgResult.s_strGlobalMsg_UID,
                lMsgParam1=0,
                lMsgParam2=0)
            pass
        pass

    # 获得需要执行的远程命令
    #start by sk. 180414
    def PopRetrive_RemoteExec(self):
        retMsgUnit = None
        if(len(self.s_store_listNeedSendRemoteMsgTask)>0):
            retMsgUnit=self.s_store_listNeedSendRemoteMsgTask.pop(0)
        return retMsgUnit


    # 增加延迟任务到队列
    def AddDelayPostMsgToList(self, fromSenderUnit, lTaskUID, strFbUnitFullName,
                              strDestTaskParam, lTaskParam1, lTaskParam2,
                              messageID,
                              strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        msgPostStore= FiberMang.CMsgPostStoreUnit(
            senderFiberUnit=fromSenderUnit,
            lTaskUID=lTaskUID, strDestTaskFullName=strFbUnitFullName,
            strTaskParm=strDestTaskParam, lTaskParam1=lTaskParam1,
            lTaskParam2=lTaskParam2,
            lMessageID=messageID, strMsgJsonParam=strMsgJsonParam,
            strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        self.s_listPostMsgStore.append(msgPostStore)


    # 获得节点单元的格式。
    # update to same to c# version. by sk. 180416
    @staticmethod
    def GetTaskKey(strTaskFullName, strParam, lParam1, lParam2):
        strStrParamKey, strStrLongParamKey="", ""

        if(strParam):
            strStrParamKey="strParam_##_%s_##_%s" % (strParam, strTaskFullName)

        if(lParam1):
            strStrLongParamKey="lParam_##_%d_##_%d_##_%s" % (lParam1, lParam2, strTaskFullName)

        if(strStrParamKey=="" and strStrLongParamKey==""):
            strStrParamKey=strTaskFullName

        return  strStrParamKey, strStrLongParamKey

    pass

# 纤程单元的实现
class FiberUnit_Base:
    def __init__(self, strFullTaskName, strTaskParam="", lTaskParam1=0, lTaskParam2=0,
                 iCheckEveryMilSecond=1000, iIdleCheckEveryMilSecond=5000, bExRemoteCallMe=False, bTemporyUse=False):
        # 获得最后唯一ID
        self.s_lUniqueID = FiberMang.GetUniqueInstanceID()

        self.s_strFullTaskName = strFullTaskName
        self.s_strTaskParam = strTaskParam
        self.s_lTaskParam1=lTaskParam1
        self.s_lTaskParam2=lTaskParam2

        # 时间检查
        self.s_iCheckEveryMilSecond =iCheckEveryMilSecond    # 每单位时间检查一次
        self.s_iIdleCheckEveryMilSecond=iIdleCheckEveryMilSecond  # 如果持续空闲，则休眠这个时间段

        self.s_lastFreeMilTimeDiff=CSkBot_Common_Share.CSkBot_MilTimeIdentify(self.s_iCheckEveryMilSecond) # 空闲检查
        self.s_lastContinueIdle_MilTimeDiff=CSkBot_Common_Share.CSkBot_MilTimeIdentify(self.s_iIdleCheckEveryMilSecond) # 空闲检查
        self.s_bLastBusyStatus=False
        self.s_bInContinueCheckFreeStatus=False
        self.s_iKeepIdleCheckFitCount=0  # 持续统计空闲次数
        self.s_iMaxKeepIdleCheckCount = 20 # 最多持续空闲20次

        self.s_parentFiberMang = None

        self.s_bExRemoteCallMe=bExRemoteCallMe
        self.s_bTemporyUse=bTemporyUse

    def __del__(self):
        if(self.s_parentFiberMang):
            self.s_parentFiberMang.RemoveTaskFromDict(self)


    def v_SetParentMang(self, parentFiberMang):
        self.s_parentFiberMang = parentFiberMang  # 保存父单元管理
        self.PostTaskMsg_UID(self.s_lUniqueID, Fiber_MessageID.FMID_Init)
        self.s_parentFiberMang.AddTaskToDict(self)

    def v_OnInit(self):
        # 初始化
        pass

    def v_OnClose(self):
        # 删除
        pass

    # 单位时间检查
    def TimerCheck(self):
        bRetTaskBusy=False  # 返回状态值
        bExecTask, bExecTimerCheck=False,False # 执行任务，执行时间检查

        # 是否为N毫秒检查一次？
        if(self.s_iCheckEveryMilSecond):
            if(self.s_lastFreeMilTimeDiff.CheckTimeDiff()):
                bExecTimerCheck=True
        else:
            bExecTimerCheck=True

        if(bExecTimerCheck):
            #上次繁忙吗？这次直接执行
            if(self.s_bLastBusyStatus):
                bExecTask=True
            else:
                # 上次还在进行持续空闲检查?
                if(self.s_bInContinueCheckFreeStatus):
                    if(self.s_lastContinueIdle_MilTimeDiff.CheckTimeDiff()):
                        bExecTask=True
                else:
                    bExecTask=True

            if(bExecTask):
                # 执行，时间检查
                startTimeDiffCheck=CSkBot_Common_Share.CSkBot_MilTimeIdentify()

                try:
                    bRetTaskBusy=self.v_Base_TimerCheck()
                except Exception as e:
                    CTYLB_MainSys_MiscFunc.ShowExceptionInfo(e)
                    bRetTaskBusy=True

                curTimeDiff = startTimeDiffCheck.GetStartTimeDiff()
                iTotalMilSecond=curTimeDiff.microseconds
                if(iTotalMilSecond>3000):
                    strFullParam="UID:%d, strParam:%s, lParam:%d-%d" % \
                                 (self.s_lUniqueID, self.s_strTaskParam, self.s_lTaskParam1, self.s_lTaskParam2)
                    CTYLB_Log.ShowLog(0, self.s_strFullTaskName, ("time:%d, " % (iTotalMilSecond/1000)) + strFullParam)

                if(bRetTaskBusy):
                    # 如果繁忙，清空所有状态
                    self.s_bInContinueCheckFreeStatus=False
                    self.s_iKeepIdleCheckFitCount = 0
                else:
                    # 如果上次也为空闲
                    if(self.s_bLastBusyStatus):
                        self.s_iKeepIdleCheckFitCount += 1
                        if(self.s_iKeepIdleCheckFitCount >= self.s_iMaxKeepIdleCheckCount):
                            # 持续空闲，进行空闲持续状态
                            self.s_bInContinueCheckFreeStatus=True
                            self.s_lastContinueIdle_MilTimeDiff.ResetToNow()

                self.s_bLastBusyStatus=bRetTaskBusy

        return bRetTaskBusy

    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        pass

    # 下面实现消息机制
    def SendTaskMsg_UID(self, lTaskUID, messageID,
                        strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        return self.s_parentFiberMang.ExecTaskUnitMessage_UID(
            self, lTaskUID, messageID, True,
            strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        pass

    def PostTaskMsg_UID(self, lTaskUID, messageID,
                        strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        return self.s_parentFiberMang.ExecTaskUnitMessage_UID(
            self, lTaskUID, messageID, False,
            strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        pass

    def SendTaskMsg_StrParam(self, strFbUnitFullName, messageID, strDestTaskParam="",
                        strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        return self.s_parentFiberMang.ExecTaskUnitMessage_StrParam(
            self, strFbUnitFullName, strDestTaskParam, messageID, True,
            strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

        pass

    def PostTaskMsg_StrParam(self, strFbUnitFullName, messageID, strDestTaskParam="",
                        strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        return self.s_parentFiberMang.ExecTaskUnitMessage_StrParam(
            self, strFbUnitFullName, strDestTaskParam, messageID, False,
            strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

    def SendTaskMsg_LongParam(self, strFbUnitFullName, messageID, lTaskParam1=0, lTaskParam2=0,
                              strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        return self.s_parentFiberMang.ExecTaskUnitMessage_LongParam(
            self, strFbUnitFullName, lTaskParam1, lTaskParam2, messageID, True,
            strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

    def PostTaskMsg_LongParam(self, strFbUnitFullName, messageID, lTaskParam1=0, lTaskParam2=0,
                              strMsgJsonParam="", strMsgParam="", lMsgParam1=0, lMsgParam2=0):

        return self.s_parentFiberMang.ExecTaskUnitMessage_LongParam(
            self, strFbUnitFullName, lTaskParam1, lTaskParam2, messageID, False,
            strMsgJsonParam=strMsgJsonParam, strMsgParam=strMsgParam, lMsgParam1=lMsgParam1, lMsgParam2=lMsgParam2)

    # 处理消息
    def v_HandleMessage(self, fromSenderUnit, messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        fiberMsgRet=None

        if(messageID==Fiber_MessageID.FMID_Init):
            self.v_OnInit()
        elif(messageID==Fiber_MessageID.FMID_Close):
            self.v_OnClose()
        elif(messageID==Fiber_MessageID.FMID_RemoteReplyMsgExecResult):
            msgExecRet=FiberMsgRet()
            msgExecRet.ImportFromStr(strMsgJsonParam)
            self.v_On_RemoteReplyMsgResult(strMsgParam, msgExecRet)
            pass
        elif(messageID==Fiber_MessageID.FMID_Ping):
            msgExecRet=FiberMsgRet(strRetValue=strMsgParam, strRetJsonValue=strMsgJsonParam,
                                   lRetValue=lMsgParam1, lRetValue2=lMsgParam2)

        return fiberMsgRet

    # 虚函数，通知远端发送回消息
    # add by sk. 180415
    def v_On_RemoteReplyMsgResult(self, strMsgExecUID, msgExecRet):
        pass

    pass


# 组单元基本类
class FiberGroupUnit_Base(FiberUnit_Base):
    s_g_strGroupUnit_FullName="FiberGroupUnit_Base"
    def __init__(self, strFullTaskName=s_g_strGroupUnit_FullName, strTaskParam="",
                 lTaskParam1=0, lTaskParam2=0,
                 iCheckEveryMilSecond=1000, iIdleCheckEveryMilSecond=5000):
        FiberUnit_Base.__init__(self, strFullTaskName=strFullTaskName, strTaskParam=strTaskParam,
                       lTaskParam1=lTaskParam1, lTaskParam2=lTaskParam2,
                       iCheckEveryMilSecond=iCheckEveryMilSecond, iIdleCheckEveryMilSecond=iIdleCheckEveryMilSecond)

        self.s_subTasksArray=[]

    def AddSubFiberUnit(self, subFiberUnit):
        # 增加到我的子单元列表
        self.s_subTasksArray.append(subFiberUnit)

        # 设置父总管理
        if(self.s_parentFiberMang):
            subFiberUnit.v_SetParentMang(self.s_parentFiberMang)
        pass

    def v_SetParentMang(self, parentFiberMang):
        FiberUnit_Base.v_SetParentMang(self, parentFiberMang)

        # 此时也设置子单元的 父管理
        for eachFiber in self.s_subTasksArray:
            eachFiber.v_SetParentMang(self.s_parentFiberMang)


    # 应用单元 应用级调用
    def v_Base_TimerCheck(self):
        bRetValue=False

        for eachFiber in self.s_subTasksArray:
            if(eachFiber.TimerCheck()):
                bRetValue=True

        if(self.v_GroupApp_TimerCheck()):
            bRetValue=True

        return bRetValue

    # 应用单元 应用级调用
    def v_GroupApp_TimerCheck(self):
        pass
