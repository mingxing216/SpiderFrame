# -*-coding:utf-8-*-

'''

'''
# import gevent
# from gevent import monkey
# monkey.patch_all()
import sys
import os
import time
import traceback
import hashlib
import random
import requests
from datetime import datetime
from contextlib import closing
import json
import threading
from io import BytesIO
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Utils import timeutils
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.middleware import download_middleware
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.service import service
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui.dao import dao
from Project.GuoJiaZiRanKeXueJiJinWeiYuanHui import config
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


log_file_dir = 'ZiRanKeXue'  # LOG日志存放路径
LOGNAME = '<国家自然科学_论文_data>'  # LOG名
NAME = '国家自然科学_论文_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  stream=config.STREAM,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

        self.profile_url = 'http://ir.nsfc.gov.cn/baseQuery/data/paperInfo'

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None, ranges=None):
        # 发现验证码，请求页面3次
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer, ranges=ranges)
            if resp and resp.headers['Content-Type'].startswith('text'):
                if '请输入验证码' in resp.text:
                    LOGGING.error('出现验证码: {}'.format(url))
                    continue

            return resp

        else:
            return

    # 获取文档实体字段
    def document(self, pdf_dict):
        # 获取页面响应
        pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET')
        LOGGING.info('开始获取内容')
        start_time = time.time()
        if not pdf_resp:
            LOGGING.error('附件响应失败, url: {}'.format(pdf_dict['url']))
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return
        # media_resp.encoding = media_resp.apparent_encoding
        # 判断内容获取是否完整
        if pdf_resp.raw.tell() >= int(pdf_resp.headers['Content-Length']):
            LOGGING.info('handle | 获取内容完整 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), pdf_resp.raw.tell()))
            # 获取二进制内容
            pdf_content = pdf_resp.content
        else:
            LOGGING.info('handle | 获取内容不完整 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), pdf_resp.raw.tell()))
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

        # # 内存中读写
        # bytes_container = BytesIO()
        # # time_begin = time.time()
        # for i in range(3):
        #     try:
        #         # 自动释放连接
        #         with closing(pdf_resp) as response:
        #             for chunk in response.iter_content(chunk_size=4096):
        #                 if chunk:
        #                     # time_end = time.time()
        #                     # if time_end - time_begin >= 2:
        #                     #     LOGGING.info("handle | RequestTooLong Timeout | use time: {}s | length: {}".format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #                     #     # 存储文档种子
        #                     #     self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
        #                     #     return
        #
        #                     bytes_container.write(chunk)
        #                     # time_begin = time.time()
        #     except Exception as e:
        #         LOGGING.info("handle | 获取内容失败 | use time: {}s | length: {} | message: {}".format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue()), e))
        #         # 请求头增加参数
        #         ranges = 'bytes=%d-' % len(bytes_container.getvalue())
        #         # 断点续传
        #         pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET', ranges=ranges)
        #         continue
        #
        #     # 判断内容获取是否完整
        #     if pdf_resp.raw.tell() >= int(pdf_resp.headers['Content-Length']):
        #         LOGGING.info('handle | 获取内容完整 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #         break
        #     else:
        #         LOGGING.info('handle | 获取内容失败 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #         # 请求头增加参数
        #         ranges = 'bytes=%d-' % len(bytes_container.getvalue())
        #         # 断点续传
        #         pdf_resp = self.__getResp(url=pdf_dict['url'], method='GET', ranges=ranges)
        # else:
        #     LOGGING.info('handle | 获取内容不完整 | use time: {}s | length: {}'.format('%.3f' % (time.time() - start_time), len(bytes_container.getvalue())))
        #     # 存储文档种子
        #     self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
        #     return
        #
        # # 获取二进制内容
        # pdf_content = bytes_container.getvalue()

        # with open('profile.pdf', 'wb') as f:
        #     f.write(pdf_resp)
        LOGGING.info('结束获取内容')

        # 存储文档
        succ = self.dao.saveMediaToHbase(media_url=pdf_dict['url'], content=pdf_content, item=pdf_dict, type='test')
        if not succ:
            # # 标题内容调整格式
            # pdf_dict['bizTitle'] = pdf_dict['bizTitle'].replace('"', '\\"').replace("'", "''").replace('\\', '\\\\')
            # # 存储文档种子
            # self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')
            return

        # 文档数据存储字典
        doc_data = {}
        # 获取标题
        doc_data['title'] = pdf_dict['bizTitle']
        # 获取URL
        doc_data['xiaZaiLianJie'] = pdf_dict['url']
        # 文档内容
        doc_data['labelObj'] = self.server.getDocs(pdf_dict)
        # 获取格式
        doc_data['geShi'] = ""
        # 获取大小
        doc_data['daXiao'] = ""
        # 获取标签
        doc_data['biaoQian'] = ""
        # 获取来源网站
        doc_data['laiYuanWangZhan'] = ""
        # 关联论文
        doc_data['guanLianLunWen'] = pdf_dict['relEsse']

        # ===================公共字段
        # url
        doc_data['url'] = pdf_dict['url']
        # 生成key
        doc_data['key'] = pdf_dict['id']
        # 生成sha
        doc_data['sha'] = hashlib.sha1(pdf_dict['id'].encode('utf-8')).hexdigest()
        # 生成ss ——实体
        doc_data['ss'] = '文档'
        # 生成es ——栏目名称
        doc_data['es'] = '论文'
        # 生成ws ——目标网站
        doc_data['ws'] = '国家自然科学基金委员会'
        # 生成clazz ——层级关系
        doc_data['clazz'] = '文档_论文文档'
        # 生成biz ——项目
        doc_data['biz'] = '文献大数据_论文'
        # 生成ref
        doc_data['ref'] = ''

        LOGGING.info('文档数据开始存储')
        # 保存数据到Hbase
        sto = self.dao.saveDataToHbase(data=doc_data)

        if sto:
            LOGGING.info('文档数据存储成功, sha: {}'.format(doc_data['sha']))
            return True
        else:
            LOGGING.error('文档数据存储失败, url: {}'.format(doc_data['url']))
            # # 逻辑删除任务
            # self.dao.deleteLogicTask(table=config.MYSQL_PAPER, sha=sha)
            # 存储文档种子
            self.dao.saveTaskToMysql(table=config.MYSQL_DOCUMENT, memo=pdf_dict, ws='国家自然科学基金委员会', es='期刊论文')

    def handle(self, task_data, save_data):
        # print(task_data)
        id = task_data.get('id')
        sha = hashlib.sha1(id.encode('utf-8')).hexdigest()
        url = 'http://ir.nsfc.gov.cn/paperDetail/' + task_data.get('id')
        xueKeLeiBie = task_data['xueKeLeiBie']

        # 获取标题
        save_data['title'] = task_data.get('chineseTitle')
        # 获取作者
        save_data['zuoZhe'] = self.server.getMoreFieldValue(task_data.get('authors'))
        # # 获取成果类型
        # productType = int(task_data.get('productType'))
        # if productType == 3:
        #     # 成果类型
        #     save_data['chengGuoLeiXing'] = '会议论文'
        #     # es ——栏目名称
        #     save_data['es'] = '会议论文'
        #     # 获取会议名称
        #     save_data['huiYiMingCheng'] = task_data.get('journal')
        #     # 获取语种
        #     if save_data['huiYiMingCheng']:
        #         hasChinese = self.server.hasChinese(task_data.get('journal'))
        #         if hasChinese:
        #             save_data['yuZhong'] = "中文"
        #         else:
        #             save_data['yuZhong'] = "英文"
        #     else:
        #         save_data['yuZhong'] = ""
        # elif productType == 4:
        #     # 成果类型
        #     save_data['chengGuoLeiXing'] = '会议论文'
        #     # es ——栏目名称
        #     save_data['es'] = '期刊论文'
        #     # 获取会议名称
        #     save_data['qiKanMingCheng'] = task_data.get('journal')
        #     # 获取语种
        #     if save_data['qiKanMingCheng']:
        #         hasChinese = self.server.hasChinese(task_data.get('journal'))
        #         if hasChinese:
        #             save_data['yuZhong'] = "中文"
        #         else:
        #             save_data['yuZhong'] = "英文"
        #     else:
        #         save_data['yuZhong'] = ""
        # # 获取数字对象标识符
        # save_data['DOI'] = task_data.get('doi')
        # # 获取时间
        # shiJian = task_data.get('publishDate')
        # if shiJian:
        #     try:
        #         save_data['shiJian'] = timeutils.getDateTimeRecord(shiJian)
        #
        #     except:
        #         save_data['shiJian'] = shiJian
        # else:
        #     save_data['shiJian'] = ""
        # # 获取关键词
        # save_data['guanJianCi'] = task_data.get('zhKeyword')
        # # 获取摘要
        # save_data['zhaiYao'] = task_data.get('zhAbstract')
        # # 获取项目类型
        # save_data['xinagMuLeiXing'] = task_data.get('supportTypeName')
        # # 获取项目编号
        # save_data['xinagMuBianHao'] = self.server.getFieldValue(resp_json, 'fundProjectNo')
        # # 获取项目名称
        # save_data['xinagMuMingCheng'] = self.server.getFieldValue(resp_json, 'fundProject')
        # # 获取研究机构
        # save_data['yanJiuJiGou'] = self.server.getFieldValue(resp_json, 'organization')
        # # 获取点击量
        # save_data['dianJiLiang'] = self.server.getFieldValue(resp_json, 'browseCount')
        # # 获取下载次数
        # save_data['xiaZaiCiShu'] = self.server.getFieldValue(resp_json, 'downloadCount')
        # # 获取其它来源网站
        # save_data['qiTaLaiYuanWangZhan'] = self.server.getFieldValue(resp_json, 'doiUrl')
        # # 获取学科类别
        # save_data['xueKeLeiBie'] = self.server.getXueKeLeiBie(resp_json, 'fieldName', xueKeLeiBie)
        # # 获取学科领域代码
        # save_data['xueKeLingYuDaiMa'] = self.server.getFieldValue(resp_json, 'fieldCode')

        # 获取关联文档
        doc_id = task_data.get('fulltext')
        if doc_id:
            doc_sha = hashlib.sha1(doc_id.encode('utf-8')).hexdigest()
            doc_url = task_data.get('pdfUrl')
            save_data['guanLianWenDang'] = self.server.guanLianWenDang(doc_url, doc_id, doc_sha)

            pdf_dict = {}
            pdf_dict['url'] = doc_url
            pdf_dict['id'] = doc_id
            pdf_dict['bizTitle'] = save_data['title']
            pdf_dict['relEsse'] = self.server.guanLianLunWen(url, id, sha)
            pdf_dict['relPics'] = self.server.guanLianWenDang(doc_url, doc_id, doc_sha)

            # 存储文档实体及文档本身
            suc = self.document(pdf_dict=pdf_dict)
            if not suc:
                return

        else:
            save_data['guanLianWenDang'] = {}

        # ======================公共字段
        # url
        save_data['url'] = url
        # 生成key
        save_data['key'] = id
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '论文'
        # 生成ws ——目标网站
        save_data['ws'] = '国家自然科学基金委员会'
        # 生成clazz ——层级关系
        save_data['clazz'] = '论文_期刊论文'
        # 生成biz ——项目
        save_data['biz'] = '文献大数据_论文'
        # 生成ref
        save_data['ref'] = ''

    def run(self):
        #第一次请求的等待时间
        delay_time = time.time()
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))
        LOGGING.info('handle | download delay | use time: {}s'.format('%.3f' % (time.time() - delay_time)))

        while True:
            # 获取任务
            start_time = time.time()
            task_list = self.dao.getTask(key=config.REDIS_ZIRANKEXUE_TEST, count=1,
                                         lockname=config.REDIS_ZIRANKEXUE_TEST_LOCK)
            if task_list:
                for task in task_list:
                    try:
                        # 创建数据存储字典
                        save_data = {}
                        # json数据类型转换
                        task_data = json.loads(task)
                        sha = task_data['sha']
                        # 获取字段值存入字典并返回sha
                        self.handle(task_data=task_data, save_data=save_data)
                        # 保存数据到Hbase
                        if not save_data:
                            LOGGING.info('没有获取数据, 存储失败')
                            continue
                        if 'sha' not in save_data:
                            LOGGING.info('数据获取不完整, 存储失败')
                            continue
                        LOGGING.info('论文数据开始存储')
                        # 存储数据
                        success = self.dao.saveDataToHbase(data=save_data)

                        if success:
                            LOGGING.info('论文数据存储成功')
                            # # 删除任务
                            # self.dao.deleteTask(table=config.MYSQL_TEST, sha=sha)
                        else:
                            LOGGING.info('论文数据存储失败')
                            # # 逻辑删除任务
                            # self.dao.deleteLogicTask(table=config.MYSQL_TEST, sha=sha)

                        # 逻辑删除任务
                        self.dao.deleteLogicTask(table=config.MYSQL_TEST, sha=sha)

                        LOGGING.info('handle | task complete | use time: {}s'.format('%.3f' % (time.time() - start_time)))

                    except:
                        LOGGING.exception(str(traceback.format_exc()))
            else:
                time.sleep(1)
                continue

    def start(self):
        # gevent.joinall([gevent.spawn(self.run, task) for task in task_list])

        # # 创建gevent协程
        # g_list = []
        # for i in range(8):
        #     s = gevent.spawn(self.run)
        #     g_list.append(s)
        # gevent.joinall(g_list)

        # self.run()

        # 创建线程池
        threadpool = ThreadPool(processes=config.THREAD_NUM)
        for i in range(config.THREAD_NUM):
            threadpool.apply_async(func=self.run)

        threadpool.close()
        threadpool.join()

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run(task="{'id': '207d122a-3a68-41b1-8d8a-f20552f22054', 'xueKeLeiBie': '信息科学部', 'url': 'http://ir.nsfc.gov.cn/paperDetail/207d122a-3a68-41b1-8d8a-f20552f22054'}")
    except:
        LOGGING.exception(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    # process_start()

    po = Pool(processes=config.PROCESS_NUM)
    for i in range(config.PROCESS_NUM):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('====== Time consuming is %.2fs ======' %(end_time - begin_time))
