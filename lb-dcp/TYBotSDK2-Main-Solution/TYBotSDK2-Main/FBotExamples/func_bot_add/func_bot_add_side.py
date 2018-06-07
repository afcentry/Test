from TYBotSDK2.FBot.fbotV2 import FBot
from TYBotSDK2.FBot.global_define import *
import time

#实现关于OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT指令结果的回调
def connect_request_exec_callback(value, param1,param2,is_last_package):
    print("[*]Connect Request Callback:Value={0},Param1={1},Param2={2}".format(value,param1,param2))
    if "Add" in value:
        c=int(param1)+int(param2)
    else:
        c=-99999
    strNowTime = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    sendCTUnit=FBot.make_package(OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT,"","","插件模块计算结果为：{0} [{1}]".format(c,strNowTime))
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray

if __name__=="__main__":
    bot=FBot(name="FBotA",connect_to_socks={"BrainA":LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE})
    bot.add_connect_to_callbacks("BrainA",connect_request_exec_callback)
    bot.run()