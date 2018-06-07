from TYBotSDK2.FBot.fbotV2 import FBot
from TYBotSDK2.FBot.global_define import *
import time

'''
用例交互协议说明：
场景描述：FBotA主动连接BrainA，并向A发起任务
请求（协议ID901），BrainA收到任务请求，把任务
内容发送给FBotA执行（协议ID902），FBotA执行
完任务后，把任务结果发送给BrainA（协议ID903）
，BrainA接收到任务结果后回复确认（协议ID904）
======================================

FBotA      <FBotA主动发送>       BrainA

State A:处理901,发送901
------------------------------------->
            State B:处理901,发送902
<-------------------------------------
State C:处理902,发送903
------------------------------------->
            State D:处理903,发送904
<-------------------------------------
              ....
======================================
'''


def protocol_state_C(value, param1, param2, is_last_package):
    print("[*]Protocol State C:Value={0},Param1={1},Param2={2}".format(value, param1, param2))

    strNowTime = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    sendCTUnit = FBot.make_package(903, "", "", "插件1模块计算结果为：{0} [{1}]".format(value, strNowTime))
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray


def protocol_state_A(value, param1, param2, is_last_package):
    # print("[*]Protocol State A:Value={0},Param1={1},Param2={2}".format(value,param1,param2))

    sendCTUnit = FBot.make_package(901, "", "", "")
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray


def protocol_state_C2(value, param1, param2, is_last_package):
    print("[*]Protocol State C2:Value={0},Param1={1},Param2={2}".format(value, param1, param2))

    strNowTime = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    sendCTUnit = FBot.make_package(1103, "", "", "插件2模块计算结果为：{0} [{1}]".format(value, strNowTime))
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray


def protocol_state_A2(value, param1, param2, is_last_package):
    # print("[*]Protocol State A2:Value={0},Param1={1},Param2={2}".format(value,param1,param2))

    sendCTUnit = FBot.make_package(1101, "", "", "")
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray


def protocol_state_E2(value, param1, param2, is_last_package):
    print("[*]Protocol State E2:Value={0},Param1={1},Param2={2}".format(value,param1,param2))

    sendCTUnit = FBot.make_package(1105, "自定义协议哦", "是的", "没错")
    retCTUnitArray = [sendCTUnit]
    return retCTUnitArray


if __name__ == "__main__":
    bot = FBot(connect_to_socks={"BrainA": [900, 1100]}, report_status=True, comment="执行加法计算")
    bot.add_connect_to_callbacks("BrainA", 900, 901, protocol_state_A, True)
    bot.add_connect_to_callbacks("BrainA", 900, 902, protocol_state_C, False)

    bot.add_connect_to_callbacks("BrainA", 1100, 1101, protocol_state_A2, True)
    bot.add_connect_to_callbacks("BrainA", 1100, 1102, protocol_state_C2, False)
    bot.add_connect_to_callbacks("BrainA", 1100, 1104, protocol_state_E2, False)
    bot.run()
