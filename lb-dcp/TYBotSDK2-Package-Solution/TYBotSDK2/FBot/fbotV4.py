# ======================================================
# 功能机器人实现模块,实现功能机器人的高层封装。
# 对底层SDK进行更高层次封装，简化编写功能通讯机器人对难度。
#
# Pxk    2017-05-15
# fix add to v3. by sk. 180319
#
# add pyFiber纤程功能。by sk. 180413
# ======================================================

from TYBotSDK2.BotBase.Tylb_Bot_Sk_TaskReg_UnitDef import CTYBot_CTUnit_CommonData, CTYLB_Bot_BaseDef
from TYBotSDK2.P2PClient.Tylb_p2p_share import CTYLB_Log, CTYLB_MainSys_MiscFunc
from TYBotSDK2.BotBase.Tylb_Bot_Frame import CLessTYBotFrameThread
from TYBotSDK2.BotBase.Tylb_FBot_BaseFuncReal import CTYFBot_OpSession_ConnectSock
from .global_define import *
from TYBotSDK2.Utils.ini_config import get_config_value
from .bot_status import NodeStatus, SockInfo
import os
import time
import socket

IS_SYS_RUNNING=True

class FBotV4:
    def __init__(self, connect_to_socks=None, loop_event_callbacks=None, listen_socks=None,listen_accpet_callback=None,
                 config_file="config/config.yaml", report_status=False, report_interval=60, comment=""):
        '''
        功能Bot初始化对象
        :param connect_to_socks: 需要连接的套管对象集合，字典格式{"连接端的惟一ID":创建连接对应的指令值}
        :param loop_event_callbacks: 需要在每次主轮询时执行的函数回调集合，一般用于数据库检测操作,List集合
        :param listen_socks: 需要监听的套管对象ID集合，List格式[ID]
        :param config_file: 配置文件路径，默认为"./config/config.ini"
        :param report_status: 是否向节点状态监测节点发送节点状态信息:True-发送当前节点状态信息，False-不发送当前节点状态信息，默认为False
        :param report_interval: 状态汇报时间间隔，单位秒，默认60秒
        :param comment: 节点描述/备注，用于描述节点功能说明，默认为""
        '''
        # 功能Bot的名字，一般与配置文件中一致
        self.__bot_name = get_config_value(config_file, 'client.myid')
        self.__connect_to_socks = connect_to_socks if connect_to_socks else {}
        self.__listen_socks = listen_socks if listen_socks else []
        self.__listen_accept_callback=listen_accpet_callback
        self.__config_file = config_file
        self.__report_status = report_status
        self.__report_interval = report_interval
        self.__last_report_time = time.time()
        self.__node_comments = comment
        self.__connect_to_callbacks = {}
        self.__listen_callbacks = {}
        self.__loop_event_callbacks = loop_event_callbacks if loop_event_callbacks else []
        self.__node_status = NodeStatus(name=self.__bot_name, comment=self.__node_comments)
        # 增加节点当前状态汇报
        if self.__report_status:
            self.__add_report_status_sock_callbacks()

        assert (isinstance(self.__connect_to_socks, dict))
        if len(self.__listen_socks) < 1 and len(self.__connect_to_socks.keys()) <1:
            CTYLB_Log.ShowLog(2, "Error Sock Pipes",
                              "Connect to socks and Listen socks could not be zero at the same time.")
            exit(-1)
        # 需要发送到服务端的数据队列数组，可能连接到多个服务端，因此以字典形式存储每个对应的发送队列数组
        self.__connect_wait_to_send_arrays = {}
        # 监听模式下，只有一个监听行为
        # 监听模式下需要发送的数据队列数组
        self.__listen_wait_to_send_arrays = []
        # 初始化客户端发送队列数组
        for key in self.__connect_to_socks.keys():
            for port in self.__connect_to_socks[key]:
                if key not in self.__connect_wait_to_send_arrays.keys():
                    self.__connect_wait_to_send_arrays[key] = {}
                self.__connect_wait_to_send_arrays[key][port]=[]
                if self.__report_status:
                    sockInfo = SockInfo(name=key, operateId=self.__connect_to_socks[key])
                    obj = sockInfo.dump_obj()
                    key=CTYLB_MainSys_MiscFunc.SafeGetUnicode(key)
                    self.__node_status.SocksInfo['Socks'][key] = obj

    def add_connect_to_callbacks(self, sock_id,sock_port, cmd_id, callback,is_auto_callback=False):
        '''
        添加客户端连接数据交互回调处理函数
        :param sock_id: 对应的套管的客户端的唯一ID名
        :param sock_port: 对应的连接套管的端口号
        :param cmd_id: 回调对应的协议ID
        :param callback: 回调函数
        :param is_auto_callback: 是否为主动发送回调,主动发送的回调会定时自动触发. True-是主动触发回调, False-不是主动触发回调
        :return: 无
        '''
        assert int(cmd_id)
        assert callable(callback)
        if sock_id not in self.__connect_to_callbacks.keys():
            self.__connect_to_callbacks[sock_id] = {}
        if sock_port not in self.__connect_to_callbacks[sock_id].keys():
            self.__connect_to_callbacks[sock_id][sock_port] = {}

        if 'send' not in self.__connect_to_callbacks[sock_id][sock_port].keys():
            self.__connect_to_callbacks[sock_id][sock_port]['send'] = {}

        if 'recv' not in self.__connect_to_callbacks[sock_id][sock_port].keys():
            self.__connect_to_callbacks[sock_id][sock_port]['recv'] = {}

        if is_auto_callback:
            self.__connect_to_callbacks[sock_id][sock_port]['send'][cmd_id] = callback
        else:
            self.__connect_to_callbacks[sock_id][sock_port]['recv'][cmd_id] = callback




    def add_listen_callbacks(self, cmd, callback):
        '''
        添加服务端连接数据交互回调处理函数
        :param cmd: 回调函数对应的指令ID
        :param callback: 回调函数
        :return: 无
        '''
        assert int(cmd)
        assert callable(callback)

        self.__listen_callbacks[cmd] = callback

    def add_connect_to_send_package(self, sock_id, sock_port,package_data):
        '''
        向客户端通讯队列中添加需要发送的数据包
        :param sock_id: 管套唯一ID名称
        :param sock_port: 对应的通讯管道端口号
        :param package_data: 数据包
        :return: 无
        '''
        assert isinstance(package_data, type(CTYBot_CTUnit_CommonData))
        self.__connect_wait_to_send_arrays[sock_id][sock_port].append(package_data)

    #暂时无效函数，隐藏不暴露使用
    def __add_listen_send_package(self, package_data):
        '''
        项服务端通讯队列中添加需要发送的数据包
        :param package_data: 数据包
        :return: 无
        '''
        assert isinstance(package_data, type(CTYBot_CTUnit_CommonData))
        self.__listen_wait_to_send_arrays.append(package_data)

    @staticmethod
    def environment_event_handle(signum, frame):
        '''
        系统全局事件处理函数，主要处理Ctrl+C等终止事件
        '''
        CTYLB_Log.ShowLog(1, "Ctrl+C", "Ctrl+C keyboard event detected...[Exiting]")
        global IS_SYS_RUNNING
        IS_SYS_RUNNING = False

    @staticmethod
    def GetGlobalIsRunning():
        return IS_SYS_RUNNING

    @staticmethod
    def make_package(command_id, value="", param1="", param2=""):
        '''
        生成需要发送的数据包
        :param command_id: 整型值，一般用于填写指令ID
        :param value: 用户可自定义参数1,默认为""
        :param param1: 用户可自定义参数2,默认为""
        :param param2: 用户可自定义参数3,默认为""
        :return: 按照指定数据生成的数据包对象
        '''
        packageCTUnit = CTYBot_CTUnit_CommonData()
        packageCTUnit.SetIntData(command_id)
        packageCTUnit.SetParam(param1, param2)
        packageCTUnit.SetStrData(value)
        return packageCTUnit

    # 汇报节点状态回调任务
    def __add_report_status_sock_callbacks(self):
        # 实现关于OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT指令结果的回调,对需要汇报自身状态的任务进行状态结果回复
        def connect_request_exec_callback(value, param1, param2, is_last_package):
            # 更新状态更新时间
            self.__node_status.StatusTime = NodeStatus.get_now_timestamp()
            # 更新节点主机信息
            self.__node_status.NodeHostName = socket.gethostname()
            self.__node_status.NodeIPAddress = NodeStatus.get_all_avaliable_ip_address()
            self.__node_status.NodeMachineInfo = NodeStatus.get_machine_info()

            sendCTUnit = FBotV4.make_package(OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT, self.__node_status.dumps_json(),
                                           "", "")
            retCTUnitArray = [sendCTUnit]
            return retCTUnitArray

        def connect_request_exec_request_callback(value, param1, param2, is_last_package):
            retSendUnitArray = []

            sendCTUnit = CTYBot_CTUnit_CommonData()
            sendCTUnit.SetIntData(OP_ACTION_BRAIN_SUB_CMD_REQUEST_EXEC)
            sendCTUnit.SetParam(str(self.__connect_to_socks[TYFBOT_STATUS_MANAGER_IDENTIFY_NAME][0]), '')
            retSendUnitArray.append(sendCTUnit)

            if self.__connect_wait_to_send_arrays[TYFBOT_STATUS_MANAGER_IDENTIFY_NAME][LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE]:
                retSendUnitArray.extend(self.__connect_wait_to_send_arrays[TYFBOT_STATUS_MANAGER_IDENTIFY_NAME][LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE])
                self.__connect_wait_to_send_arrays[TYFBOT_STATUS_MANAGER_IDENTIFY_NAME][LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE] = []

            return retSendUnitArray

        self.__connect_to_socks[TYFBOT_STATUS_MANAGER_IDENTIFY_NAME] = [LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE]
        self.add_connect_to_callbacks(TYFBOT_STATUS_MANAGER_IDENTIFY_NAME,LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE,
                                      OP_ACTION_BRAIN_SUB_CMD_REQUEST_EXEC,
                                      connect_request_exec_request_callback,True)
        self.add_connect_to_callbacks(TYFBOT_STATUS_MANAGER_IDENTIFY_NAME, LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE,
                                      OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT,
                                      connect_request_exec_callback,False)



    def __listen_basic_handle(self, sockManager, clientSock, ctUnitArray):
        strPeerName, iPeerPort = sockManager.GetSockPeerAddr(clientSock)
        if isinstance(strPeerName, bytes):
            strPeerName = strPeerName.decode()
        retDataArray = []
        isNonePackageReply = True
        arrayLen = len(ctUnitArray)
        packageCount = 0
        for eachCTUnit in ctUnitArray:
            packageCount += 1
            eachRetCommCTUnitArray = []
            if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):

                if eachCTUnit.s_iValue in self.__listen_callbacks.keys():
                    eachRetCommCTUnitArray = self.__listen_callbacks[eachCTUnit.s_iValue](
                        CTYLB_MainSys_MiscFunc.SafeGetUnicode(strPeerName),
                        CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachCTUnit.s_strValue),
                        CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachCTUnit.s_strParam1),
                        CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachCTUnit.s_strParam2),
                        packageCount == arrayLen)

            if (eachRetCommCTUnitArray):
                isNonePackageReply = False
                retDataArray.extend(eachRetCommCTUnitArray)
        # 如果没有内容，那么，放一个空单元
        if isNonePackageReply:
            sendCTUnit = CTYBot_CTUnit_CommonData()
            retDataArray.append(sendCTUnit)
        sockManager.PassiveSend_To_AcceptSock(clientSock, retDataArray)
        if self.__report_status:
            if strPeerName in self.__node_status.SocksInfo['Socks'].keys():
                self.__node_status.SocksInfo['Socks'][strPeerName]['Status'] = "Up"
                self.__node_status.SocksInfo['Socks'][strPeerName]['TotalSend'] += len(ctUnitArray)
                self.__node_status.SocksInfo['Socks'][strPeerName]['LastSendTime'] = NodeStatus.get_now_timestamp()
                self.__node_status.SocksInfo['TotalSend'] += len(ctUnitArray)

    #Connect端数据包接收到后处理
    def __connect_to_basic_handle(self, sock_id, sock_port,eachCTUnit, is_last_package):
        if (eachCTUnit.s_iMyDataType == CTYLB_Bot_BaseDef.s_g_iDataType_CommonTask):
            if eachCTUnit.s_iValue in self.__connect_to_callbacks[sock_id][sock_port]['recv'].keys():
                eachRetCommCTUnitArray = self.__connect_to_callbacks[sock_id][sock_port]['recv'][eachCTUnit.s_iValue](
                    CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachCTUnit.s_strValue),
                    CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachCTUnit.s_strParam1),
                    CTYLB_MainSys_MiscFunc.SafeGetUnicode(eachCTUnit.s_strParam2),
                    is_last_package)
                return eachRetCommCTUnitArray

    #Connect数据包发送处理，所有的数据包最终都在这里进行处理并放入主循环中的发送队列
    def __connect_send_package_handle(self, sock_key,sock_port):
        retSendUnitArray=[]
        for key in self.__connect_to_callbacks[sock_key][sock_port]['send'].keys():
            actinveSendUnit=self.__connect_to_callbacks[sock_key][sock_port]['send'][key]("", "", "", True)
            if isinstance(actinveSendUnit,list):
                self.__connect_wait_to_send_arrays[sock_key][sock_port].extend(actinveSendUnit)
            else:
                self.__connect_wait_to_send_arrays[sock_key][sock_port].append(actinveSendUnit)

        if self.__connect_wait_to_send_arrays[sock_key][sock_port]:
            retSendUnitArray.extend(self.__connect_wait_to_send_arrays[sock_key][sock_port])
            self.__connect_wait_to_send_arrays[sock_key][sock_port] = []

        return retSendUnitArray

    def run(self):
        global IS_SYS_RUNNING
        IS_SYS_RUNNING=True
        # 获取配置文件路径及文件名，文件夹不存在则创建
        config_file = os.path.abspath(self.__config_file)
        if not os.path.isfile(config_file):
            CTYLB_Log.ShowLog(0, 'Main', '[%s] config file missing...Quit!' % self.__bot_name)
            # 配置文件不存在，直接退出
            os._exit(-1)

        db_dir = os.path.join(os.path.abspath("."), u"db")
        db_file = os.path.join(db_dir, "{0}.db".format(self.__bot_name))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        # 创建机器人框架
        botFrameThread = CLessTYBotFrameThread(config_file, db_file)
        # 设置默认对环境全局事件处理
        botFrameThread.SetDefaultConsoleCompatible(FBotV4.environment_event_handle)
        # 准备运行
        botFrameThread.Prepare_Start()

        # 获得通讯管套管理对象
        sockManager = botFrameThread.s_HLSockMang

        connectToSocks = {}
        # 获得通讯管套管理对象、操作结果以及操作参数块
        for key in self.__connect_to_socks.keys():
            connectToSocks[key]={}
            for port in self.__connect_to_socks[key]:
                # 若为状态汇报，则间隔时间由用户指定
                if key == TYFBOT_STATUS_MANAGER_IDENTIFY_NAME:
                    sock = CTYFBot_OpSession_ConnectSock(hlSockMang=sockManager, strDestSrvName=key,
                                                         iDestPort=port,
                                                         iDefaultIdleTick=self.__report_interval)
                else:
                    sock = CTYFBot_OpSession_ConnectSock(hlSockMang=sockManager, strDestSrvName=key,
                                                         iDestPort=port,
                                                         iDefaultIdleTick=1)
                connectToSocks[key][port]=sock

                CTYLB_Log.ShowLog(0, 'exec', 'Start HLSock connect remote [{0}:{1}]  --{2}'.format(
                    key, port, self.__bot_name))

        listenSocks = []
        acceptSocks = []
        for sockID in self.__listen_socks:
            listenSock = sockManager.CreateListenSock(sockID)
            listenSocks.append(listenSock)

        iFreeCount = 0
        while IS_SYS_RUNNING:
            isTaskBusy = False
            for key in connectToSocks.keys():
                for port in connectToSocks[key].keys():
                    sock=connectToSocks[key][port]
                    if (sock.ExecNextCheck()):
                        isTaskBusy = True

                    if (sock.CanExecSendData()):
                        for port in self.__connect_to_callbacks[key].keys():
                            execSendCTArray = self.__connect_send_package_handle(key,port)
                            sock.ExecSendData(execSendCTArray)
                        isTaskBusy = True
                        if self.__report_status:
                            if key in self.__node_status.SocksInfo['Socks'].keys():
                                self.__node_status.SocksInfo['Socks'][key]['Status'] = "Up"
                                self.__node_status.SocksInfo['Socks'][key]['TotalSend'] += len(execSendCTArray)
                                self.__node_status.SocksInfo['Socks'][key]['LastSendTime'] = NodeStatus.get_now_timestamp()
                                self.__node_status.SocksInfo['TotalSend'] += len(execSendCTArray)
                    recvCTArray = sock.PopRetriveRecvCTArray()

                    if( not recvCTArray):
                        bSockExist, recvCTArray = sockManager.PassiveRecv_From_ConnectSock( sock.s_iExecConnectSockIndex)
                        if (not bSockExist):
                            CTYLB_Log.ShowLog(0, 'exec', 'sock close by remote. restarting.')
                            sock.Close()

                    if (recvCTArray):
                        isTaskBusy = True
                        strPeerName, iPeerPort = sockManager.GetSockPeerAddr(
                            sock.s_iExecConnectSockIndex)
                        if isinstance(strPeerName, bytes):
                            strPeerName = strPeerName.decode()
                        isNonePackageReply = True
                        arrayLen = len(recvCTArray)
                        if self.__report_status:
                            if key in self.__node_status.SocksInfo['Socks'].keys():
                                self.__node_status.SocksInfo['Socks'][key]['Status'] = "Up"
                                self.__node_status.SocksInfo['Socks'][key]['TotalRecv'] += arrayLen
                                self.__node_status.SocksInfo['Socks'][key]['LastRecvTime'] = NodeStatus.get_now_timestamp()
                                self.__node_status.SocksInfo['TotalRecv'] += arrayLen
                        packageCount = 0
                        for eachUnit in recvCTArray:
                            packageCount += 1
                            eachRetCommCTUnitArray = self.__connect_to_basic_handle(key, port,eachUnit, packageCount == arrayLen)
                            if eachRetCommCTUnitArray:
                                isNonePackageReply = False
                                self.__connect_wait_to_send_arrays[key][port].extend(eachRetCommCTUnitArray)
                        if isNonePackageReply:
                            defaultPackage = CTYBot_CTUnit_CommonData()
                            self.__connect_wait_to_send_arrays[key][port].append(defaultPackage)
            # 若存在监听服务
            for listenSock in listenSocks:
                # 监听服务通信检查，检查新接受的连接
                newClientSockIndex = sockManager.ExAcceptNewListenArriveSock(listenSock)
                if newClientSockIndex:
                    strPeerName, iPeerPort = sockManager.GetSockPeerAddr(newClientSockIndex)
                    if isinstance(strPeerName, bytes):
                        strPeerName = strPeerName.decode()
                    if self.__listen_accept_callback:
                        self.__listen_accept_callback(listen_sock_id=listenSock,peer_name=strPeerName,
                                                      peer_port=iPeerPort,client_index=newClientSockIndex)
                    CTYLB_Log.ShowLog(0, u'New Client Accept', u'From [%s:%d] new HLConnect %d accept.' % (
                        strPeerName, iPeerPort, newClientSockIndex))
                    bTaskBusy = True
                    acceptSocks.append(newClientSockIndex)
                    if self.__report_status:
                        # 添加Listen端SockInfo
                        sockInfo = SockInfo(name=strPeerName, operateId=key, sockType='Listen')
                        self.__node_status.SocksInfo['Socks'][strPeerName] = sockInfo.dump_obj()
                        self.__node_status.SocksInfo['Socks'][strPeerName]['Status'] = "Up"
                    pass
                for iEachAcceptSock in acceptSocks:
                    # 检查有否新数据包到达
                    strPeerName, iPeerPort = sockManager.GetSockPeerAddr(iEachAcceptSock)
                    if isinstance(strPeerName, bytes):
                        strPeerName = strPeerName.decode()
                    bSockExist, ctUnitArray = sockManager.ActiveRecv_From_AcceptSock(iEachAcceptSock)
                    if (not bSockExist):
                        # 检查是否管套已经关闭
                        if self.__report_status:
                            if strPeerName in self.__node_status.SocksInfo['Socks'].keys():
                                self.__node_status.SocksInfo['Socks'][strPeerName]['Status'] = "Down"
                        CTYLB_Log.ShowLog(0, u'Accept Client Closed', u'Accept sock %d closed' % (iEachAcceptSock))
                        acceptSocks.remove(iEachAcceptSock)

                        break
                    else:
                        if (ctUnitArray):
                            bTaskBusy = True
                            self.__listen_basic_handle(sockManager, iEachAcceptSock, ctUnitArray)
                            if self.__report_status:
                                if strPeerName in self.__node_status.SocksInfo['Socks'].keys():
                                    self.__node_status.SocksInfo['Socks'][strPeerName]['Status'] = "Up"
                                    self.__node_status.SocksInfo['Socks'][strPeerName]['TotalRecv'] += len(ctUnitArray)
                                    self.__node_status.SocksInfo['Socks'][strPeerName][
                                        'LastRecvTime'] = NodeStatus.get_now_timestamp()
                                    self.__node_status.SocksInfo['TotalRecv'] += len(ctUnitArray)
            # 循环需要调用的回调处理，比如定时从数据库读取任务发送等
            for loop_event_callback in self.__loop_event_callbacks:
                loop_event_callback()

            if (not isTaskBusy):
                iFreeCount += 1
                if (iFreeCount > 50):
                    time.sleep(0.01)
            else:
                iFreeCount = 0

        for key in connectToSocks.keys():
            for port in connectToSocks[key]:
                connectToSocks[key][port].Close()
        connectToSocks = {}
        listenSocks = []

        botFrameThread.SafeStop()
        CTYLB_Log.ShowLog(0, "System Exited", "Bye Bye!")
