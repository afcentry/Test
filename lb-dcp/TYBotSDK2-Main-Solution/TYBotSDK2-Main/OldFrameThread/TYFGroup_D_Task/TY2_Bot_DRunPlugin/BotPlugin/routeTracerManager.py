#=-*-coding:utf-8 -*-
'''
利用tracert程序获取域名或者IP的路由跟踪信息-管理端
'''

import json
from .utils import *
import time
import datetime
import subprocess
import chardet
import shlex

class RouteTracerManager:
    '''
    路由跟踪实现类，目前仅支持Windows
    任务执行管理端，主要负责结果的解析
    '''
    def __init__(self):
        pass

    def _result_parse_json_Windows(self, resultText):
        '''
        解析Windows版本Tracert结果
        :param resultText: Windows版本的Tracert结果，为Json字符串，如下：
         ----------------------
            {
                "target":"baidu.com",                #需要路由跟踪的IP或者域名目标
                "raw":"[...]",                       #路由跟踪的原始结果
                "state":"",                          #需要传递的额外内容，用户指定
                "max_hops":30,                       #路由跟踪最大跳数（TTL）值
                "timeout":1,                         #路由跟踪超时时间，单位为秒
                "time":"2017-01-12 02:15:37.166689", #路由跟踪完成时间（UTC）
                "os":"Linux",                        #执行路由跟踪命令的操作系统类型(Windows/Linux)
                "uid":-1,                            #被路由跟踪的IP或者域名的唯一标记，用户指定
                "task_id":-1                         #任务ID
            }
       ----------------------
        :return: 解析后的结果的Json字符串，如下：
        ---------------------
        {
            "domain": "",                            #路由跟踪的目标的域名
            "task_id":-1                             #任务ID
            "uid": -1,                               #被路由跟踪的IP或者域名的唯一标记，用户指定
            "trace": [                               #路由跟踪结果集合
                {
                    "index": 1,                      #路由跟踪跳数
                    "ip": "192.168.1.254",           #当前跳的IP
                    "time1": 140,                    #第1个数据包返回时间ms
                    "time2": 123,                    #第2个数据包返回时间ms
                    "time3": 115,                    #第3个数据包返回时间ms
                    "host": "",                      #当前跳的IP对应的域名
                    "timeout": false,                #是否超时，超时：true，未超时：false
                    "average_time":126,              #平均时延ms
                },
                {
                    ...
                }
            ],
            "ttl": 30,                               #路由跟踪实际跳数（TTL）值
            "ip": "154.63.25.8",                     #路由跟踪的目标的IP
            "error": 0,                              #路由跟踪结果状态码,0-成功  非零-失败（1-目标域名无法解析 2-解析结果失败 1231-传输错误）
            "state": "",                             #需要传递的额外内容，用户指定
            "timeout": 1,                            #路由跟踪超时时间，单位为秒
            "time": "2017-01-12 06:46:04.519000",    #路由跟踪完成时间（UTC）
            "max_ttl": 30,                           #路由跟踪最大跳数（TTL）值
            "os": "Windows",                         #执行路由跟踪命令的操作系统类型(Windows/Linux)
            "error_msg": "OK",                       #路由跟踪结果状态码附加说明信息
            "target": "154.63.25.8",                 #需要路由跟踪的IP或者域名目标
            "is_reached":true                        #是否到达目标IP,是-true,否-false
        }
        ---------------------
        '''
        resultJson = json.loads(resultText, encoding='utf-8')
        taskId = resultJson['task_id']
        target = resultJson['target'].encode('utf-8')
        raw = resultJson['raw'].encode('utf-8')
        state = resultJson['state'].encode('utf-8')
        max_hops = resultJson['max_hops']
        timeout = resultJson['timeout']
        record_time = resultJson['time'].encode('utf-8')
        os_type = resultJson['os'].encode('utf-8')
        uid = resultJson['uid']
        lines = raw.split('\n')
        root = {}
        root['error'] = 0
        root['error_msg'] = 'OK'
        root['os'] = os_type
        root['time'] = record_time
        root['task_id'] = taskId
        root['uid'] = uid
        root['state'] = state
        root['target'] = target
        root['timeout'] = timeout

        result = []
        maxTTL = max_hops
        TTL = 0
        targetIP = ''
        targetDomain = ''
        isReachDestination=False
        root['is_reached'] =isReachDestination
        try:
            for line in lines:
                line = line.lower()
                if line == '' or line.strip() == '':
                    continue
                line = line.strip()
                '''
                ############################################################
                Unable to resolve target system name fdsfdsfd.cnn.ccc.
                ############################################################
                无法解析目标系统名称 fsfdsfds.ccn.ccn。
                ############################################################
                '''
                if "无法解析目标系统名称".lower() in line or "Unable to resolve target system name".lower() in line:
                    root['error'] = 1
                    root['error_msg'] = 'Unable to resolve target system name %s' % (target)
                    return json.dumps(root, indent=4)
                if 'Transmit error'.lower() in line:
                    root['error'] = 1231
                    root['error_msg'] = 'Transmit error: code 1231'
                    return json.dumps(root, indent=4)
                if 'ms' not in line and '*' not in line:
                    '''
                    ############################################################
                    Tracing route to 123.125.114.144 over a maximum of 30 hops

                    1     7 ms    17 ms    14 ms  192.168.79.1
                    2     *        *        *     Request timed out.
                    3    78 ms    64 ms    37 ms  120.80.62.53
                    4    91 ms    48 ms    66 ms  120.80.62.102
                    ############################################################
                    通过最多 30 个跃点跟踪到 23.91.97.24 的路由

                    1     *       93 ms   102 ms  bogon [192.168.1.1]
                    2    96 ms   101 ms   112 ms  2-171-100-101.myrepublic.com.sg [101.100.171.2]
                    3   100 ms    88 ms    89 ms  103-6-148-49.myrepublic.com.sg [103.6.148.49]
                    ############################################################
                    Tracing route to sina.com [66.102.251.33]
                    over a maximum of 30 hops:

                      1     5 ms    16 ms    11 ms  192.168.79.1
                      2     *        *        *     Request timed out.
                      3    56 ms    44 ms    81 ms  120.80.62.49
                      4    51 ms    29 ms    47 ms  120.80.62.94
                      5    68 ms    44 ms    40 ms  120.80.62.89
                      6    47 ms     *        *     120.80.62.105
                    ############################################################
                    通过最多 30 个跃点跟踪
                    到 baidu.com [111.13.101.208] 的路由:

                      1   107 ms    92 ms   121 ms  bogon [192.168.1.1]
                      2    98 ms   109 ms   110 ms  2-171-100-101.myrepublic.com.sg [101.100.171.2]
                      3   115 ms   101 ms   107 ms  103-6-148-49.myrepublic.com.sg [103.6.148.49]
                      4   123 ms   120 ms   121 ms  snge-b1-link.telia.net [213.248.72.21]
                      5   342 ms   278 ms   317 ms  las-b21-link.telia.net [62.115.134.43]
                      6   293 ms   290 ms   286 ms  chinamobile-ic-319993-las-b21.c.telia.net [213.248.92.171]
                    ############################################################
                    '''

                    if line.startswith('Tracing route to'.lower()) and line.endswith('hops'.lower()):
                        line = line.replace('Tracing route to'.lower(), '').replace('over a maximum of'.lower(), '') \
                            .replace('hops'.lower(), '').strip()
                        datas = split_and_remove_empty(line, sep=' ')
                        targetIP = datas[0]
                        maxTTL = int(datas[1])
                    elif line.startswith('通过最多'.lower()) and line.endswith('的路由'.lower()):
                        line = line.replace('通过最多'.lower(), '').replace('个跃点跟踪到'.lower(), '').replace('的路由'.lower(),
                                                                                                      '').strip()
                        datas = split_and_remove_empty(line, sep=' ')
                        targetIP = datas[1]
                        maxTTL = int(datas[0])
                    elif line.startswith('Tracing route to'.lower()) and line.endswith(']'.lower()):
                        line = line.replace('Tracing route to'.lower(), '').replace('['.lower(), '') \
                            .replace(']'.lower(), '').strip()
                        datas = split_and_remove_empty(line, sep=' ')
                        targetDomain = datas[0]
                        targetIP = datas[1]
                    elif line.startswith('通过最多'.lower()) and line.endswith('个跃点跟踪'.lower()):
                        line = line.replace('通过最多'.lower(), '').replace('个跃点跟踪'.lower(), '').strip()
                        datas = split_and_remove_empty(line, sep=' ')
                        maxTTL = int(datas[0])
                    elif line.startswith('over a maximum of'.lower()) and line.endswith('hops:'.lower()):
                        line = line.replace('over a maximum of'.lower(), '').replace('hops:'.lower(), '').strip()
                        datas = split_and_remove_empty(line, sep=' ')
                        maxTTL = int(datas[0])
                    elif line.startswith('到'.lower()) and line.endswith('的路由:'.lower()):
                        line = line.replace('到'.lower(), '').replace('['.lower(), '') \
                            .replace(']'.lower(), '').replace('的路由:'.lower(), '').strip()
                        datas = split_and_remove_empty(line, sep=' ')
                        targetDomain = datas[0]
                        targetIP = datas[1]
                    continue

                temp = line.split(' ')
                datas = []
                for t in temp:
                    if t == '' or t.strip() == '' or t.strip() == 'ms':
                        continue
                    t = t.strip()
                    if t == "*":
                        t = '0'
                    datas.append(t)
                totalLen = len(datas)
                index = int(datas[0])
                time1 = int(datas[1])
                time2 = int(datas[2])
                time3 = int(datas[3])
                if totalLen == 6:
                    host = datas[4]
                    ip = datas[5]
                else:
                    if "请求超时".lower() in line or "timed out".lower() in line:
                        host = ''
                        ip = ''
                    else:
                        host = ''
                        ip = datas[4]
                ip=ip.replace('[', '').replace(']', '')
                #到达目的跳，不记录
                if ip==targetIP:
                    #到达最后一跳
                    isReachDestination=True
                    continue
                ret = {}
                ret['index'] = index
                ret['time1'] = time1
                ret['time2'] = time2
                ret['time3'] = time3
                ret['average_time']=(time1+time2+time3)/3
                ret['host'] = host
                ret['ip'] = ip
                # 是否超时
                ret['timeout'] = (time1 == time2 == time3 == 0)
                result.append(ret)
                TTL = index  # 记录实际的TTL
        except Exception as e:
            root['error'] = 2
            root['error_msg'] = 'Parse tracert result error:{}'.format(e)
            return json.dumps(root, indent=4)
        root['trace'] = result
        root['ip'] = targetIP
        root['domain'] = targetDomain
        root['max_ttl'] = maxTTL
        root['ttl'] = TTL
        root['is_reached'] =isReachDestination
        return json.dumps(root, indent=4)

    def _result_parse_json_Linux(self, resultText):
        # TODO: Unix和Linux系统由于存在解析结果错误，暂未实现功能
        pass

    def result_parse_json(self, resultText):
        '''
        将Tracert原始结果解析成json格式
        :param resultText: 需要解析的结果
        :return: 解析后的json格式结果
        '''
        return self._result_parse_json_Windows(resultText)
        '''
        if isWindwosOS():
            return self._result_parse_json_Windows(resultText)
        else:
            raise 'Not Supported Unix or Linux.'
            return self._result_parse_json_Linux(resultText)
        '''
			
    def trace(self, domain, taskId=-1, uid=-1, state='', maxHops=30, timeout=1):
        '''#######################################################################
        路由跟踪操作，兼容Windows "tracert"命令和Unix/Linux 下的"traceroute"命令。
        :param domain:需要进行路由跟踪的IP或者域名
        :param taskId:任务ID
        :param uid:[可选]被路由跟踪的IP或者域名的唯一标记，用户指定
        :param state:[可选]需要传递的额外内容，用户指定
        :param maxHops:[可选]路由跟踪最大跳数
        :param timeout:[可选]路由跟踪超时时间，单位为秒
        :return:如下格式的Json字符串：
        --------
             {
                "target":"baidu.com",                #需要路由跟踪的IP或者域名目标
                "raw":"[...]",                       #路由跟踪的原始结果
                "state":"",                          #需要传递的额外内容，用户指定
                "max_hops":30,                       #路由跟踪最大跳数
                "timeout":1,                         #路由跟踪超时时间，单位为秒
                "time":"2017-01-12 02:15:37.166689", #路由跟踪完成时间（UTC）
                "os":"Linux",                        #执行路由跟踪命令的操作系统类型(Windows/Linux)
                "uid":-1,                            #被路由跟踪的IP或者域名的唯一标记，用户指定
                "task_id":-1                         #任务ID
             }
        --------
        ##########################################################################'''

        domain = domain.strip()
        result = {}
        result['target'] = domain
        result['task_id'] = taskId
        result['uid'] = uid
        result['state'] = state
        result['max_hops'] = maxHops
        result['timeout'] = timeout
        if isWindwosOS():
            cmd = 'tracert -h %d -w %d %s ' % (maxHops, timeout * 1000, domain)
            result['os'] = 'Windows'
        else:
            cmd = 'traceroute -m %d -w %d %s ' % (maxHops, timeout, domain)
            result['os'] = 'Linux'
            # raise 'Not Supported Unix or Linux.'
        try:
            proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = proc.communicate()
            encoding = chardet.detect(out)['encoding'].lower()
            if encoding == 'gb2312':
                out = out.decode('gb2312').encode('utf-8')
            elif encoding == 'gbk':
                out = out.decode('gbk').encode('utf-8')
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            print("[%s] Task [%s] Finished ...OK" % (strTime, domain))
            result['raw'] = out

        except Exception as e:
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            print("[{0}] Task [{1}] Error:{2} ...Failed!".format(strTime, domain, e))
            result['raw'] = ''
        result['time'] = str(datetime.datetime.utcnow())
        jsonResult = json.dumps(result, ensure_ascii=False)
        # with open('%s.json' % (domain), 'w') as f:
        #    f.write(jsonResult)
        return jsonResult
