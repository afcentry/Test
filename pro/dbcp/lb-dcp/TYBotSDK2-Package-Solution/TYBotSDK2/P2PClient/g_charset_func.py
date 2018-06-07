# -*- coding:UTF-8 -*- 放到第一行标记
#代码编码格式功能
#
# start by sk. 160607


import chardet  #编码功能

#操作类
class g_C_SkCharset:
    def __init__(self):
        pass
    
    @staticmethod
    def IsTextUnicode(strText):
        bRetValue = False
        if( type(strText) == str):  # 默认是unicode
            bRetValue = True
        return bRetValue
    
    @staticmethod
    def IsTextUTF8(strText):
        if( g_C_SkCharset.IsTextUnicode(strText)):
            return False
        #判断字符串是否utf8
        bRetValue=False
        strCharSet = chardet.detect(strText)['encoding']
        if( strCharSet == 'utf-8'):
            bRetValue = True
        return bRetValue
    
    @staticmethod
    def IsTextGB2312(strText):
        if( g_C_SkCharset.IsTextUnicode(strText)):
            return False
        #判断字符串是否gb2312
        bRetValue=False
        strCharSet = chardet.detect(strText)['encoding']
        if( strCharSet == 'GB2312'):
            bRetValue = True
        return bRetValue
    
    @staticmethod
    def ChangeTextToUTF8(strInText):
        #将文字改成UTF8格式
        strRetText = strInText
        #是否是unicode?
        if( g_C_SkCharset.IsTextUnicode( strInText) != True):
            #是否已经 utf-8?
            if( g_C_SkCharset.IsTextUTF8(strInText) != True):
                #文字是否GB2312?
                if( g_C_SkCharset.IsTextGB2312(strInText) == True):
                    strUnicodeText = unicode( strInText, 'GB2312', errors='ignore')
                else:  #是GB2312, utf8,unicode以外的其他类型
                    old_charset = chardet.detect(strInText)['encoding']
                    strUnicodeText = strInText.decode(old_charset)
                strRetText = strUnicodeText.encode( 'utf-8')
            else: #是utf8，直接返回
                strRetText = strInText
        else: #是unicode，直接转换
            strUnicodeText = strInText
            strRetText = strUnicodeText.encode( 'utf-8')
        return strRetText
    
    @staticmethod
    def CopyChangeFileToUTF8(strInFileName, strOutFileName):
        #将文件改成UTF8格式
        
        #读取旧内容
        fileOrig = open( strInFileName)
        strOrigText = fileOrig.read()
        fileOrig.close()
        
        strUTF8Content = g_C_SkCharset.ChangeTextToUTF8( strOrigText)
        fileDest = open( strOutFileName, 'w')
        fileDest.write( strUTF8Content)
        fileDest.close()

    @staticmethod
    def ChangeTextToUnicode(strInText):
        #将文字改成Unicode格式
        strUnicodeText = ''
        if( g_C_SkCharset.IsTextUnicode(strInText)): #是否已经 utf-8?
            strUnicodeText = strInText
        elif( g_C_SkCharset.IsTextUTF8(strInText) == True):
            strUnicodeText = unicode( strInText, 'utf-8', errors='ignore')
            #文字是否GB2312?
        elif( g_C_SkCharset.IsTextGB2312(strInText) == True):
            strUnicodeText = unicode( strInText, 'GB2312', errors='ignore')
        elif (type(strInText) == str):
            try:
                strUnicodeText = strInText.decode('gbk')
            except Exception as e:
                strUnicodeText = strInText
        else:  #是否Unicode?
            old_charset = chardet.detect(strInText)['encoding']
            strUnicodeText = strInText.decode(old_charset, 'ignore')
        return strUnicodeText
    
    @staticmethod
    def CopyChangeFileToUnicode(strInFileName, strOutFileName):
        #将文件改成Unicode格式
        
        #读取旧内容
        fileOrig = open( strInFileName)
        strOrigText = fileOrig.read()
        fileOrig.close()
        
        strUnicodeContent = g_C_SkCharset.ChangeTextToUnicode( strOrigText)
        fileDest = open( strOutFileName, 'w')
        fileDest.write( strUnicodeContent)
        fileDest.close()


# 识别字符序列变换算法，当前支持标准的MD5、SHA-1、Base64，及主流的URL编码、HTML编码
class g_CTextTypeCheck:
    # MD5判断函数
    @staticmethod
    def checkMD5(inStr):
        MD5KeyStrs = '0123456789abcdefABCDEF'
        inStr = inStr.strip()  # 判断MD5的时候把输入两端的空格切掉
        if (len(inStr) != 16) and (len(inStr) != 32):
            return False
        else:
            for eachChar in inStr:
                if eachChar not in MD5KeyStrs:
                    return False
            return True

    # SHA1判断函数
    @staticmethod
    def checkSHA1(inStr):
        SHA1KeyStrs = '0123456789abcdefABCDEF'
        inStr = inStr.strip()  # 判断SHA-1的时候把输入两端的空格切掉
        if len(inStr) != 40:
            return False
        else:
            for eachChar in inStr:
                if eachChar not in SHA1KeyStrs:
                    return False
            return True

    # Base64判断函数
    @staticmethod
    def checkBase64(inStr):
        Base64KeyStrs = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
        inStr = inStr.strip()  # 判断Base64的时候把输入两端的空格切掉
        if len(inStr) % 4 != 0:
            return False
        else:
            for eachChar in inStr:
                if eachChar not in Base64KeyStrs:
                    return False
            return True

    # URL编码判断函数
    @staticmethod
    def checkURLCode(inStr):
        reURLCode = '%[0-9a-fA-F][0-9a-fA-F]'  # 正则表达式
        reResultList = re.findall(reURLCode, inStr)
        if len(reResultList) == 0:
            return False
        else:
            return True

    # HTML编码判断函数
    @staticmethod
    def checkHTMLCode(inStr):
        htmlEncodeTuple = ('&lt;', '&gt;', '&amp;', '&#039;', '&quot;', '&nbsp;', '&#x27;', '&#x2F;')
        for each in htmlEncodeTuple:
            if each in inStr:
                return True
        return False

    # 总的调度函数，负责调用各个算法的判断函数
    @staticmethod
    def checkInput(inStr):
        if g_CTextTypeCheck.checkMD5(inStr):
            resStr = 'MD5'
            return resStr
        if g_CTextTypeCheck.checkSHA1(inStr):
            resStr = 'SHA-1'
            return resStr
        if g_CTextTypeCheck.checkBase64(inStr):
            resStr = 'Base64'
            return resStr
        if g_CTextTypeCheck.checkURLCode(inStr):  # 考虑到 URL编码 与 HTML编码可能会同时出现
            resStr = 'URLCode'
            if g_CTextTypeCheck.checkHTMLCode(inStr):
                resStr = 'URLCode + HTMLCode'
                return resStr
            else:
                return resStr
        if g_CTextTypeCheck.checkHTMLCode(inStr):
            resStr = 'HTMLCode'
            return resStr

        resStr = 'UnKnown'
        return resStr

    pass
