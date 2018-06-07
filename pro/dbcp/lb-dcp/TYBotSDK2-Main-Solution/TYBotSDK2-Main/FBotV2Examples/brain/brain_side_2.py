from TYBotSDK2.FBot.fbotV2 import FBot

import time


class BrainWorker:
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

    def protocol_state_B(self, peerName, value, param1, param2, is_last_package):
        '''
        回调处理函数
        :param peerName: 回调任务远端节点名称
        :param value: 参数Value,内容由用户根据协议自定义
        :param param1: 参数Value,内容由用户根据协议自定义
        :param param2: 参数Value,内容由用户根据协议自定义
        :param is_last_package: 是否是最后一个数据包（处理的数据包可能是一批，也可能是单个）
        :return: 处理完成后需要发送应答的数据包或数据包List集合
        '''
        # print("[*]Protocol State B:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName, value,param1, param2))
        sendCTUnit = FBot.make_package(902, str(time.time()), "", "")
        retCTUnitArray = [sendCTUnit]
        return retCTUnitArray

    def protocol_state_D(self, peerName, value, param1, param2, is_last_package):
        print(
            "[*]Protocol State D:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName, value, param1, param2))
        sendCTUnit = FBot.make_package(904, "", "", "")
        retCTUnitArray = [sendCTUnit]
        return retCTUnitArray

    def protocol_state_B2(self, peerName, value, param1, param2, is_last_package):
        # print("[*]Protocol State B2:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName, value,param1, param2))
        sendCTUnit = FBot.make_package(1102, str(time.time()), "", "")
        retCTUnitArray = [sendCTUnit]
        return retCTUnitArray

    def protocol_state_D2(self, peerName, value, param1, param2, is_last_package):
        print(
            "[*]Protocol State D2:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName, value, param1, param2))
        sendCTUnit = FBot.make_package(1104, "", "", "")
        retCTUnitArray = [sendCTUnit]
        return retCTUnitArray

    def protocol_state_E2(self, peerName, value, param1, param2, is_last_package):
        print(
            "[*]Protocol State E2:PeerName={0},Value={1},Param1={2},Param2={3}".format(peerName, value, param1, param2))
        sendCTUnit = FBot.make_package(1106, "", "", "")
        retCTUnitArray = [sendCTUnit]
        return retCTUnitArray

    def listen_accept_callback(self, **kwargs):
        for key in kwargs:
            print(key, kwargs[key])

    def start(self):
        bot = FBot(listen_socks=[900, 1100], listen_accpet_callback=self.listen_accept_callback, report_status=True,
                   comment="任务大脑调度")
        bot.add_listen_callbacks(901, self.protocol_state_B)
        bot.add_listen_callbacks(903, self.protocol_state_D)
        bot.add_listen_callbacks(1101, self.protocol_state_B2)
        bot.add_listen_callbacks(1103, self.protocol_state_D2)
        bot.add_listen_callbacks(1105, self.protocol_state_E2)
        bot.run()


if __name__ == "__main__":
    brain = BrainWorker()
    brain.start()
