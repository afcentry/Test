#=-*-coding:utf-8 -*-
'''
利用Dig程序获取DNS的解析路径，类似于路由跟踪的tracert 命令。
'''
import subprocess
import shlex
import time
import chardet
import json
import datetime
from .utils import *

class DnsTracerManager:
    def __init__(self):
        pass
    def trace(self,domain):
        '''
        DNS Dig跟踪
        :param domain: 需要跟踪的目标域名
        :return: 跟踪结果Json字符串
        ==================================================================================================
        {
             "raw": "...",                                        #DNS Dig的原始结果
            "os": "Windows",                                      #执行Dig的系统类型Windows/Linux
            "target": "google.com",                               #执行目标域名
            "time": "2017-01-22 12:30:54.933000"                  #执行完成时间
        }
        ==================================================================================================
        '''
        domain=domain.strip().lower()
        cmd='dig %s +trace' %(domain)
        jsonData={}
        jsonData['target']=domain
        if isWindwosOS():
            jsonData['os']="Windows"
        else:
            jsonData['os']="Linux"
        try:
            proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
            out, err = proc.communicate()
            encoding = chardet.detect(out)['encoding'].lower()
            if encoding == 'gb2312':
                out = out.decode('gb2312').encode('utf-8')
            elif encoding == 'gbk':
                out = out.decode('gbk').encode('utf-8')
            strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            print("[%s] Task [%s] Finished ...OK" % (strTime,domain))
            jsonData['raw']=out

        except Exception as e:
            strTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
            print("[{0}] Task [{1}] Error:{2} ...Failed!".format(strTime,domain,e))
            jsonData['raw']=''
        jsonData['time'] = str(datetime.datetime.utcnow())
        jsonStr=json.dumps(jsonData,ensure_ascii=False,indent=4)
        # with open("%s.json"%(domain),'w') as f:
        #    f.write(jsonStr)
        return jsonStr

    def result_parse_json(self,resultJson):
        '''
        解析DNS Dig结果为Json字符串
        :param resultJson: 需要解析的DNS Dig结果
        :return: 解析后的结果Json字符串
        ==================================================================================================
        {
            "target": "google.com",                                    #执行目标域名
            "time": "2017-01-22 12:30:54.933000",                      #执行完成时间
            "dns_path": [                                              #Dns 解析路径集合
                {
                    "domain": "",                                      #当前解析的域，若为空，则表示为根
                    "dns_server": "i.root-servers.net",                #负责解析当前域的DNS服务器域名或者IP
                    "server_type": "NS",                               #解析服务器类型
                    "is_encrypt": false,                               #是否为加密结果
                    "dns_server_type": "Domain",                       #当前解析服务器类型，Domain-正常域名解析，Unknown-未知类型
                    "net_type": "IN",                                  #网络类型
                    "timeout": "473688"                                #解析结果超时时间或有效时间
                },
                {
                    "domain": "S84AE3BIT99DKIHQH27TRC0584HV5KOH.com",
                    "dns_server": "1 1 0 - S84C439C9HACCNUVH6CBPPTUS93VLTUG  NS DS RRSIG",
                    "server_type": "NSEC3",
                    "is_encrypt": true,
                    "dns_server_type": "Unknown",
                    "net_type": "IN",
                    "timeout": "86400"
                }
            ],
            "error": 0,                                                #任务执行错误码，0-正常，1-错误
            "os": "Windows",                                           #任务执行操作系统类型，Windows/Linux
            "error_msg": "OK"                                          #与错误码匹配的错误消息内容
        }
        ==================================================================================================
        '''
        resultJson=json.loads(resultJson)
        target=resultJson['target'].encode("utf-8")
        runOs=resultJson['os'].encode("utf-8")
        finishTime=resultJson['time'].encode("utf-8")
        resultText=resultJson['raw'].encode("utf-8")
        lines=resultText.split('\n')
        dataJson={}
        dataJson['target']=target
        dataJson['os']=runOs
        dataJson["time"]=finishTime
        dataJson["error"]=0
        dataJson["error_msg"]="OK"
        dataJson["dns_path"]=[]

        for line in lines:
            if line == '' or line.strip() == '' or line.startswith(';'):
                continue
            line=line.replace("\t\t\t","\t").replace("\t\t","\t").strip()
            datas=line.split("\t")
            dataLen=len(datas)
            if dataLen==5:
                isEncrypt=False
                nsDomainType="Domain"
                currentDomain=datas[0][0:-1]
                timeout=datas[1]
                type=datas[2]
                server=datas[3]
                nsDomain=datas[4]
                if " " in nsDomain:
                    nsDomainType="Unknown"
            elif dataLen==1:
                isEncrypt = True
                datas=datas[0].split(" ",4)
                nsDomainType = "Unknown"
                currentDomain = datas[0][0: -1]
                timeout = datas[1]
                type = datas[2]
                server = datas[3]
                nsDomain = datas[4]
            else:
                continue
            if nsDomain.endswith("."):
                nsDomain=nsDomain[0:-1]
            digRecord={}
            digRecord["is_encrypt"]=isEncrypt
            digRecord["domain"]=currentDomain
            digRecord["timeout"]=timeout
            digRecord["net_type"]=type
            digRecord["server_type"]=server
            digRecord["dns_server"]=nsDomain
            digRecord["dns_server_type"]=nsDomainType
            dataJson['dns_path'].append(digRecord)
        if len(dataJson["dns_path"])<1:
            dataJson["error"] = 2
            dataJson["error_msg"] = "Dns Dig Failed."
        return json.dumps(dataJson,ensure_ascii=False,indent=4)

if __name__=="__main__":
    #定义DNS跟踪对象
    dns=DnsTracerManager()
    #执行跟踪
    jsonData = dns.trace("baidu.com")
    #jsonData = open("baidu.com.json", 'r').read()
    #jsonData=dns.trace("hku.hk")
    #jsonData=open("hku.hk.json",'r').read()
    #jsonData = dns.trace("google.com")
    #解析跟踪结果
    # print dns.result_parse_json(jsonData)