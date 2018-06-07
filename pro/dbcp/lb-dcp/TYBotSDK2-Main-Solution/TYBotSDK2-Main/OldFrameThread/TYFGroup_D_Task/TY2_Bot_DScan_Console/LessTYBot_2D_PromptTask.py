# -*- coding:UTF-8 -*- 放到第一行标记
# LessTYBot_2D_PromptTask.py 分布任务提交机器人
#
# start by sk. 170223

from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log
from Tylb_Bot_Sock_Prompt_D_Task import CTYBot_Sock_D_PromptTask, CTYBot_WebName_DTask2_Base, CTYFBot_DTask_OPDB_Prompter
from datetime import datetime
import os
import sys
import time

s_iExec_PingCmd = 1  # 需要执行Ping命令
s_iExec_PingCmd_Reply = 2  # 执行Ping命令 回复
s_iExec_Web_Crawl = 3  # 需要执行Web爬虫
s_iExec_Web_Crawl_Reply = 4  # 需要执行Web爬虫  回复
s_iExec_Tracert = 5  # 需要执行路由跟踪
s_iExec_Tracert_Reply = 6  # 需要执行路由跟踪 回复
s_iExec_DigDNS = 7  # 执行dns获取
s_iExec_DigDNS_Reply = 8  # 执行dns获取 回复

s_iExec_Enterprise_Name = 100  # 获取企业名称
s_iExec_Enterprise_Name_Reply = 101  # 获取企业名称 回复
s_iExec_Enterprise_Domain_Name = 102  # 根据企业名称获取企业域名
s_iExec_Enterprise_Domain_Name_Reply = 103  # 根据企业名称获取企业域名 回复

s_iExec_SubdomainDig = 501  # 子域名挖掘
s_iExec_SubdomainDig_Reply = 502  # 子域名挖掘 回复

s_iExec_DomainIP = 503  # 域名获取IP
s_iExec_DomainIP_Reply = 504  # 域名获取IP 回复

g_bSysRunning = True   # 系统运行标识

class CTYFBot_D_OPDB_GetEnterPriseDomainName( CTYFBot_DTask_OPDB_Prompter):
    def __init__(self, hlSockMang, iEachBlockCount=50):
        strTaskAppName = 'Get_EnterPrise_DomainName'
        strSubTaskName = datetime.now().strftime('%Y_%m_%d#%H_%M_%S')
        strDBName = 'ty2_zhl_enterprises'
        strTableName = 'ty2_enterprises'
        strFieldName = 'name'
        strParamSignIDField = 'id'
        CTYFBot_DTask_OPDB_Prompter.__init__(self, hlSockMang, strTaskAppName, strSubTaskName, 'GetEnterPriseDomain',
                                             strDBName, strTableName, strFieldName, strParamSignIDField,
                                             s_iExec_Enterprise_Domain_Name, iEachBlockCount)
        pass


class CTYFBot_D_OPDB_GetPing( CTYFBot_DTask_OPDB_Prompter):
    def __init__(self, hlSockMang, iEachBlockCount=50):
        strTaskAppName = 'PingDomainName_GetIP'
        strSubTaskName = datetime.now().strftime('%Y_%m_%d#%H_%M_%S')
        strDBName = 'ty2_zhl_enterprises'
        strTableName = 'ty2_enterprises'
        strFieldName = 'name'
        strParamSignIDField = 'id'
        CTYFBot_DTask_OPDB_Prompter.__init__(self, hlSockMang, strTaskAppName, strSubTaskName, 'GetPingIP',
                                             strDBName, strTableName, strFieldName, strParamSignIDField,
                                             s_iExec_PingCmd, iEachBlockCount)
        pass


'''

# 获得企业列表名字对应的域名
# start by sk. 170328
class CTYBot_D_GetEnterPriseDomainName(CTYBot_WebName_DTask2_Base):
    def __init__(self, strRunTaskLineFile, iEachBlockCount):
        CTYBot_WebName_DTask2_Base.__init__(self, s_iExec_Enterprise_Domain_Name, strRunTaskLineFile, iEachBlockCount)
        pass

    # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无
    def Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID):
        CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID)
        pass

    # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容
    def Viul_Internal_ParamBlock_ReadEach(self):
        strRetParamUnitArray = CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_ReadEach(self)

        return strRetParamUnitArray

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult)

        with open('d_task/result/enterprisename_domain.txt', 'a+') as resultFile:
            strLine = '\r\n>>>[%s][%s][%d]\r\n' % (
               datetime.now().strftime('%y-%m-%d %H:%M:%S'), strOrigDomain, iReplyPluginID)
            strWriteFileResult = '**--**: %s' % (strResult)
            resultFile.write(strWriteFileResult)
    pass

# 获取企业名字列表任务插件
# start by sk. 170328
class CTYBot_D_GetEnterpriseName(CTYBot_WebName_DTask2_Base):
    def __init__(self, iEachBlockCount):
        self.s_iLastParamIndex = 0
        CTYBot_WebName_DTask2_Base.__init__(self, s_iExec_Enterprise_Name, '', iEachBlockCount)
        pass

    # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无
    def Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID):
        # CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID)
        pass

    # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容
    def Viul_Internal_ParamBlock_ReadEach(self):
        # strRetParamUnitArray = CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_ReadEach(self)
        strRetParamUnitArray = []
        for i in range(self.s_iEachParamBlockCount):
            strEachUnit = '%d' % (self.s_iLastParamIndex)
            self.s_iLastParamIndex += 1
            strRetParamUnitArray.append(strEachUnit)

        return strRetParamUnitArray

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult)

        with open('d_task/result/run_tracert.txt', 'a+') as resultFile:
            strLine = '\r\n>>>[%s][%s][%d]\r\n' % (
               datetime.now().strftime('%y-%m-%d %H:%M:%S'), strOrigDomain, iReplyPluginID)
            resultFile.write(strLine)
            strWriteFileResult = '**--**: %s' % (strResult)
            resultFile.write(strWriteFileResult)
    pass


# Tracert 任务请求分配
# start by sk. 170226
class CTYBot_D_TracertTask(CTYBot_WebName_DTask2_Base):
    def __init__(self, strRunTaskLineFile, iEachBlockCount):
        CTYBot_WebName_DTask2_Base.__init__(self, s_iExec_Tracert, strRunTaskLineFile, iEachBlockCount)
        pass

    # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无
    def Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID):
        CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID)
        pass

    # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容
    def Viul_Internal_ParamBlock_ReadEach(self):
        strRetParamUnitArray = CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_ReadEach(self)

        return strRetParamUnitArray

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult)

        with open(os.path.join(os.path.dirname( os.path.realpath(__file__)),"d_task/result/run_tracert.txt"), 'a+') as resultFile:
            strLine = '\r\n>>>[%s][%s][%d]\r\n' % (
               datetime.now().strftime('%y-%m-%d %H:%M:%S'), strOrigDomain, iReplyPluginID)
            resultFile.write(strLine)
            resultFile.write(strResult)
    pass


#子域名挖掘任务分配
#pxk 2017年3月30日17:31:10
class CTYBot_D_GetSubdomain(CTYBot_WebName_DTask2_Base):
    def __init__(self,strRunTaskLineFile, iEachBlockCount):
        self.s_iLastParamIndex = 0
        CTYBot_WebName_DTask2_Base.__init__(self, s_iExec_SubdomainDig,strRunTaskLineFile,iEachBlockCount)
        pass

        # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无

    def Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID):
        CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID)
        pass

        # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容

    def Viul_Internal_ParamBlock_ReadEach(self):
        strRetParamUnitArray = CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_ReadEach(self)

        return strRetParamUnitArray

        # 当运行结果到达的通知

    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain,
                                                              strResult)

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult)

        with open('d_task/result/subdomain.txt', 'a+') as resultFile:
            strLine = '\r\n>>>[%s][%s][%d]\r\n' % (
               datetime.now().strftime('%y-%m-%d %H:%M:%S'), strOrigDomain, iReplyPluginID)
            resultFile.write(strLine)
            strWriteFileResult = '**--**: %s' % (strResult)
            resultFile.write(strWriteFileResult)
    pass

#域名获取IP
#pxk 2017年3月30日17:31:10
class CTYBot_D_GetDomainIp(CTYBot_WebName_DTask2_Base):
    def __init__(self,strRunTaskLineFile, iEachBlockCount):
        self.s_iLastParamIndex = 0
        CTYBot_WebName_DTask2_Base.__init__(self, s_iExec_DomainIP, strRunTaskLineFile, iEachBlockCount)
        pass

        # [子类可继承实现] - 内部调用－ 准备参数块。 返回：无

    def Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID):
        CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_PrePare(self, strTaskCenterID)
        pass

        # [子类可继承实现] - 内部调用－ 输出一个参数块. 返回：stringArray, 要提交扫描的目标数组，返回空表示无内容

    def Viul_Internal_ParamBlock_ReadEach(self):
        strRetParamUnitArray = CTYBot_WebName_DTask2_Base.Viul_Internal_ParamBlock_ReadEach(self)

        return strRetParamUnitArray

        # 当运行结果到达的通知

    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain,
                                                              strResult)

    # 当运行结果到达的通知
    def Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult):
        CTYBot_WebName_DTask2_Base.Viul_Notify_Recv_RunResult(self, strParamSign, iReplyPluginID, strOrigDomain, strResult)

        with open('d_task/result/domain_ip.txt', 'a+') as resultFile:
            strLine = '\r\n>>>[%s][%s][%d]\r\n' % (
               datetime.now().strftime('%y-%m-%d %H:%M:%S'), strOrigDomain, iReplyPluginID)
            resultFile.write(strLine)
            strWriteFileResult = '**--**: %s' % (strResult)
            resultFile.write(strWriteFileResult)
    pass
'''

# 中断处理函数
# start by sk. 170116
def CtrlCHandle( signum, frame):
    global g_bSysRunning
    CTYLB_Log.ShowLog(1, 'CTRL_C', "Ctrl+C Input, exiting")
    msgObject={
        "monitor_type":"status",
        "level":"error",
        "target":"",
        "plugin_id":-1,
        "block_id":"",
        "block_size":0,
        "free_size":0,
        "wait_size":0,
		"success_size":0,
        "result_code":0,
        "msg":"Ctrl+C keyboard detected, PLC exiting..."
        }
    CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
    g_bSysRunning = False

# 主程序入口
if __name__ == '__main__':
    msgObject={
        "monitor_type":"status",
        "level":"info",
        "target":"",
        "plugin_id":-1,
        "block_id":"",
        "block_size":0,
        "free_size":0,
        "wait_size":0,
		"success_size":0,
        "result_code":0,
        "msg":"PLC starting..."
        }
    CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
    iNextFileReadPos = 0

    iArgCount = len(sys.argv)
    if( iArgCount < 2):
        print('input run: [skip_block_count], default is 0')
    elif( iArgCount >= 2):
        iNextFileReadPos = int(sys.argv[1])

    msgObject={
        "monitor_type":"status",
        "level":"info",
        "target":"",
        "plugin_id":-1,
        "block_id":"",
        "block_size":0,
        "free_size":0,
        "wait_size":0,
		"success_size":0,
        "result_code":0,
        "msg":"PLC loading config..."
        }
    CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

    #获取配置文件路径及文件名，文件夹不存在则创建
    config_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),"config")
    config_file= os.path.join(config_dir,"config.ini")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.isfile(config_file):
        CTYLB_Log.ShowLog(0, 'Main', '[%s] config file missing...Quit!' % g_strProgName)
        msgObject={
            "monitor_type":"status",
            "level":"error",
            "target":"",
            "plugin_id":-1,
            "block_id":"",
            "block_size":0,
            "free_size":0,
            "wait_size":0,
			"success_size":0,
            "result_code":0,
            "msg":"Config file not found, PLC exiting..."
            }
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
        #配置文件不存在，直接退出
        os._exit(-1)

    msgObject={
        "monitor_type":"status",
        "level":"info",
        "target":"",
        "plugin_id":-1,
        "block_id":"",
        "block_size":0,
        "free_size":0,
        "wait_size":0,
		"success_size":0,
        "result_code":0,
        "msg":"PLC loading local data..."
        }
    CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

    db_dir=os.path.join(os.path.dirname(os.path.realpath(__file__)),"db")
    db_file= os.path.join(db_dir,"data.db")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 创建机器人框架
    g_execTYLB_SockBot_Req_DTask_Frame = CTYBot_Sock_D_PromptTask( config_file, db_file)
    # 设置默认环境处理
    g_execTYLB_SockBot_Req_DTask_Frame.s_LessTYLB_Bot_FrameThread.SetDefaultConsoleCompatible( CtrlCHandle)

    # 增加参数
    # opdbGetEntpriseDomainTask = CTYFBot_D_OPDB_GetEnterPriseDomainName(g_execTYLB_SockBot_Req_DTask_Frame.s_hlSockMang)
    # g_execTYLB_SockBot_Req_DTask_Frame.PromptDTask( opdbGetEntpriseDomainTask)
    pingTask = CTYFBot_D_OPDB_GetPing( g_execTYLB_SockBot_Req_DTask_Frame.s_hlSockMang)
    g_execTYLB_SockBot_Req_DTask_Frame.PromptDTask( pingTask)

    # 提交企业任务
    # botGetEnterpriseNameTask = CTYBot_D_GetEnterpriseName( 50)
    # g_execTYLB_SockBot_Req_DTask_Frame.PromptDTask( botGetEnterpriseNameTask)

    # 提交企业获取域名的任务
    #botGetEnterPriseDomainNameTask = CTYBot_D_GetEnterPriseDomainName('d_task/needtask/need_enterprise.txt', 50)
    #g_execTYLB_SockBot_Req_DTask_Frame.PromptDTask( botGetEnterPriseDomainNameTask)

    #botGetSubdomainTask = CTYBot_D_GetSubdomain('d_task/needtask/need_domains.txt', 50)
    #g_execTYLB_SockBot_Req_DTask_Frame.PromptDTask( botGetSubdomainTask)


    #botGetDomainIpTask = CTYBot_D_GetDomainIp('d_task/needtask/need_domains_ip.txt', 50)
    #g_execTYLB_SockBot_Req_DTask_Frame.PromptDTask( botGetDomainIpTask)

    # 准备运行
    g_execTYLB_SockBot_Req_DTask_Frame.Vilu_Prepare_Run( )

    msgObject={
        "monitor_type":"status",
        "level":"info",
        "target":"",
        "plugin_id":-1,
        "block_id":"",
        "block_size":0,
        "free_size":0,
        "wait_size":0,
		"success_size":0,
        "result_code":0,
        "msg":"PLC successfully started..."
        }
    CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

    # 运行
    while(g_bSysRunning):
        bTaskBusy = False
        if( g_execTYLB_SockBot_Req_DTask_Frame.Vilu_TimerCheck()):
            bTaskBusy = True
        if( not bTaskBusy):
            time.sleep(0.1)
    # 退出
    # opdbGetEntpriseDomainTask.Vilu_CloseQuit()
    pingTask.Vilu_CloseQuit()
    g_execTYLB_SockBot_Req_DTask_Frame.StopQuit()

    CTYLB_Log.ShowLog(0, 'Main', '[%s] bye bye' % ('d_task_Sock_Prompt_D_Task_main'))
    msgObject={
        "monitor_type":"status",
        "level":"error",
        "target":"",
        "plugin_id":-1,
        "block_id":"",
        "block_size":0,
        "free_size":0,
        "wait_size":0,
		"success_size":0,
        "result_code":0,
        "msg":"PLC  exited."
        }
    CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)
