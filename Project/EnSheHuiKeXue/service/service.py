# -*-coding:utf-8-*-

import ast
import re
import hashlib
import langid
from scrapy import Selector
from bs4 import BeautifulSoup

from Utils import timers
from Utils.captcha import RecognizeCode
from Utils.verfication_code import VerificationCode


class DomResultHolder(object):
    def __init__(self):
        self.dict = {}
        self.text = None

    def get(self, mode, text):
        if text != self.text:
            self.dict.clear()
            self.text = text

        if mode in self.dict:
            return self.dict[mode]

        if mode == 'Selector':
            self.dict[mode] = Selector(text=text)
            return self.dict[mode]

        if mode == 'BeautifulSoup':
            self.dict[mode] = BeautifulSoup(text, 'html.parser')
            return self.dict[mode]

        raise NotImplementedError


class Server(object):
    def __init__(self, logging):
        self.logger = logging
        self.dom_holder = DomResultHolder()

    # ---------------------
    # task script
    # ---------------------

    # 数据类型转换
    @staticmethod
    def get_eval_response(task_data):
        return ast.literal_eval(task_data)

    # 获取期刊列表页总页数
    def get_journal_total_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            span = selector.xpath("//span[@id='lblCurrentPage']/text()").extract_first()
            total_page = re.findall(r"\d+/(\d+)", span)[0]

        except Exception:
            return 1

        return total_page

    # 获取期刊详情种子及附加信息
    def get_journal_list(self, text):
        journal_data_list = []
        paper_catalog_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            div_list = selector.xpath("//div[a[@class='btnnoimg']]")
            for a in div_list:
                journal_dict = {}
                paper_dict = {}
                journal_dict['url'] = 'http://103.247.176.188/' + a.xpath(
                    "./a[@class='btnnoimg']/@href").extract_first()
                journal_data_list.append(journal_dict)

                paper_dict['url'] = 'http://103.247.176.188/' + a.xpath(
                    "./a[@class='btnnoimg2']/@href").extract_first() + '&ob=dd'
                paper_dict['journalUrl'] = journal_dict['url']
                paper_catalog_list.append(paper_dict)

        except Exception:
            return journal_data_list, paper_catalog_list

        return journal_data_list, paper_catalog_list

    # 获取论文列表页总页数
    def get_paper_total_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            total_data = selector.xpath("//div[@class='term-title']//td/b/text()").extract_first()
            total_page = int(total_data)//10 + 1 if int(total_data) % 10 else int(total_data)//10

        except Exception:
            total_page = 1

        return total_page

    # 获取论文详情及全文种子
    def get_paper_list(self, text, journal_url):
        paper_data_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            div_list = selector.xpath("//div[a[@class='btnnoimg']]")
            for a in div_list:
                paper_dict = {}
                if a.xpath("./a[@class='btnnoimg']"):
                    paper_dict['url'] = 'http://103.247.176.188/' + a.xpath(
                        "./a[@class='btnnoimg']/@href").extract_first()
                else:
                    continue
                if a.xpath("./a[@class='btnnoimg2']"):
                    paper_dict['pdfUrl'] = 'http://103.247.176.188/' + a.xpath(
                        "./a[@class='btnnoimg2']/@href").extract_first()
                else:
                    paper_dict['pdfUrl'] = ''
                paper_dict['journalUrl'] = journal_url
                paper_data_list.append(paper_dict)

        except Exception:
            return paper_data_list

        return paper_data_list

    # 获取下一页
    def get_next_page(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            next_a = selector.xpath("//div[contains(@class, 'pages')]/a[text()='下一页']/@href").extract_first()
            next_url = 'http://103.247.176.188/' + next_a

        except Exception:
            next_url = None

        return next_url

    # 获取验证码参数
    def get_captcha(self, text):
        captcha_data = {}
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            captcha_data['__VIEWSTATE'] = selector.xpath("//input[@id='__VIEWSTATE']/@value").extract_first()
            captcha_data['__EVENTVALIDATION'] = selector.xpath("//*[@id='__EVENTVALIDATION']/@value").extract_first()
            captcha_data['btnOk'] = selector.xpath("//*[@id='btnOk']/@value").extract_first()

        except Exception:
            return captcha_data

        return captcha_data

    # 获取图片url
    def get_img_url(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            img_url = 'http://103.247.176.188/' + selector.xpath("//img[@id='imgCode1']/@src").extract_first()

        except Exception:
            return ''

        return img_url

    # ---------------------
    # data script
    # ---------------------

    # ====== 期刊、论文、文档实体
    # 是否包含中文（判断语种）
    def hasChinese(self, data):
        for ch in data:
            if '\u4e00' <= ch <= '\u9fa5':
                return True

        return False

    # 语种识别
    @staticmethod
    def get_lang(text):
        return langid.classify(text)[0]

    # 标题
    def get_journal_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h1/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 字段值通用获取
    def get_normal_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(
                para)).extract_first().strip()

        except Exception:
            field_value = ""

        return field_value

    # 摘要获取（区分摘要、英文摘要）
    def get_abstract_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath(
                "//tr/td[span[contains(text(), '{}') and not(contains(text(), '英文'))]]/following-sibling::td[1]/text()".format(
                    para)).extract_first().strip()

        except Exception:
            field_value = ""

        return field_value

    # 字段多值获取
    def get_multi_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(
                para)).extract_first().strip()
            multi_avlue = re.sub(r"\s*[,，]\s*", "|", field_value)

        except Exception:
            multi_avlue = ""

        return multi_avlue

    # 字段多值获取
    def get_more_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath(
                "//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/a/text()".format(para)).extract()
            multi_avlue = '|'.join(field_value)

        except Exception:
            multi_avlue = ""

        return multi_avlue

    # 关键词多值获取（关键词）
    def get_keyword_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            keyword = re.sub(r"[\.。;；]$", "", selector.xpath(
                "//tr/td[span[contains(text(), '{}') and not(contains(text(), '英文'))]]/following-sibling::td[1]/text()".format(
                    para)).extract_first().strip())
            if ';' in keyword or '；' in keyword:
                keywords = re.sub(r"\s*[;；]\s*", "|", keyword).strip()
            elif '.' in keyword:
                keywords = re.sub(r"\s*\.\s*", "|", keyword).strip()
            else:
                return keyword

        except Exception:
            keywords = ""

        return keywords

    # 关键词多值获取（英文关键词）
    def get_en_keyword_value(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            keyword = re.sub(r"[\.。;；]$", "", selector.xpath(
                "//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(
                    para)).extract_first().strip())
            if ';' in keyword or '；' in keyword:
                keywords = re.sub(r"\s*[;；]\s*", "|", keyword).strip()
            elif '.' in keyword:
                keywords = re.sub(r"\s*\.\s*", "|", keyword).strip()
            else:
                return keyword

        except Exception:
            keywords = ""

        return keywords

    # 全文链接
    def get_full_link(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            link = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/a/@href".format(
                para)).extract_first().strip()

        except Exception:
            link = ""

        return link

    # 中图分类
    def get_classification_value(self, text, para):
        classi_list = []
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            field_value = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(
                para)).extract_first().strip()
            value_list = re.split(r"[,，]", field_value)
            for value in value_list:
                classi_dict = {
                    'code': re.split(r"[:：]", value)[0].strip(),
                    'type': re.split(r"[:：]", value)[1].strip()
                }
                classi_list.append(classi_dict)

        except Exception:
            return classi_list

        return classi_list

    # 期刊网址
    def get_journal_website(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            website = selector.xpath("//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/a/@href".format(
                para)).extract_first().strip()

        except Exception:
            website = ""

        return website

    # ====== 论文实体
    # 标题
    def get_paper_title(self, text):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            title = selector.xpath("//h1/text()").extract_first().strip()

        except Exception:
            title = ""

        return title

    # 作者单位
    def get_author_affiliation(self, text, para):
        selector = self.dom_holder.get(mode='Selector', text=text)
        try:
            affiliation_list = selector.xpath(
                "//tr/td[span[contains(text(), '{}')]]/following-sibling::td[1]/text()".format(para)).extract()
            affiliation = '|'.join(affiliation_list).strip()

        except Exception:
            affiliation = ""

        return affiliation

    # =========== 文档实体 =============
    # 获取文档
    def getDocs(self, pdfData, size):
        labelObj = {}
        return_docs = []
        try:
            if pdfData:
                if pdfData['url']:
                    picObj = {
                        'url': pdfData['url'],
                        'title': pdfData['bizTitle'],
                        'desc': "",
                        'sha': hashlib.sha1(pdfData['url'].encode('utf-8')).hexdigest(),
                        'format': 'PDF',
                        'size': size,
                        'ss': 'document'
                    }
                    return_docs.append(picObj)
                labelObj['全部'] = return_docs
        except Exception:
            labelObj['全部'] = []

        return labelObj

    # 关联期刊
    def rela_journal(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '期刊'
        except Exception:
            return e

        return e

    # 关联文档
    def rela_document(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '文档'
        except Exception:
            return e

        return e

    # 关联论文
    def rela_paper(self, url, key, sha):
        e = {}
        try:
            e['url'] = url
            e['key'] = key
            e['sha'] = sha
            e['ss'] = '论文'
        except Exception:
            return e

        return e


class CaptchaProcessor(object):
    def __init__(self, server, downloader, session, logger):
        self.server = server
        self.downloader = downloader
        self.session = session
        self.logger = logger
        self.recognize_code = RecognizeCode(self.logger)
        # self.verfication_code = VerificationCode('mingxing123', 'qazwsx123', self.logger)
        self.captcha_timer = timers.Timer()
        self.total_timer = timers.Timer()
        self.request_timer = timers.Timer()

    def is_captcha_page(self, resp):
        if len(resp.content) > 2048:
            return False
        if '验证码' in resp.text:
            return True
        return False

    def process_first_request(self, url, method, s, ranges=None):
        self.logger.info('process start | 请求开始 | url: {}'.format(url))
        self.total_timer.start()
        self.request_timer.start()
        resp = self.downloader.get_resp(url=url, method=method, s=s, ranges=ranges)
        self.logger.info('process | 一次请求完成时间 | use time: {} | url: {}'.format(self.request_timer.use_time(), url))
        return resp

    def process(self, resp):
        retry_count = 10
        captcha_page = self.is_captcha_page(resp)
        for i in range(retry_count):
            if captcha_page:
                try:
                    self.logger.info('process | 出现验证码')
                    self.captcha_timer.start()
                    # 获取验证码及相关参数
                    form_data = self.server.get_captcha(resp.text)
                    image_url = self.server.get_img_url(resp.text)
                    img_content = self.downloader.get_resp(url=image_url, method='GET', s=self.session).content
                    # data_dict = self.verfication_code.get_code_from_img_content(img_content)
                    # code = data_dict['result']
                    code = self.recognize_code.image_data(img_content, show=False, length=4,
                                                          invalid_charset="^0-9^A-Z^a-z")
                    form_data['iCode'] = code
                    self.logger.info('process | 一次验证码处理完成 | use time: {}'.format(self.captcha_timer.use_time()))
                    # 带验证码访问
                    self.request_timer.start()
                    real_url = resp.url
                    resp = self.downloader.get_resp(url=real_url, method='POST', data=form_data, s=self.session)
                    if resp is None:
                        self.logger.error(
                            'process end | 验证码识别失败总时间 | use time: {} | url: {} | count: {}'.format(
                                self.total_timer.use_time(),
                                real_url, i+1))
                        return
                    # 判断是否还有验证码
                    captcha_page = self.is_captcha_page(resp)
                    # if captcha_page:
                    #     self.logger.info('captcha | 验证码错误')
                        # self.verfication_code.report_error(data_dict['id'])
                    self.recognize_code.report(img_content, code, not captcha_page)
                    self.logger.info(
                        'process | 一次请求完成时间 | use time: {} | url: {}'.format(self.request_timer.use_time(), resp.url))
                except Exception:
                    self.logger.error(
                        'process end | 验证码识别失败总时间 | use time: {} | url: {} | count: {}'.format(
                            self.total_timer.use_time(),
                            resp.url, i))
                    return
            else:
                self.logger.info(
                    'process end | 请求成功总时间 | use time: {} | url: {} | count: {}'.format(self.total_timer.use_time(),
                                                                                        resp.url, i))
                return resp

        self.logger.error(
            'process end | 验证码识别失败总时间 | use time: {} | url: {} | count: {}'.format(self.total_timer.use_time(),
                                                                                   resp.url, retry_count))

        return
