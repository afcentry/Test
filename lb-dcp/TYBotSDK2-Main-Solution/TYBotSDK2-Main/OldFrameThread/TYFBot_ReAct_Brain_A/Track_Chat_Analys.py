# -*- coding:UTF-8 -*- 放到第一行标记
# Track_Chat_Analys.py 跟踪-聊天-分析 功能实现
#
# start by sk. 170412

from datetime import datetime
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from Sk_LB_db_FBot_ReactBrain_Real import CSkLBDB_ea_brain_chatcontent, CSkLBDB_ea_brain_enviru_property, CSkLBDB_ea_brain_envirument,\
    CSkLBDB_ea_brain_usermang, CSkLBDB_ea_brain_exec_task
from Operate_Store_Real import CTYOp_ReActBrain_Store

import time
import os
import json

from BotSDK.bot_manager import BotManager


g_i_ExecTypeID_LifeSupport_AlarmRing = 1000001   # 执行类型ID-生活助手-闹钟方式提醒
g_str_TYLB_TimeFormat = u'%Y-%m-%d %H:%M:%S'   # 时间格式

g_str_Alarm_origParam_Time = u'NotifyTime'
g_str_Alarm_origParam_AlarmContent = u'Content'

g_i_ExecTypeID_Monitor_ShowNetworkSituation=20001 #执行类型ID-态势感知-显示器展示指定地区或者企业网络安全态势
g_i_ExecTypeID_Monitor_ShowNetworkAssets=20002    #执行类型ID-态势感知-展示指定地区或企业的网络资产分布


chatBot=BotManager()    #初始化语义行动分解机器人
chatBot.train()        #训练语料

# 大脑分析机器人，对任务进行跟踪检查
# start by sk. 170412
class CTYReActBrainBot_Track_Checker:
    s_g_iTaskCheckDiffTime = 2   # 每2秒钟检查一次任务状态
    s_g_iTask_WaitStart_MaxIdleTime = 10  # 每10秒检查一下等待调度的任务
    s_g_iTask_Running_MaxWaitTime = 10  # 每10秒检查一下正在运行的任务

    def __init__(self):
        self.s_iLastCheckTaskTime = datetime(2017,1,1)
        self.s_lastCheckUserMoodTime = datetime(2017,1,1)
        pass

    def __del__(self):
        pass

    # 单位时间检查接收到的内容，进行分析处理
    # start by sk. 170412
    @staticmethod
    def TimerCheck_ChatContent( dbConn):
        bRetValue = False

        # 搜索聊天内容表，未处理的新记录
        iNextChatContentID = CSkLBDB_ea_brain_chatcontent.SearchNextRec_By_Direction_ExecStatus(
            dbConn, CTYOp_ReActBrain_Store.s_g_iDirection_From_User_To_Brain, CTYOp_ReActBrain_Store.s_g_iStatus_Free)

        if( iNextChatContentID):
            bRetValue = True
            iBelongEnviruID, strChatContent, iContentType, iDirection, createTime, execTime, iExecStatus\
                = CSkLBDB_ea_brain_chatcontent.ReadByRecID( dbConn, iNextChatContentID)

            iOrigUserType, strOrigUserName, strOrigGroupName = CTYOp_ReActBrain_Store.GetEnvirumentID_NameType( dbConn, iBelongEnviruID)
            strReplyChatContent, iReplyContentType = '', CTYOp_ReActBrain_Store.s_g_iContentType_Text
            if( iContentType == CTYOp_ReActBrain_Store.s_g_iContentType_Text):
                # 如果需要执行，放到exec_task表中，等待其他程序来取，取了执行后，结果放入 exec_result表。

                # 把result表的结果，放入chatcontent表，其他模块自动调度发送
                strReplyChatContent = CTYReActBrainBot_Track_Checker.__SubAnalyExecCmd( dbConn, iBelongEnviruID, strChatContent)


            else:
                strReplyChatContent = '暂时不支持图像类型'

            if(strReplyChatContent):
                CTYReActBrainBot_Track_Checker.AddReplyTextInfoToUser( dbConn, iBelongEnviruID, strReplyChatContent)
            # 设置原记录已经处理
            CSkLBDB_ea_brain_chatcontent.Update_ExTime_Status( dbConn, iNextChatContentID, datetime.now(), CTYOp_ReActBrain_Store.s_g_iStatus_Finish)

        return bRetValue

    # 分析处理子命令
    # start by sk. 170413
    @staticmethod
    def __SubAnalyExecCmd(dbConn, iBelongEnviruID, strChatContent):
        '''
        reply_action={}
        reply_action["error"] = 0
        reply_action["msg"] = "ok"
        reply_action["reply_text"]="你设置了提醒任务，我将在1分钟后提醒你[上厕所]哦"
        reply_action["operation"]="Add"
        reply_action["task_type"]="Alarm"
        reply_action["task_data"]={"hour":0,"minute":0,"remarks":"上厕所"}
        '''
        reply_action=chatBot.think_reply_action(word=strChatContent)
        strOperateType=reply_action["operation"].strip()
        strTaskType=reply_action["task_type"].strip()
        strParamJson=reply_action["task_data"]
        strReply = reply_action["reply_text"]
        strRetContentReply = strReply


        if strTaskType=="Alarm":
            # 提醒任务
            iExecTaskTypeID = g_i_ExecTypeID_LifeSupport_AlarmRing
            if strOperateType=="Add":
                #新增任务
                iHour = strParamJson["hour"]
                iMinute = strParamJson["minute"]
                nowTime = datetime.now()
                #TODO:调试时时间设置为当前的小时+2分钟
                iHour=nowTime.hour
                iMinute=nowTime.minute+2
                alarmTime = datetime(nowTime.year, nowTime.month, nowTime.day, iHour, iMinute, 0)
                strAlarmTime = alarmTime.strftime(g_str_TYLB_TimeFormat)

                strCombParam = {g_str_Alarm_origParam_Time: strAlarmTime,
                                g_str_Alarm_origParam_AlarmContent: strParamJson["remarks"]}
                strOrigParam = json.dumps(strCombParam,ensure_ascii=False)

                CSkLBDB_ea_brain_exec_task.AddNewdRec(dbConn, iBelongEnviruID, iExecTaskTypeID, strChatContent,
                                                      strOrigParam, '', 0)
                strRetContentReply = strReply
            elif strOperateType=="Delete":
                #删除任务
                pass
            else:
                #未知任务类型
                pass
        elif strTaskType=="NetworkSituation":
            #网络安全态势感知展示任务
            iExecTaskTypeID = g_i_ExecTypeID_Monitor_ShowNetworkSituation
            if strOperateType=="Add":
                #新增任务
                strOrigParam = json.dumps(strParamJson,ensure_ascii=False)
                CSkLBDB_ea_brain_exec_task.AddNewdRec(dbConn, iBelongEnviruID, iExecTaskTypeID, strChatContent,
                                                      strOrigParam, '', 0)
                strRetContentReply = strReply
                print("[*]新增态势任务：{}".format(strOrigParam))
            elif strOperateType=="Delete":
                #删除任务
                pass
            else:
                #未知任务类型
                pass
        elif strTaskType=="NetworkAssets":
            #网络资产关联展示任务
            iExecTaskTypeID = g_i_ExecTypeID_Monitor_ShowNetworkAssets
            if strOperateType=="Add":
                #新增任务
                strOrigParam = json.dumps(strParamJson,ensure_ascii=False)
                CSkLBDB_ea_brain_exec_task.AddNewdRec(dbConn, iBelongEnviruID, iExecTaskTypeID, strChatContent,
                                                      strOrigParam, '', 0)
                strRetContentReply = strReply
                print("[*]新增网络资产任务：{}".format(strOrigParam))
            elif strOperateType=="Delete":
                #删除任务
                pass
            else:
                #未知任务类型
                pass

        else:
            #当作普通对话处理
            strRetContentReply = strReply



        return strRetContentReply

    # 提交信息发送给用户
    # start by sk. 170413
    @staticmethod
    def AddReplyTextInfoToUser( dbConn, iUserEnviruID, strChatText):
        CSkLBDB_ea_brain_chatcontent.AddNewdRec(dbConn, iUserEnviruID, strChatText, CTYOp_ReActBrain_Store.s_g_iContentType_Text,
                                                CTYOp_ReActBrain_Store.s_g_iDirection_From_Brain_To_User)

    # 调度 持续运行的任务进行执行
    # start by sk. 170413
    def TimerCheck_ScheduleAlwaysTask(self, dbConn):
        bRetValue = False

        # 任务表，已经完成了的，但是，又需要总是运行的
        recIDArray = CSkLBDB_ea_brain_exec_task.GetRecList_By_Status_AlwaysValue(dbConn, CTYOp_ReActBrain_Store.s_g_iStatus_Finish, 1)
        if( recIDArray):
            bRetValue = True

        for iEachRecID in recIDArray:
            CSkLBDB_ea_brain_exec_task.Update_ExStatus( dbConn, iEachRecID, CTYOp_ReActBrain_Store.s_g_iStatus_Free)

        # 每2秒钟检查一次
        if( CTYLB_MainSys_MiscFunc.CheckIdleTime(self.s_iLastCheckTaskTime, CTYReActBrainBot_Track_Checker.s_g_iTaskCheckDiffTime)):
            self.s_iLastCheckTaskTime = datetime.now()

            # 检查当前用户环境可否需要输出

            # 检查任务表中，已经提交，但长时间未启动的，提示，当前系统忙还需要等待。
            waitLongTimeRecArray = CSkLBDB_ea_brain_exec_task.GetRecList_By_Status( dbConn, CTYOp_ReActBrain_Store.s_g_iStatus_Free)
            for iEachWaitRecID in waitLongTimeRecArray:
                iUserEnvID, lastCheckTime = CSkLBDB_ea_brain_exec_task.Read_EnvID_LastCheckTIme_By_RecID( dbConn, iEachWaitRecID)
                if( CTYLB_MainSys_MiscFunc.CheckIdleTime( lastCheckTime, CTYReActBrainBot_Track_Checker.s_g_iTask_WaitStart_MaxIdleTime)):
                    lastCheckTime = datetime.now()

                    curCheckUserExec = CUserExecReal( dbConn, iUserEnvID)
                    if( curCheckUserExec.GetCanTrackTaskLog()):
                        CTYReActBrainBot_Track_Checker.AddReplyTextInfoToUser( dbConn, iUserEnvID, u'系统忙，请稍等，任务还在准备调度')
                    CSkLBDB_ea_brain_exec_task.Update_LastCheckTime( dbConn, iEachWaitRecID, lastCheckTime)

            # 任务表中，已经启动，但长时间未完成的，提示，当前还在运行
            runningLongTimeRecArray = CSkLBDB_ea_brain_exec_task.GetRecList_By_Status( dbConn, CTYOp_ReActBrain_Store.s_g_iStatus_Running)
            for iEachRunningRecID in waitLongTimeRecArray:
                iUserEnvID, lastCheckTime = CSkLBDB_ea_brain_exec_task.Read_EnvID_LastCheckTIme_By_RecID( dbConn, iEachRunningRecID)
                if( CTYLB_MainSys_MiscFunc.CheckIdleTime( lastCheckTime, CTYReActBrainBot_Track_Checker.s_g_iTask_Running_MaxWaitTime)):
                    lastCheckTime = datetime.now()

                    curCheckUserExec = CUserExecReal( dbConn, iUserEnvID)
                    if( curCheckUserExec.GetCanTrackTaskLog()):
                        lastRequestExecTime = CSkLBDB_ea_brain_exec_task.Read_RequestExecTime_By_RecID( dbConn, iUserEnvID)
                        if( lastRequestExecTime):
                            timeDiff = datetime.now() - lastRequestExecTime
                            strWaitTime = u'%d秒' % (timeDiff.seconds)
                        else:
                            strWaitTime = u'%d秒以上' % (CTYReActBrainBot_Track_Checker.s_g_iTask_Running_MaxWaitTime)
                        CTYReActBrainBot_Track_Checker.AddReplyTextInfoToUser( dbConn, iUserEnvID, u'任务正在运行，请等待，开始时间已经有 %s 了' % (strWaitTime))

                    CSkLBDB_ea_brain_exec_task.Update_LastCheckTime( dbConn, iEachRunningRecID, lastCheckTime)
                pass


        return bRetValue

    # 对每个用户进行对话的跟踪状态情绪和反应
    # start by sk. 170413
    def TimerCheck_UserMoodCheckTime( self, dbConn):
        bRetValue = False

        # 每2秒钟检查一次
        if( CTYLB_MainSys_MiscFunc.CheckIdleTime(self.s_lastCheckUserMoodTime, CTYReActBrainBot_Track_Checker.s_g_iTaskCheckDiffTime)):
            self.s_lastCheckUserMoodTime = datetime.now()

            # 获得用户单独对话的列表
            iUserFaceToFaceEnvRecArray = CSkLBDB_ea_brain_envirument.GetRecList_By_GroupName( dbConn, '')
            if( iUserFaceToFaceEnvRecArray):
                bRetValue = True
            for iEachUserEnvRecID in iUserFaceToFaceEnvRecArray:
                curCheckUserExec = CUserExecReal(dbConn, iEachUserEnvRecID)
                iContentType, strActiveSendContent = curCheckUserExec.CheckActive_DaShan_SayContent()
                if( strActiveSendContent):
                    CTYReActBrainBot_Track_Checker.AddReplyTextInfoToUser(dbConn, iEachUserEnvRecID, strActiveSendContent)
                pass
        return bRetValue

    # 调度 持续运行的任务进行执行
    # start by sk. 170412
    @staticmethod
    def SubExec_TellAnswner(dbConn, strChatContent, inputCheckSayUnit):
        strRetChatContent, iRetContentType = u'TianYuan FuncBot - waiting',  CTYOp_ReActBrain_Store.s_g_iContentType_Text

        return strRetChatContent, iRetContentType


# 用户执行实现，操作用户的属性，判断用户特点，设置存储用户的内容
# start by sk. 170413
class CUserExecReal:
    s_g_strTrackProp = u'TrackTaskLog'   # 跟踪任务日志属性

    def __init__(self, dbConn, iUserEnvRecID):
        self.s_dbConn = dbConn
        self.s_iUserEnvRecID = iUserEnvRecID
        pass

    def __del__(self):
        pass

    # 设置 属性值
    def __SetPropValue(self, strPropName, strPropValue):
        CSkLBDB_ea_brain_enviru_property.AddNewdRec( self.s_dbConn, self.s_iUserEnvRecID, strPropName, strPropValue)

    # 获取 属性值
    def __GetPropValue(self, strPropName, strDefaultValue):
        strRetValue = strDefaultValue
        iPropRecID = CSkLBDB_ea_brain_enviru_property.GetRecID_By_EnviruID_PropName( self.s_dbConn, self.s_iUserEnvRecID, strPropName)
        if( iPropRecID):
            strRetValue = CSkLBDB_ea_brain_enviru_property.ReadValueField_By_RecID( self.s_dbConn,  self.s_iUserEnvRecID, iPropRecID)
        return strRetValue

    # 设置 跟踪任务日志
    def SetTrackTaskLog(self, bTrackLog):
        strPropValue = '1' if(bTrackLog) else '0'
        self.__SetPropValue( CUserExecReal.s_g_strTrackProp, strPropValue)

    # 获取 是否可以 跟踪任务日志
    def GetCanTrackTaskLog(self):
        bRetValue = False
        strGetTrackLogValue = self.__GetPropValue(CUserExecReal.s_g_strTrackProp, '0')
        if( strGetTrackLogValue == '1'):
            bRetValue = True

        return bRetValue

    # 设置 搭讪方式的内容，主动打招呼
    def CheckActive_DaShan_SayContent(self):
        return 0, ''
