# -*-coding:utf-8-*-

'''

'''
import sys
import os
import ast
import re
import time
from urllib.parse import quote,unquote
import requests
from lxml import etree
from lxml.html import fromstring, tostring
from scrapy import Selector

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")



class Server(object):
    def __init__(self, logging):
        self.logging = logging

    # ---------------------
    # task script
    # ---------------------

    # 数据类型转换
    def getEvalResponse(self, task_data):
        return ast.literal_eval(task_data)

    # 获取研究领域名称及种子
    def getCatalogList(self, json):
        return_data = []
        try:
            datas = json['data']
            for data in datas:
                dict = {}
                dict['code'] = data['code']
                # 请求第一页
                dict['num'] = 0
                dict['xueKeLeiBie'] = data['depC']
                dict['totalCount'] = data['num']
                return_data.append(dict)

        except Exception:
            return return_data

        return return_data

    # 获取详情种子
    def getDetailUrl(self, json, xuekeleibie):
        return_data = []
        try:
            datas = json['data']
            for data in datas:
                data['xueKeLeiBie'] = xuekeleibie
                data['chineseTitle'] = re.sub(r"(\(|（)[^\(（）\)]*?(）|\))$", "", data['chineseTitle']).strip()
                data['authors'] = re.sub(r"(\(\)|\(#\)|\(\*\)|<.*?>)", "", data['authors']).strip()
                t = round(time.time()* 1000)
                data['url'] = 'http://kns.cnki.net/kns/brief/brief.aspx?pagename=ASP.brief_default_result_aspx&isinEn=1&dbPrefix=SCDB&dbCatalog=%e4%b8%ad%e5%9b%bd%e5%ad%a6%e6%9c%af%e6%96%87%e7%8c%ae%e7%bd%91%e7%bb%9c%e5%87%ba%e7%89%88%e6%80%bb%e5%ba%93&ConfigFile=SCDBINDEX.xml&research=off&t=' + str(t) + '&keyValue=' + quote(data['chineseTitle']) + '&S=1&sorttype='
                data['pdfUrl'] = 'http://ir.nsfc.gov.cn/paperDownload/' + data['fulltext'] + '.pdf'
                return_data.append(data)

        except Exception:
            return return_data

        return return_data

    # 获取搜索结果条数
    def getResult(self, text):
        selector = Selector(text=text)
        try:
            result = selector.xpath("//div[@class='TitleLeftCell']/div//text()").extract_first().strip()
            num = int(re.findall(r"\s+(\d+)\s+", result)[0])

        except Exception:
            num = ''

        return num

    # 获取搜索结果条数
    def nextPage(self, text):
        selector = Selector(text=text)
        try:
            next_href = selector.xpath("//div[@class='TitleLeftCell']/div//a[contains(text(), '下一页')]/@href").extract_first().strip()
            next_page = 'https://kns.cnki.net/kns/brief/brief.aspx' + next_href

        except Exception:
            next_page = ''

        return next_page

    # 获取每条结果的标题、第一作者、来源
    def getResults(self, text):
        results = []
        selector = Selector(text=text.replace('<TR', '<tr').replace('</TR>', '</tr>'))
        try:
            tr_list = selector.xpath("//td[@class='author_flag']/..")
            for tr in tr_list:
                dict = {}
                try:
                    # 获取标题、链接
                    title_tag = tr.xpath("./td[@class='author_flag']/preceding-sibling::td[1]/a")[0]
                    if title_tag:
                        dict['title'] = ''.join(title_tag.xpath(".//text()").extract()).strip()
                        href = title_tag.xpath('./@href').extract_first().strip()
                        if re.findall(r"DbCode=(.*?)&", href, re.I):
                            dbcode = re.findall(r"DbCode=(.*?)&", href, re.I)[0]
                        elif re.findall(r"DbCode=(.*)", href, re.I):
                            dbcode = re.findall(r"DbCode=(.*)", href, re.I)[0]
                        else:
                            continue

                        if re.findall(r"FileName=(.*?)&", href, re.I):
                            filename = re.findall(r"FileName=(.*?)&", href, re.I)[0]
                        elif re.findall(r"FileName=(.*)", href, re.I):
                            filename = re.findall(r"FileName=(.*)", href, re.I)[0]
                        else:
                            continue

                        if re.findall(r"DbName=(.*?)&", href, re.I):
                            dbname = re.findall(r"DbName=(.*?)&", href, re.I)[0]
                        elif re.findall(r"DbName=(.*)", href, re.I):
                            dbname = re.findall(r"DbName=(.*)", href, re.I)[0]
                        else:
                            continue

                        dict['url'] = 'http://kns.cnki.net/kcms/detail/detail.aspx?dbcode=' + dbcode + '&filename=' + filename + '&dbname=' + dbname
                    else:
                        continue
                except:
                    continue

                # 获取第一作者
                try:
                    author_tag = tr.xpath("./td[@class='author_flag']/a")
                    if author_tag:
                        dict['author'] = author_tag[0].xpath("./text()").extract_first().strip()
                    else:
                        dict['author'] = re.findall(r"(.*?)[;；]", tr.xpath("./td[@class='author_flag']/text()").extract_first().strip())[0]
                except:
                    dict['author'] = ''

                try:
                    # 获取来源
                    source = ''.join(tr.xpath("./td[@class='author_flag']/following-sibling::td[1]//text()").extract())
                    dict['source'] = source.strip()
                except:
                    dict['source'] = ''

                yield dict

        except Exception:
            return results

        return results

    # ---------------------
    # data script
    # ---------------------

    # ====== 论文实体
    def getFieldValue(self, value):
        try:
            if isinstance(value, str):
                value = value.strip()

        except Exception:
            value = ""

        return value

    def getMoreFieldValue(self, value):
        try:
            if ';' in value or '；' in value:
                values = re.sub(r"\s*[;；]\s*", "|", value).strip()
            else:
                values = re.sub(r"\s*[,，]\s*", "|", value).strip()

        except Exception:
            values = ""

        return values

    def hasChinese(self, data):
        journal = data
        for ch in journal:
            if '\u4e00' <= ch <= '\u9fa5':
                return True

        return False


    def getXueKeLeiBie(self, json, para, xueke):
        try:
            value = str(json['data'][0][para]).strip()
            if value:
                xuekeleibie = xueke + '_' + value
            else:
                xuekeleibie = xueke

        except Exception:
            xuekeleibie = xueke

        return xuekeleibie

    # 关联文档
    def guanLianWenDang(self, url, id, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = id
            e['sha'] = sha
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    # ====== 文档实体
    # 关联论文
    def guanLianLunWen(self, url, id, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = id
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e


























