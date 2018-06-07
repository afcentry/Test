#coding:utf-8

def getgenerate():
    for i in range(6):
        yield i

xx = getgenerate()
while 1:
    print(next(xx))