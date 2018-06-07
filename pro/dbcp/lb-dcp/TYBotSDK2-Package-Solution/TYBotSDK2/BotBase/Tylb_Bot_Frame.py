# -*- coding:UTF-8 -*- 放到第一行标记
# Tylb_Bot_Frame.py 天元机器人－基本框架
#
# start by sk. 170222
# update by sk. 170429, to python3, 字符串转为unicode 和流数据 utf-8 bytes格式

import time
from datetime import datetime
import threading
from TYBotSDK2.P2PClient.Tylb_Support_Client import CTYLB_Base_Client
from TYBotSDK2.P2PClient.Tylb_p2p_ExCall_SubClient import CTYLB_Bot_Sk_Entry_Main, CTYLB_Bot_G_CallBack_DefUnit, \
    CTYBot_CTUnit_SimuSystemNotify, CTYBot_CTUnit_CreateNewUnit_SimuSystemNotify
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc, CTY_YamlFile
from .Tylb_Bot_HL_SockReal import CTYBot_HL_Sock_Mang, CTYBot_CTUnit_CreateNewUnit_HLSessionSock
from .Tylb_Bot_Base_Def import CTYLB_Bot_BaseDef
from .Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYBot_CTUnit_Common_CreateNewUnit_CommonData

g_iMaxExecIdleCount = 50  # 最大的执行休眠次数

# 机器人执行框架
# start by sk. 170226
class CTylb_Bot_Exec_Frame:
    # 初始化
    # funcIsGlobalExit --- 是否退出的检测函数  bool IsGlobalExit()
    # funcTimerCheckCallBack  --- 每隔小段时间触发的回调函数  bool TimerCheckCallBack()
    # strTYP2PClientCfgFile  --- 天元客户端配置文件名
    # strDbFileName --- 数据库存放的文件名
    # start by sk. 170222
    def __init__(self, funcTimerCheckCallBack, ustrCfgFileName, ustrDbFileName, funcIsGlobalExit=None):
        self.s_clientP2PExec = CTYLB_Bot_Sk_Entry_Main( ustrCfgFileName, ustrDbFileName)
        self.s_tylbBaseClient = CTYLB_Base_Client(ustrCfgFileName, ustrDbFileName)
        self.s_funcIsGlobalExit = funcIsGlobalExit
        self.s_funcTimerCheckCallBack = funcTimerCheckCallBack
        pass

    # 读取 ini里面的字符串配置值
    # start by sk. 170223
    @staticmethod
    def ReadIniSectionValue( strIniFileName, strSection, strKey, strDefValue):
        yamlFile = CTY_YamlFile(strIniFileName)
        yamlFile.load_configs()

        strReadKey = '%s.%s'%(strSection, strKey)
        strValue = yamlFile.get_config(strReadKey, strDefValue)
        return strValue

    # 注册 当数据单元到达时，的回调函数
    # iDataType  --- 数据单元的数据类型
    # iMainCmd --- 数据单元的主命令
    # iSubCmd --- 数据单元的子命令
    # param1  --- 触发回调时的参数1
    # param2  --- 触发回调时的参数2
    # funcCreateNewCTUnit  --- 创建新单元的执行函数
    # funcRecvCTUnitCallBack --- 接收到单元时的回调函数  def CTYBot_ReportResult_CallBack( strFromName, param1, param2, recvCTUnit, execCallBackUnit)
    # start by sk. 170222
    def Register_CTUnit_CallBack(self, iDataType, iMainCmd, iSubCmd, param1, param2, funcCreateNewCTUnit, funcRecvCTUnitCallBack):
        self.s_clientP2PExec.ExCall_Register_CallBackFunc( iDataType, iMainCmd, iSubCmd, param1, param2, funcCreateNewCTUnit, funcRecvCTUnitCallBack)

    # 注册 通用IntStr的 数据回调函数
    # start by sk. 170222
    def Register_CommStrInt_CallBack(self, funcCommStrIntRecvCallBack, runParam1=None, runParam2=None):
        # 注册 － 通用数据回传
        self.s_clientP2PExec.ExCall_Register_CallBackFunc(CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask,
                                                       CTYLB_Bot_BaseDef.s_g_iMainCmd_CommonTask_SingleData,
                                                       CTYLB_Bot_BaseDef.s_g_iSubCmd_CommonTask_SingleData,
                                                       0, 0,
                                                       CTYBot_CTUnit_Common_CreateNewUnit_CommonData,
                                                       funcCommStrIntRecvCallBack)
        pass

    # 注册 通用IntStr的 数据回调函数
    # start by sk. 170222
    def Register_CommStrInt_SubCmd_Range_CallBack(self, funcCommStrIntRecvCallBack, iSubCmd_Start,
                                                  iSubCmd_End=CTYLB_Bot_G_CallBack_DefUnit.s_g_iSubRange_ALL_Valid):
        self.s_clientP2PExec.ExCall_Register_SubCmd_Range_CallBackFunc( CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask,
                                                                        CTYLB_Bot_BaseDef.s_g_iMainCmd_CommonTask_SingleData,
                                                                        iSubCmd_Start, iSubCmd_End, 0, 0,
                                                                        CTYBot_CTUnit_Common_CreateNewUnit_CommonData,
                                                                        funcCommStrIntRecvCallBack)
        pass

    # 不断调用
    # start by sk. 170302
    def ExecTimerCheck(self):
        bTaskBusy = False
        if (self.s_tylbBaseClient.Run_TimerCheck()):
            bTaskBusy = True
        # 客户端单元调度运行检测
        if (self.s_clientP2PExec.Vil_Run_TimeCheck()):
            bTaskBusy = True
        # 执行时间检查的回调函数
        if (self.s_funcTimerCheckCallBack and self.s_funcTimerCheckCallBack()):
            bTaskBusy = True
        if (self._Vilu_TimerCheck()):
            bTaskBusy = True
        return bTaskBusy

    # 运行前的准备 - 子类可继承
    # start by sk. 170226
    def Vilu_Prepare_Run(self, ustrCfgFileName):
        self.s_clientP2PExec.Vil_Run_Prepare()
        self.s_tylbBaseClient.PrePare_Run()
        return

    # 退出的准备 - 子类可继承
    # start by sk. 170302
    def Vilu_Prepare_Quit(self):
        self.s_clientP2PExec.Vil_Run_Stop()
        self.s_tylbBaseClient.StopRun()
        return

    # 单位时间调度 - 子类可继承
    # start by sk. 170226
    def _Vilu_TimerCheck(self):
        return False
        pass

    # 发送数据单元到目标用户
    # start by sk. 170222
    def SendCTUnitToUser(self, bstrDestUser, sendCTUnit):
        self.s_clientP2PExec.ExCall_Prompt_Unit_To_Send(bstrDestUser, sendCTUnit)

    # 发送整数值－通用单元给指定用户，返回发送的唯一符
    # start by sk. 170222
    def SendToUser_IntValue(self, bstrDestUser, iValue, bstrParam1=b'', bstrParam2=b''):
        sendCommUnit = CTYBot_CTUnit_CommonData()
        sendCommUnit.SetIntData(iValue)
        sendCommUnit.SetParam(bstrParam1, bstrParam2)
        self.s_clientP2PExec.ExCall_Prompt_Unit_To_Send(bstrDestUser, sendCommUnit)
        return sendCommUnit.s_strUniqueSign

    # 发送字符串值－通用单元到目标用户，返回发送的唯一符
    # start by sk. 170222
    def SendToUser_StrValue(self, strDestUser, strValue, strParam1='', strParam2=''):
        sendCommUnit = CTYBot_CTUnit_CommonData()
        sendCommUnit.SetStrData(strValue)
        sendCommUnit.SetParam(strParam1, strParam2)
        self.s_clientP2PExec.ExCall_Prompt_Unit_To_Send(strDestUser, sendCommUnit)
        return sendCommUnit.s_strUniqueSign

    pass


# tylb－p2p的  实际调用，模拟系统命令到达的回调处理。单元结构为：CTYBot_CTUnit_SimuSystemNotify
# start by sk. 170220
def CTYBot_Frame_SimuSystemNotify_CallBack(bstrFromName, paramBotExecFrame, paramBotFrameThread, simuSystemNotifyCTUnit, execCallBackUnit):
    iNotifyType = simuSystemNotifyCTUnit.s_iNotifyType
    iNotifyParam = simuSystemNotifyCTUnit.s_iNotifyParam
    strNotifyParam = simuSystemNotifyCTUnit.s_strNotifyParam

    if( iNotifyType == CTYBot_CTUnit_SimuSystemNotify.s_g_iType_Notify_Peer_Online):
        paramBotFrameThread.s_HLSockMang.Handle_SystemNotify_ClientStatus( iNotifyParam, strNotifyParam)
    elif(iNotifyType == CTYBot_CTUnit_SimuSystemNotify.s_g_iType_Notify_PeerServer_Restart):
        paramBotFrameThread.s_HLSockMang.Handle_SystemNotify_PeerServerRestart()

    pass


# ################################################################################################
#   重写 接收到 通用数据结构的回调处理  主命令，s_g_iMainCmd_CommonTask_SingleData
#           s_g_iSubCmd_CommonTask_SingleData # 子命令。
# ################################################################################################
# tylb－p2p的 实际调用，通用数据结构的回调处理。单元结构为：CTYBot_CTUnit_CommonData
# start by sk. 170220
def CTYBot_Frame_CommonData_CallBack(bstrFromName, param1, param2, commDataCTUnit, execCallBackUnit):
    if (commDataCTUnit.s_iType == CTYBot_CTUnit_CommonData.s_g_iType_int):
        CTYLB_Log.ShowLog(0, 'common-callback', '>>> exactly, data receive %d - %d' % (commDataCTUnit.s_strParam1, commDataCTUnit.s_iValue))
    elif (commDataCTUnit.s_iType == CTYBot_CTUnit_CommonData.s_g_iType_string):
        CTYLB_Log.ShowLog(0, 'common-callback', '>>> exactly, data receive: [%s]' % (commDataCTUnit.s_strValue))
    else:
        CTYLB_Log.ShowLog(0, 'common-callback', 'unknown data receive, type:%d' % (commDataCTUnit.s_iType))
    pass

# tylb－p2p的  实际调用，高层管套会话的回调处理。单元结构为：CTYBot_CTUnit_HLSockSession
# start by sk. 170220
def CTYBot_Frame_HLSockSession_CallBack(strFromName, paramBotExecFrame, paramBotFrameThread, hlSockSessionCTUnit, execCallBackUnit):
    if( paramBotExecFrame):
        subUnitReal = paramBotExecFrame.s_clientP2PExec.s_p2p_ChatMain_SubUnitReal
        hlSockSessionCTUnit.RestoreCTUnitArrayFromBuff( subUnitReal)
    # 对单元每个缓冲进行处理
    if( paramBotFrameThread):
        paramBotFrameThread.s_HLSockMang.HandleRecvHLSessionCTUnit( strFromName, hlSockSessionCTUnit)
    pass

# 天元机器人线程执行实现框架
# start by sk. 170302
class CLessTYBotFrameThread(threading.Thread):
    def __init__(self, strCfgFileName, strDbFileName):
        threading.Thread.__init__(self)
        self.s_bRunning = True
        self.s_cfgFileName = strCfgFileName
        self.s_execTYLB_Bot_Sample = CTylb_Bot_Exec_Frame( None, strCfgFileName, strDbFileName)
        self.s_CtrlCQuit = None
        self.s_HLSockMang = CTYBot_HL_Sock_Mang(self.s_execTYLB_Bot_Sample)
        pass

    # 准备，并且启动
    def RegisterNewCTUnit(self, iDataType, iMainCmd, iSubCmd, funcCreateNewCTUnit):
        self.s_execTYLB_Bot_Sample.Register_CTUnit_CallBack( iDataType, iMainCmd, iSubCmd, None, None, funcCreateNewCTUnit, None)
        pass

    # 准备，并且启动
    def Prepare_Start(self):
        # 准备运行
        self.s_execTYLB_Bot_Sample.Vilu_Prepare_Run( self.s_cfgFileName)
        # 注册 通用数据到达 回调函数
        self.s_execTYLB_Bot_Sample.Register_CommStrInt_CallBack( CTYBot_Frame_CommonData_CallBack, self.s_execTYLB_Bot_Sample, self)
        # 注册 管套会话实现 回调函数
        self.s_execTYLB_Bot_Sample.Register_CTUnit_CallBack( CTYLB_Bot_BaseDef.s_g_iDataType_HLSockSession,
                                                             CTYLB_Bot_BaseDef.s_g_iMainCmd_HLSockSession,
                                                             CTYLB_Bot_BaseDef.s_g_iSubCmd_HLSockSession,
                                                             self.s_execTYLB_Bot_Sample, self,
                                                             CTYBot_CTUnit_CreateNewUnit_HLSessionSock,
                                                             CTYBot_Frame_HLSockSession_CallBack)
        # 注册 模拟系统命令 回调函数
        self.s_execTYLB_Bot_Sample.Register_CTUnit_CallBack( CTYLB_Bot_BaseDef.s_g_iDataType_SimuSystemNotify,
                                                             CTYLB_Bot_BaseDef.s_g_iMainCmd_SimuSystemNotify,
                                                             CTYLB_Bot_BaseDef.s_g_iSubCmd_SimuSystemNotify,
                                                             self.s_execTYLB_Bot_Sample, self,
                                                             CTYBot_CTUnit_CreateNewUnit_SimuSystemNotify,
                                                             CTYBot_Frame_SimuSystemNotify_CallBack)
        # 设置本线程，启动
        self.setDaemon(True)
        self.start()
        pass

    # 运行线程
    def run(self):
        iFreeCount = 0
        while( self.s_bRunning):
            bTaskBusy = False
            if( self.s_execTYLB_Bot_Sample.ExecTimerCheck()):
                bTaskBusy = True
            if( self.s_HLSockMang.TimerCheck()):
                bTaskBusy = True

            if(not bTaskBusy):
                iFreeCount += 1
                if(iFreeCount > g_iMaxExecIdleCount):
                    time.sleep(0.01)
            else:
                iFreeCount = 0

        self.s_HLSockMang.SelfMangAllQuit()
        self.s_execTYLB_Bot_Sample.Vilu_Prepare_Quit()
        pass

    # 安全退出
    def SafeStop(self):
        self.s_bRunning = False
        pass

    # 获得我的名字
    # start by sk. 170307
    def GetMyName( self):
        return self.s_execTYLB_Bot_Sample.s_clientP2PExec.s_strMyName

    # 注册 默认的控制台兼容 和 Ctrl_C 的处理
    # start by sk. 170222
    @staticmethod
    def SetDefaultConsoleCompatible( funcCtrlCHandle):
        CTYLB_MainSys_MiscFunc.SetConsoleCompatible()
        # 登记异常处理函数
        import signal
        signal.signal(signal.SIGINT, funcCtrlCHandle)
        signal.signal(signal.SIGTERM, funcCtrlCHandle)

    pass
