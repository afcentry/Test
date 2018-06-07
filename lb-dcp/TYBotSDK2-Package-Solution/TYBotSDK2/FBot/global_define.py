#======================================================
#功能机器人实现模块全局变量定义模块
#定义所有用到的全局变量，进行统一的引用操作。
#
#Pxk    2017-05-15
#======================================================

#进程是否运行标志
IS_SYS_RUNNING=True

#状态展示功能机器人名称
TYFBOT_STATUS_MANAGER_IDENTIFY_NAME="TYFBOT_STATUS_MANAGER"
TYFBOT_STATUS_MANAGER_API_URL="[Set your api url in config file.]"
#智能大脑调度事件定义
# 下面定义本机器人的任务执行管套
LISTEN_SOCK_FBOT_ACTION_BRAIN_OPERATE=9                # 监听管套，操作行动机器人的任务
#指令宏定义
OP_ACTION_BRAIN_SUB_CMD_REQUEST_EXEC=901               # 申请可以执行的子任务
OP_ACTION_BRAIN_SUB_CMD_REPLY_REQUEST_EXEC=902         # 回复 申请子任务
OP_ACTION_BRAIN_SUB_CMD_REPLY_EXEC_RESULT=903          # 执行子任务后，返回执行结果
OP_ACTION_BRAIN_SUB_CMD_REPLY_REPLY_EXEC_RESULT=904    # 回复 返回执行结果

#微信操作相关定义
LISTEN_SOCK_FBOT_ACTION_WEIXIN_OPERATE=7               # 监听管套，操作微信机器人
OP_ACTION_WX_SUB_CMD_GET_LOGIN_CODE=701                # 获得登录二维码图片
OP_ACTION_WX_SUB_CMD_REPLY_GET_LOGIN_CODE=702          # 回复 获得登录二维码图片
OP_ACTION_WX_SUB_CMD_GET_CHAT_CONTENT=703              # 获得聊天的内容
OP_ACTION_WX_SUB_CMD_REPLY_GET_CHAT_CONTENT=704        # 回复 获得聊天的内容
OP_ACTION_WX_SUB_CMD_SEND_CHAT_CONTENT=705             # 发送要和别人说的内容
OP_ACTION_WX_SUB_CMD_REPLY_SEND_CHAT_CONTENT = 706     # 回复 发送要和别人说的内容
