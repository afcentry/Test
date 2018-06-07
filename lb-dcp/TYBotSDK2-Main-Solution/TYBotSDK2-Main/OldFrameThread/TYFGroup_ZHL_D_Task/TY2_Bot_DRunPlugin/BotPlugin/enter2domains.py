#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    ICP备案域名爬虫，网址：http://www.beianbeian.com/
    功能：输入企业/单位名称，输出域名集合
    创建时间: 2017-03-24
'''
import requests
from bs4 import BeautifulSoup


class Enterprise2Domain(object):
    def __init__(self, name):
        self.domains = []
        self.enter_name = name
        self.main_url = 'http://www.beianbeian.com'
        self.url2 = 'http://www.beianbeian.com/s?keytype=2&q=%s'
        self.url3 = 'http://www.beianbeian.com/s?keytype=3&q=%s'
        self.header = {'Host': 'www.beianbeian.com',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

    def start(self):
        urls = []
        urls.append(self.url2)
        urls.append(self.url3)
        for url in urls:
            self.parser(url)
        return '%s|*|%s' % (self.enter_name, '|'.join(self.domains))

    def parser(self, url):
        response = requests.get(url % self.enter_name, headers=self.header)
        data = response.content
        soup = BeautifulSoup(data, "html.parser")
        for item in soup.find_all('a', attrs={'target': '_blank'}, href=True):
            if item.text.encode('utf-8') == '详细信息':
                detail_url = item['href']
                self.detail_parser(detail_url)

    def detail_parser(self, url):
        response = requests.get(self.main_url + url, headers=self.header)
        data = response.content
        soup = BeautifulSoup(data, 'html.parser')
        for item in soup.find_all('a', attrs={'target': '_blank'}):
            if '/go/?domain=' in item['href']:
                a_url = item.text.encode('utf-8').replace('izhuye.', '')
                if a_url not in self.domains and a_url is not '':
                    self.domains.append(a_url)

# UnitTest
def GetEnterPriseName_To_DomainName( strEnterPriseName):
    '''
        API Usage:
        1. from enter2domains import *
        2. main = Enterprise2Domain(name='***企业/单位名称')
        3. main.start()
        4. print main.domains
    '''
    # 湖南军煌教育发展有限公司
    # 深圳市腾讯计算机系统有限公司
    main = Enterprise2Domain(name=strEnterPriseName)
    # 结果输出
    strResult = main.start()
    return strResult