# api_test.py
# python Fiber API单元 测试程序1
# start by sk. 180510

import time
from TYBotUtilsSDK2.Log.log_and_monitor import CTYLB_Log, CSkBot_Common_Share
from TYBotSDK2.FiberFBot.PyFiber_BrainCore_API import PyExCallAPI_Base, Global_TinyBrainCore

g_iExecCmd=100  # 执行的命令ID, 100以上

class pyAPI_NLK(PyExCallAPI_Base):

    strNLKAnalyerName="lessnet.FiberExec.NLKer"
    lMsgID_NLKer_SenterToWord=100001  # strParam文字内容, 回复:strValue分词json

    def __init__(self):
        PyExCallAPI_Base.__init__(self)
        pass

    def ExecNLK(self, strInput):
        execCmd=self.ExecFiberCmd( strDestFiberName=self.strNLKAnalyerName, messageID=self.lMsgID_NLKer_SenterToWord,
                                   strMsgParam=strInput)
        return execCmd.s_strRetValue


if __name__ == "__main__":
    Global_TinyBrainCore.InitBrainCore()

    stringArray=["这是一个测试单词句子", "中国的GDP正在持续增长", "今天太阳高照明天马路繁忙"]
    pyAPIExec = pyAPI_NLK()

    timerSend = CSkBot_Common_Share.CSkBot_TimeIdentify()

    while(Global_TinyBrainCore.IsGlobalRunning()):
        if(timerSend.CheckTimeDiff()):
            for eachStr in stringArray:
                strValue=pyAPIExec.ExecNLK(eachStr)
                CTYLB_Log.ShowLog(0, "result", strValue)
                pass

        time.sleep(0.1)
        Global_TinyBrainCore.TimerCheck()
