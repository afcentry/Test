#coding:utf-8

import threadpool,time
import queue
q = queue.Queue()

def printsome(x):
    se = "hello," + x
    print("hello,{}".format(x))
    time.sleep(2)
    q.put((x,se))

result = list()
namelist = ['tom',"kobe","curry","james","harden","zhangsan"]
pool = threadpool.ThreadPool(8)
requests = threadpool.makeRequests(printsome,namelist)
[pool.putRequest(req) for req in requests]
pool.wait()
while not q.empty():
    result.append(q.get())
print(result)