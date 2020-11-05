# -*-coding:utf-8-*-

'''

'''
import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import time
import json
import requests
import traceback
import multiprocessing
from multiprocessing import Pool, Process
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.ZhiWangLunWen.middleware import download_middleware
from Project.ZhiWangLunWen.service import service
from Project.ZhiWangLunWen.dao import dao
from Project.ZhiWangLunWen import config

log_file_dir = 'ZhiWangLunWen'  # LOG日志存放路径
LOGNAME = '<期刊论文_论文_task>'  # LOG名
LOGGING = log.ILog(log_file_dir, LOGNAME)


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.Downloader(logging=LOGGING,
                                                                 proxy_type=config.PROXY_TYPE,
                                                                 timeout=config.TIMEOUT)
        self.server = service.QiKanLunWen_LunWen(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_MAX_NUMBER,
                           redispool_number=config.REDIS_POOL_MAX_NUMBER)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        # 初始化期刊时间列表种子模板
        self.qiKan_time_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetJournalYearList?pcode={}&pykm={}&pIdx=0'
        # 初始化论文列表种子模板
        self.lunLun_url_template = 'http://navi.cnki.net/knavi/JournalDetail/GetArticleList?year={}&issue={}&pykm={}&pageIdx=0&pcode={}'
        # 会话
        self.s = requests.Session()
        # 记录存储种子数量
        self.num = 0

    def __getResp(self, url, method, s=None, data=None, cookies=None, referer=None):
        # 发现验证码，请求页面3次
        resp = None
        for i in range(3):
            resp = self.download_middleware.getResp(s=s, url=url, method=method, data=data,
                                                    cookies=cookies, referer=referer)
            if resp:
                if '请输入验证码' in resp.text or len(resp.text) < 10:
                    continue

            return resp

        else:
            LOGGING.error('页面出现验证码: {}'.format(url))
            return resp

    def run(self, category):
        # 数据类型转换
        task = self.server.getEvalResponse(category)
        # print(task)
        qiKanUrl = task['url']
        xueKeLeiBie = task['s_xueKeLeiBie']

        # # 创建cookies
        # cookies = self.download_middleware.create_cookie(url=qiKanUrl)
        # if not cookies:
        #     # 队列一条任务
        #     self.dao.QueueOneTask(key=config.REDIS_QIKAN_CATALOG, data=task)
        #     return
        # # 设置会话cookies
        # self.s.cookies = cookies

        # 生成单个知网期刊的时间列表种子
        qiKanTimeListUrl, pcode, pykm = self.server.qiKanTimeListUrl(qiKanUrl, self.qiKan_time_url_template)
        # print(qiKanTimeListUrl)
        # 获取期刊时间列表页html源码
        qikanTimeListHtml = self.__getResp(url=qiKanTimeListUrl, method='GET')
        if not qikanTimeListHtml:
            LOGGING.error('期刊时间列表页获取失败, url: {}'.format(qiKanTimeListUrl))
            # 队列一条任务
            self.dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
            return

        # 获取期刊【年】、【期】列表
        # qiKanTimeList = self.server.getQiKanTimeList(qikanTimeListHtml)
        # if qiKanTimeList:
        # 循环获取指定年、期页文章列表页种子
        for qikan_year in self.server.getQiKanTimeList(qikanTimeListHtml):
            # 获取文章列表页种子
            articleUrl = self.server.getArticleListUrl(url=self.lunLun_url_template,
                                                       data=qikan_year,
                                                       pcode=pcode,
                                                       pykm=pykm)
            # print(articleUrl)
            # for articleUrl in articleListUrl:
            # 获取论文列表页html源码
            article_list_html = self.__getResp(url=articleUrl, method='GET')
            if not qikanTimeListHtml:
                LOGGING.error('论文列表页html源码获取失败, url: {}'.format(articleUrl))
                # 队列一条任务
                self.dao.queue_one_task_to_redis(key=config.REDIS_QIKAN_CATALOG, data=task)
                return

            # 获取论文种子列表
            article_url_list = self.server.getArticleUrlList(article_list_html, qiKanUrl, xueKeLeiBie)
            if article_url_list:
                for paper_url in article_url_list:
                    # print(paper_url)
                    # 存储种子
                    self.num += 1
                    LOGGING.info('已抓种子数量: {}'.format(self.num))
                    self.dao.save_task_to_mysql(table=config.MYSQL_PAPER, memo=paper_url, ws='中国知网', es='期刊论文')
            else:
                LOGGING.error('论文种子列表获取失败')
        else:
            LOGGING.info('年、期列表获取完毕')

    def start(self):
        while 1:
            # 获取任务
            category_list = self.dao.get_task_from_redis(key=config.REDIS_QIKAN_CATALOG,
                                                         count=20,
                                                         lockname=config.REDIS_QIKAN_CATALOG_LOCK)
            # print(category_list)
            LOGGING.info('获取{}个任务'.format(len(category_list)))

            if category_list:
                # # 创建gevent协程
                # g_list = []
                # for category in category_list:
                #     s = gevent.spawn(self.run, category)
                #     g_list.append(s)
                # gevent.joinall(g_list)

                # 创建线程池
                threadpool = ThreadPool()
                for category in category_list:
                    threadpool.apply_async(func=self.run, args=(category,))

                threadpool.close()
                threadpool.join()

                time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

    def queue_task(self):
        while 1:
            # 查询redis队列中任务数量
            url_number = self.dao.select_task_number(key=config.REDIS_QIKAN_CATALOG)
            if url_number == 0:
                LOGGING.info('redis已无任务，准备开始队列任务。')
                # 获取任务
                new_task_list = self.dao.get_task_list_from_mysql(table=config.MYSQL_MAGAZINE, ws='中国知网', es='期刊论文', count=10000)
                # print(new_task_list)
                # 队列任务
                self.dao.queue_tasks_from_mysql_to_redis(key=config.REDIS_QIKAN_CATALOG, data=new_task_list)
            else:
                LOGGING.info('redis剩余{}个任务'.format(url_number))

            time.sleep(1)

def queue_start():
    main = SpiderMain()
    try:
        main.queue_task()
        # main.run("{'url': 'http://navi.cnki.net/knavi/PPaperDetail?pcode=CDMD&logo=GJZSC', 'value': '0018'}")
    except:
        LOGGING.error(str(traceback.format_exc()))

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.run('{"url": "http://navi.cnki.net/knavi/JournalDetail?pcode=CJFD&pykm=KYGL", "title": "科研管理", "s_xueKeLeiBie": "基础科学_基础科学综合", "s_zhongWenHeXinQiKanMuLu": ""}')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    LOGGING.info('======The Start!======')
    begin_time = time.time()
    queue_process = Process(target=queue_start)
    queue_process.start()
    spider_process = Process(target=process_start)
    spider_process.start()
    # process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is %.2fs======' % (end_time - begin_time))
