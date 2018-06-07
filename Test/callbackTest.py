# coding=utf-8


def clean1(times):
    """
    就假装是扫地吧，这种函数命名方式，千万别学习
    :param times: 次数
    :return: None
    """
    print('已完成扫地次数:', str(times))


def clean2(times):
    """
    默默的装作洗抽油烟机
    :param times: 次数
    :return: None
    """
    print('已洗抽油烟机次数', str(times))


def call_clean(times, function_name):
    """
    这个很重要，这个就是家政公司的业务系统，要啥业务都得在这说
    这个是实现回调函数的核心
    :param times:次数
    :param function_name:回调函数名
    :return:调用的函数结果
    """
    return function_name(times)

if __name__ == '__main__':
    call_clean(100, clean2)  # 给我洗100次抽油烟机，好吧，很变态