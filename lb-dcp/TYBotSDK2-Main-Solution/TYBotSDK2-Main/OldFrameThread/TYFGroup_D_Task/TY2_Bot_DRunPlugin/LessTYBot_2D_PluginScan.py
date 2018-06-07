# -*- coding:UTF-8 -*- 放到第一行标记
# LessTYBot_D_PluginScan.py 外部插件实现代码
#
# start by sk. 170223

from BotPlugin.Sk_LB_Cfg_RemoteClient import CSkLB_Config_RemoteClient_BaseDef
from BotPlugin.Sk_LB_Bee_Exec_Cmd_Func import CTYLB_Sk_Plugin_BeeExecCmd
from BotPlugin.getEnterpriseName import GetEnterPriseNameStepResult
from BotPlugin.enter2domains import GetEnterPriseName_To_DomainName


# 回调，进行调度运行 每个子任务.允许出现一分钟之内的堵塞。如果堵塞太久，会导致Ctrl+C等待长时间才退出
# start by sk. 170213
def CTYBot_ExecPlugin_Each_CallBack_RunParam( iPluginID, strDestHost):
    iReplyPluginID = 0
    strRunResult = u''
    if (iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_PingCmd):
        # print 'exec ping [%s]' % (strContent)
        strRunResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_PingCmd_EachHost(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_PingCmd_Reply
    elif (iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_Web_Crawl):
        # strResultArray = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_WebCrawl(strDestHost, IsGlobalStopExit)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_Web_Crawl_Reply
        # print 'exec web-crawl ' + strContent
    elif (iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_Tracert):
        strRunResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_TraceRoute_EachHost(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_Tracert_Reply
    elif (iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_DigDNS):
        strRunResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_DnsDig_EachHost(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_Tracert_Reply

    elif( iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_Enterprise_Name):   # 获取企业列表
        strRunResult = GetEnterPriseNameStepResult(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_Enterprise_Name_Reply

    elif( iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_Enterprise_Domain_Name):   # 获取企业名对应的域名
        strRunResult = GetEnterPriseName_To_DomainName(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_Enterprise_Domain_Name_Reply

    elif( iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_SubdomainDig):   # 获取域名对应子域名
        strRunResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_SubdomainDig_EachHost(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_SubdomainDig_Reply

    elif( iPluginID == CSkLB_Config_RemoteClient_BaseDef.s_iExec_DomainIP):   # 获取域名对应IP
        strRunResult = CTYLB_Sk_Plugin_BeeExecCmd.Bee_Exec_DomainIP_EachHost(strDestHost)
        iReplyPluginID = CSkLB_Config_RemoteClient_BaseDef.s_iExec_DomainIP_Reply

    # 提交结果进行发送
    return iReplyPluginID, strRunResult

# 回调，获得支持的插件ID列表
# start by sk. 170309
def CTYBot_ExecPlugin_GetSupportIDArray():
    retArray = [
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_PingCmd,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_Web_Crawl,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_Tracert,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_DigDNS,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_Enterprise_Name,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_Enterprise_Domain_Name,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_SubdomainDig,
        CSkLB_Config_RemoteClient_BaseDef.s_iExec_DomainIP,
        ]
    return retArray
