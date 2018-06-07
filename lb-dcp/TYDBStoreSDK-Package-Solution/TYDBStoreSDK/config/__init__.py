import yaml
class YamlConfigParser:
    '''
    Yaml配置文件读取类，读取方式为点分式读取
    '''
    def __init__(self, filename):
        self.filename = filename
        self.config=None

    def load_configs(self,config_file=None):
        '''
        从指定配置文件中读取配置，若不指定，则默认从对象初始化配置文件路径中读取。
        :param config_file: 配置文件路径
        :return: 无
        '''
        if config_file:
            self.filename=config_file
        with open(self.filename,'r') as f:
            self.config=yaml.load(f)

    def get_config(self, key, default =None):
        '''
        读取指定配置键下的内容，配置键支持点分式结构，如：database.mysql.host,表示读取database下，mysql配置下，host参数值
        :param key: 配置信息对应的键值
        :param default: 配置默认值，若配置不存在，则返回该默认值
        :return: 对应配置信息
        '''
        if not self.config:
            self.load_configs()
        try:
            keys=key.split('.')
            temp=self.config
            for i in range(len(keys)):
                temp=temp[keys[i]]
            value = temp
        except:
            value = default
        return value