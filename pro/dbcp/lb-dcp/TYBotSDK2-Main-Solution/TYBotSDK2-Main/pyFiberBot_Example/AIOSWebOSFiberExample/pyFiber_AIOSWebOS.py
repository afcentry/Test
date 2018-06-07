from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log,CSkBot_Common_Share
from TYBotSDK2.FiberFBot.FbTBot_UTRC_Client import TYFiberBot_Mang_NATS_UTRClient_Instance
from TYBotSDK2.FiberFBot.FiberMangReal import FiberUnit_Base,FiberGroupUnit_Base,FiberMsgRet

import requests

class HttpPoster:
    '''
    API数据提交帮助类，实现Json字符串数据的Post提交
    '''

    #数据提交地址URL
    ApiUrl="http://192.168.10.116:6000/data/post"
    Headers={"Content-Type":"application/json"}
    @staticmethod
    def Post(jsonDataString,retryCount=1,timeout=3):
        '''
        提交数据到API接口
        :param jsonDataString: 需要提交的数据，Json字符串编码
        :param retryCount: 失败重试次数
        :param timeout: 提交超时时间，单位秒
        :return: 成功返回True,失败返回False
        '''

        CTYLB_Log.ShowLog(0, "准备发送-post", jsonDataString)
        jsonDataString=jsonDataString.encode('utf-8')
        while retryCount>0:

            try:
                res = requests.post(HttpPoster.ApiUrl,headers=HttpPoster.Headers, data=jsonDataString, timeout=timeout)
                return True
            except Exception as e:
                retryCount = retryCount - 1
                if retryCount==0:
                    CTYLB_Log.ShowLog(2,AIOSWebOSFiber.FiberName,"POST数据到WEB OS后台展示失败：{0}".format(e),1)
        return False

class AIOSWebOSFiber(FiberUnit_Base):
    '''
    AIOS基于WEB的OS用户操作界面显示控制Fiber
    '''

    CommandID=100  #执行命令的ID，100以上
    FiberName="PyFiberAIOSWebOS"  #功能Fiber的唯一ID
    # 是否启用Post数据提交，若不启用，则Post操作不会做任何事情
    EnablePost=False

    def __init__(self):
        super(AIOSWebOSFiber, self).__init__(AIOSWebOSFiber.FiberName,bExRemoteCallMe=True)
        self.sendTimeIdentify=CSkBot_Common_Share.CSkBot_TimeIdentify(10)   #10秒发送超时检测

    def v_OnInit(self):
        CTYLB_Log.ShowLog(0,AIOSWebOSFiber.FiberName,"OnInit")
        #TODO:其他初始化操作...

    def v_OnClose(self):
        CTYLB_Log.ShowLog(0,AIOSWebOSFiber.FiberName,"OnClose")
        #TODO:其他删除操作...

    def OnMessage(self,fromSenderUnit,strMsgJsonParam,strMsgParam,lMsgParam1,lMsgParam2):
        CTYLB_Log.ShowLog(0,AIOSWebOSFiber.FiberName,"recv {0} message, json:{1}, msg:{2}"
                          .format(fromSenderUnit.s_strFullTaskName,strMsgJsonParam,strMsgParam))
        if AIOSWebOSFiber.EnablePost:
            HttpPoster.Post(strMsgParam)
        msgRet=FiberMsgRet(strRetValue=strMsgParam+"->AIOS指令执行回复",lRetValue=lMsgParam1,lRetValue2=lMsgParam2)
        return msgRet

    def v_Base_TimerCheck(self):
        return False

    def v_HandleMessage(self, fromSenderUnit, messageID, strMsgJsonParam, strMsgParam, lMsgParam1, lMsgParam2):
        fiberMsgRet=FiberUnit_Base.v_HandleMessage(self,fromSenderUnit,messageID,strMsgJsonParam,strMsgParam,lMsgParam1,lMsgParam2)

        if messageID==AIOSWebOSFiber.CommandID:
            fiberMsgRet=self.OnMessage(fromSenderUnit,strMsgJsonParam,strMsgParam,lMsgParam1,lMsgParam2)

        return fiberMsgRet

    @staticmethod
    def Run():
        timeIdentify=CSkBot_Common_Share.CSkBot_TimeIdentify()
        utrcClinet=TYFiberBot_Mang_NATS_UTRClient_Instance()
        utrcClinet.AddFiberUnit(AIOSWebOSFiber())
        utrcClinet.Run()

if __name__ == '__main__':
    AIOSWebOSFiber.Run()