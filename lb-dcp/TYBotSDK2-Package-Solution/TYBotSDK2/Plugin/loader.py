# ======================================================
# 动态插件自动化加载模块。
# 实现自动化从指定的文件中及动态加载Python模块,并实例化调用。
#
# Pxk    2017-09-07
# ======================================================

import traceback
import types
import os

class BaseLoader:
    '''
    动态Py文件函数模块加载器实现类
    '''
    def __init__(self):
        pass

    def load(self,path):
        '''
        加载指定py文件中的所有模块内容,包括类,字段,函数等
        :param path: py文件路径
        :return: 包含所有模块内容的Python module对象
        '''
        name=os.path.split(os.path.abspath(path))[1]
        if name.lower().endswith(".py"):
            name=name[:-3]
        try:
            with open(path,'r') as f:
                code=f.read()
                context=types.ModuleType(name)
                exec (code, context.__dict__)
                return context
        except:
            print("Load module [{0}] error:{1}".format(path,traceback.format_exc()))
        return None

class BrainPluginLoader(BaseLoader):
    '''
    极限大脑插件批量加载器，用于加载实现了 int GetFuncID() 和 ExecFunc(param1, param2, param3, param4)方法接口的插件类对象,
    并将插件功能与插件ID一一映射为可通过字典方式调用的方法执行器。
    '''
    def __init__(self):
        super().__init__()
        self.__funcs={} #ID-函数功能对字典

    def get_all_plugin_files(self,path,ext=".py"):
        '''
        获取指定目录下所有插件文件.
        :param path: 需要加载的插件的目录或插件文件
        :param ext: 插件文件后缀名,默认为.py
        :return:所有的插件文件列表List
        '''
        all_files=[]
        path=os.path.abspath(path)
        if os.path.isfile(path):
           all_files.append(path)
        else:
            for root,dirs,files in os.walk(path):
                for file in files:
                    if not file.lower().endswith(ext):
                        continue
                    filePath=os.path.join(root,file)
                    all_files.append(filePath)
        return all_files

    def reload(self,path="./plugins"):
        '''
        重新加载指定文件或文件夹下所有插件文件，并重新加载ID-功能函数映射字典
        :param path: 需要加载插件的文件或目录，默认为“./plugins”
        :return: ID-功能函数一一映射的字典对象
        '''
        self.__funcs={}
        print("[*]Reloading plugins...")
        allfiles=self.get_all_plugin_files(path)
        for fileName in allfiles:
            context=self.load(fileName)
            if( context):
                for name in dir(context):
                    obj=getattr(context,name)
                    try:
                        obj=obj()
                        id=obj.GetFuncID()
                        func=obj.ExecFunc
                        self.__funcs[id]=func
                        # print("[*]Plugin loaded:[Class={0},ID={1},file={2}]".format(type(obj),id,fileName))
                    except:
                        pass
        return self.__funcs

    def get_func_by_id(self,func_id):
        '''
        获取指定插件ID的功能函数对象
        :param func_id: 插件ID
        :return: 若存在则返回对应插件ID的功能函数对象,否则返回None
        '''
        if id in self.__funcs:
            return self.__funcs[id]
        else:
            return None
