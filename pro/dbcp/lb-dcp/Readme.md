============================================================================
极限天元分布式智能计算框架V2.0 （Less Brain -Distributed Compute Platform）
============================================================================
[*] 项目列表说明：
	1.TYBotServerSDK2-Package-Solution :通信服务器端实现代码；
	2.TYBotSDK2-Package-Solution :通信客户端实现代码；
	3.TYBotSDK2-Main-Solution :插件端（PL）/任务注册中心（TRC）/插件任务分发及结果解析端（PLC）/服务器端（SER）实现代码；
	4.Monitor-Solution :任务状态监控界面后端RESTful API通信实现代码；
	5.Monitor-Go :任务状态监控界面Golang实现；


[*] Client共用部分构建说明
	步骤如下[在TYBotSDK2-Package-Solution目录下进行]：
	1.卸载之前安装的whl库：	pip uninstall TYBotSDK2      （选择y卸载全部）
	2.生成目标whl文件：		python setup.py bdist_wheel
	3.执行安装：			pip install ./dist/TYBotSDK2-2.0.1-py3-none-any.whl
	
	

[*] Server共用部分构建说明
	步骤如下[在TYBotServerSDK2-Package-Solution目录下进行]：
	1.卸载之前安装的whl库：	pip uninstall TYBotServerSDK2      （选择y卸载全部）
	2.生成目标whl文件：		python setup.py bdist_wheel
	3.执行安装：			pip install ./dist/TYBotServerSDK2-2.0.1-py3-none-any.whl
	

[*] Change Log (2017年4月1日):
	1.统一库名为：TYBotSDK2.P2PClient（通信客户端）、TYBotSDK2.BotBase（机器人基础库）、TYBotServerSDK2.P2PServer（通信服务端）；
	2.统一数据库存放目录文件为"db/datadb"，统一配置文件为"config/config.ini" ；
	3.新增配置或者数据库文件夹不存在，则自动生成；

[*] Change Log (2017年12月14日):
	1.将默认的配置文件由config/config.ini修改为config/config.yaml;
	2.默认配置文件模板为config_example.yaml ；
	3.FBot调用实例新增以类的方式调用的例子；

*** 安装sdK为当前源代码链接目录 python setup.py -e .


# 默认配置文件为当前目录下 config_example.yaml. 2017-12-15之后版本都需要使用新的配置文件。


# 增加virtual-env:
================
find / -name python3 2>/dev/null

sudo pip3 install virtualenv

virtualenv -p /usr/local/bin/python3 ss_proj  # 在当前目录下，创建一个ss_proj的虚拟环境，virtualenv会复制必须的文件
source ss_proj/bin/activate    # 激活ss_proj的虚拟环境

像以往一样,使用pip3和python3

deactivate # 使用完，退出

==================
180409
安装nats:
pip3 install asyncio-nats-client
