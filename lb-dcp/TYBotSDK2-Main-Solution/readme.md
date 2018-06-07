Monitor监测类型枚举
PLC		- Plugin Console
TRC		- Task Register Center

PLC:
status	- 状态汇报类消息
		msgObject={"monitor_type":"status","level":"info","msg":"PLC starting..."}
		CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={"monitor_type":"status","level":"info","msg":"PLC loading config..."}
		CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={"monitor_type":"status","level":"error","msg":"Ctrl+C keyboard detected, PLC exiting..."}
		CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={"monitor_type":"status","level":"error","msg":"Config file not found, PLC exiting..."}
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={"monitor_type":"status","level":"error","msg":"PLC exited."}
		CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)


		msgObject={"monitor_type":"result","level":"info","plugin-id":self.s_iRunPluginID,"target":strOrigDomain,"msg":strResult}
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={
                    "monitor_type":"send-task-block",
                    "level":"info",
                    "block-size":len(strParamDataArray),
                    "block-id":assignWebNameBlock.s_strUniqueSign,
                    "plugin-id":assignWebNameBlock.s_iRunPluginID,
                    "msg":""}
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={
                    "monitor_type":"recv-task-block-free",
                    "level":"info",
                    "free-size":iRemoteTaskCenterFreeCount,
                    "plugin-id":iPluginID,
                    "msg":""}
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

		msgObject={
                    "monitor_type":"block-finish-reply",
                    "level":"info",
                    "block-id":strOrigParamBlockSign,
                    "result-code":iResultCode,
                    "wait-size":len( self.s_strPromptWaitFinishParamSignArray),
                    "plugin-id":self.s_iRunPluginID,
                    "msg":""}
        CTYLB_Log.ShowMonitor(msgType="PLC",msgObject=msgObject)

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
                "msg":""
