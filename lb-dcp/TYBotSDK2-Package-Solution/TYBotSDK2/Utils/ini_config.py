#======================================================
#ini配置文件读取帮助方法实现
#
#Pxk    2017-06-29
#======================================================

from TYBotSDK2.P2PClient.Tylb_p2p_share import CTY_YamlFile

def get_config_value(config_file,key):
    '''
    从指定的ini文件中获取指定section和指定key的配置值
    :param config_file: 配置文件路径
    :param key: 值名称,yaml 点分格式
    :return: 配置值
    '''
    cfg = CTY_YamlFile(config_file)
    cfg.load_configs()
    value = cfg.get_config(key)
    return value