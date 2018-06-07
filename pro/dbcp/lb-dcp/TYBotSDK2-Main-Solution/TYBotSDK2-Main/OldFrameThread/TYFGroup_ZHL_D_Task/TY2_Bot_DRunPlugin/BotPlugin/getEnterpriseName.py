#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    全国企业名录爬虫，网址：http://shop.99114.com/
    功能：爬取特定网站的企业名录
    created time：2017-03-27
'''
import time
import requests
from bs4 import BeautifulSoup


class GetEnterprisesSpider(object):
    def __init__(self):
        self.url = 'http://shop.99114.com'
        self.alphabel_url = ''
        self.header = {'Host': 'shop.99114.com',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
        self.s_strResultArray = []  # 保存结果

        self.s_bStartGetSoup = False  # 开始未执行GetSoup
        self.s_soupSubItemArray = []   # 首页的各项内容
        self.s_zimuAlphaBetURLS = []   # 字母的链接
        self.s_bGetAlphaSouYeStart = False   # 字母的首页尚未开始?
        self.s_strCurZiMuURL = ''     # 当前处理的字母URL
        self.s_iCurAlphaPageNum = 0   # 当前字母的页数
        self.s_curAlphaSubPageArray = []   # 当前字母的每一页

    def AddResultContent(self, strResult):
        self.s_strResultArray.append(strResult)
        pass

    def ReadNextResult(self):
        pass

    def get_soup(self, url):
        try:
            response = requests.get(url, headers=self.header, timeout=5)
            data = response.content
            return BeautifulSoup(data, "html.parser")
        except Exception as e:
            pass

    def fromSecondPage2EndPage_step_exec(self):
        if( len(self.s_curAlphaSubPageArray) > 0):
            curPage = self.s_curAlphaSubPageArray.pop(0)
            try:
                soup = self.get_soup('%s%d' % (self.alphabel_url, curPage))
                # print '%s%d' % (self.alphabel_url, page)
                for item in soup.find_all("strong"):
                    # 结果输出
                    # print item.text, self.all_count
                    # 入库
                    try:
                        self.AddResultContent(item.text)
                        # insertIntoEnterprise(item.text)
                        pass
                    except Exception as e:
                        pass
                # 暂停1秒
                time.sleep(1)
            except Exception as e:
                pass

    def parser_alphabel_url_step_exec(self):
        if( not self.s_bGetAlphaSouYeStart):
            self.s_bGetAlphaSouYeStart = True
            # 截取url中特定长度的字符串
            self.alphabel_url = self.s_strCurZiMuURL[0:-1]
            soup = self.get_soup(self.s_strCurZiMuURL)
            # 首先，从首页给的HTML标签字符串中获取总页数
            array_page_num = []
            for item in soup.find_all("a"):
                if "/list/pinyin/" in item["href"]:
                    array_page_num.append(item.text)
            # 获取该字母开头企业的总页数
            self.s_iCurAlphaPageNum = int(array_page_num[-2])

            # 获取该字母，首页里的所有企业名称
            for item in soup.find_all("strong"):
                try:
                    self.AddResultContent(item.text)
                    # 结果输出
                    # print item.text, self.all_count
                    # 入库
                    # insertIntoEnterprise(item.text)
                    pass
                except Exception as e:
                    pass
            self.s_curAlphaSubPageArray = []
            for page in xrange(2, self.s_iCurAlphaPageNum + 1):
                self.s_curAlphaSubPageArray.append(page)
        # 获取该字母，第2至第page_num页里的所有企业名称
        self.fromSecondPage2EndPage_step_exec()

    def start_step_exec(self):
        strResult = ''
        if( not self.s_bStartGetSoup ):
            self.s_bStartGetSoup = True
            soup = self.get_soup(self.url)

            self.s_soupSubItemArray = soup.find_all("a", attrs={"target": "_blank"})
            pass

        if( len(self.s_strResultArray) > 0):
            strResult = self.s_strResultArray.pop(0)
        else:
            # 首页的单元项还存在？
            if( len(self.s_soupSubItemArray) > 0):
                eachSoupSubItem = self.s_soupSubItemArray.pop(0)
                if("http://shop.99114.com/list/pinyin" in eachSoupSubItem['href']):
                    # 把字母的链接加入
                    self.s_zimuAlphaBetURLS.append(eachSoupSubItem["href"])
            # 如果当前字母的页处理完成，就取下一个字母的页内容。
            if (len(self.s_curAlphaSubPageArray) == 0):
                if( len(self.s_zimuAlphaBetURLS) > 0):
                    self.s_bGetAlphaSouYeStart = False
                    self.s_strCurZiMuURL = self.s_zimuAlphaBetURLS.pop(0)
            self.parser_alphabel_url_step_exec()

            if (len(self.s_strResultArray) > 0):
                strResult = self.s_strResultArray.pop(0)

        return strResult

# 全局变量
g_GetEnterpriseSpider = None
# UnitTest
def GetEnterPriseNameStepResult( strInputParam):
    global g_GetEnterpriseSpider
    if( not g_GetEnterpriseSpider):
        g_GetEnterpriseSpider = GetEnterprisesSpider()
    strRetResult = g_GetEnterpriseSpider.start_step_exec()
    return strRetResult
