from TYBotSDK2.FBot.fbotV2 import FBot
from TYBotSDK2.FBot.global_define import *
import time

#实现关于OP_ACTION_BRAIN_SUB_CMD_REQUEST_EXEC指令的回调
def listen_request_exec_callback(peerName,value, param1,param2,is_last_package):
    print("[*]Listen Request Exec Callback:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName, value,                                                                                                  param1, param2))
    sendCTUnit =FBot.make_package(OP_ACTION_BRAIN_SUB_CMD_REPLY_REQUEST_EXEC,"Do Add Task", "100", "200" )
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray

#实现关于OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT指令的回调
def listen_reply_request_exec_callback(peerName,value, param1,param2,is_last_package):
    print("[*]Listen Reply Request Exec Callback:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName,value, param1, param2))
    sendCTUnit =FBot.make_package(OP_ACTION_BRAIN_SUB_CMD_REPLY_REPLY_EXEC_RESULT, "", "", "")
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray

if __name__=="__main__":
    bot=FBot(name="BrainA",listen_mode=True,listen_operate_id=LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE)
    bot.add_listen_callbacks(str(OP_ACTION_BRAIN_SUB_CMD_REQUEST_EXEC), listen_request_exec_callback)
    bot.add_listen_callbacks(str(OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT), listen_reply_request_exec_callback)
    bot.run()