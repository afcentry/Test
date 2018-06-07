#==============================================================
#Web API 屏幕切换展示控制任务帮助类
#封装屏幕控制WEB API实现
#
#Pxk   2017-05-06
#==============================================================

'''
{
  "table_name": "ow_kshow_command",
  "insert_data": {
    "type": 3,
    "status": 0,
    "command": "Data:index:深圳市"
  }
}



{
  "table_name": "ow_kshow_command",
  "insert_data": {
    "type": 2,
    "status": 0,
    "command": "EarlyWarning:asset:EarlyWarning:index"
  }
}


table_name  表名
type    
    2为页面切换
    3为内部数据切换
command
    type为3是command对应的格式为    Data:index:深圳市
                                    (数据:首页:深圳市)
                                    
    type为2是command对应的格式为    EarlyWarning:asset:EarlyWarning:index
                                    (态势模块:资产页面:态势模块:首页)
'''

import requests
import json
import time

DEBUG_BASE_URL="http://192.168.4.240/DisplayPage/api/add"

class MonitorApiHandler:

    @staticmethod
    def AddNetworkSituation(target,target_type,baseUrl=DEBUG_BASE_URL):
        '''
        添加网络安全态势屏幕展示任务
        :param target: 需要展示的目标名称，如：广州市，金融行业，南方电网
        :param target_type: 需要展示目标类型。分为：area-地区，industry-行业，enterprise-企业
        :param baseUrl: WEB API请求打URL地址
        :return: 执行结果状态返回
        '''

        payload={}
        payload['table_name']='ow_kshow_command'
        payload['insert_data']={}
        payload['insert_data']['type']=2
        payload['insert_data']['status']=0
        payload['insert_data']['command']="Data:index:{0}:{1}".format(target_type,target)

        retryCount = 10  # 若发送异常，尝试10次
        while retryCount > 0:
            try:
                jsonData = json.dumps(payload)
                response = requests.post(baseUrl, data=jsonData)
                #return response.text
                return "屏幕联动成功！"
                break
            except Exception as e:
                print("[*]提交屏幕展示任务失败：{}".format(e))
                retryCount = retryCount - 1
                print("[*]3秒后进行第{0}次尝试...".format(10 - retryCount))
                time.sleep(3)
        return "屏幕机器人似乎不在。。。尴尬～"


    @staticmethod
    def AddNetworkAssets(target, target_type, baseUrl=DEBUG_BASE_URL):
        '''
        添加网络安全态势屏幕展示任务
        :param target: 需要展示的目标名称，如：广州市，金融行业，南方电网
        :param target_type: 需要展示目标类型。分为：area-地区，industry-行业，enterprise-企业
        :param baseUrl: WEB API请求打URL地址
        :return: 执行结果状态返回
        '''

        payload = {}
        payload['table_name'] = 'ow_kshow_command'
        payload['insert_data'] = {}
        payload['insert_data']['type'] = 2
        payload['insert_data']['status'] = 0
        payload['insert_data']['command'] = "Data:asset:{0}:{1}".format(target_type,target)

        retryCount=10 #若发送异常，尝试10次
        while retryCount>0:
            try:
                jsonData=json.dumps(payload)
                response=requests.post(baseUrl,data=jsonData)
                return response.text
                break
            except Exception as e:
                print("[*]提交屏幕展示任务失败：{}".format(e))
                retryCount=retryCount-1
                print("[*]3秒后进行第{0}次尝试...".format(10-retryCount))
                time.sleep(3)
        return "屏幕机器人似乎不在。。。尴尬～"