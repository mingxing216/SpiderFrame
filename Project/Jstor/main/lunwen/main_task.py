# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import traceback
import datetime
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../../")
from Log import log
from Project.Jstor.middleware import download_middleware
from Project.Jstor.service import service
from Project.Jstor.dao import dao
from Project.Jstor import config

log_file_dir = 'Jstor'  # LOG日志存放路径
LOGNAME = 'JSTOR_期刊论文_task'  # LOG名
NAME = 'JSTOR_期刊论文_task'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = INSERT_DATA_NUMBER = False # 爬虫名入库, 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.DownloaderMiddleware(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.QiKanLunWen_LunWenServer(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.saveSpiderName(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()
        self.index_url = 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=&ed=&acc=dfr'
        self.cookie_dict = ''
        self.num = 0

    def __getResp(self, func, url, mode, data=None, cookies=None, referer=None):
        while 1:
            resp = func(url=url, mode=mode, data=data, cookies=cookies, referer=referer)
            if resp['code'] == 0:
                response = resp['data']
                if '请输入验证码' in response.text:
                    LOGGING.info('出现验证码')
                    continue

                else:
                    return response

            if resp['code'] == 1:
                return None

    def get_yearTask(self):
        # 存放带年份的期刊种子
        catalog_urls = []

        # 1660年至今,入口种子添加年份参数，获取到所有期刊论文种子
        for n in range(1660, datetime.datetime.now().year+1):
            catalog_urls.append('https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=' + str(n) + '&ed=' + str(n+1) + '&acc=dfr')

        # print(catalog_urls)

        # catalog_urls = ['https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1929&ed=1930&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1940&ed=1941&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1941&ed=1942&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1946&ed=1947&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1948&ed=1949&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1954&ed=1955&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1958&ed=1959&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1963&ed=1964&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1975&ed=1976&acc=dfr', 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=1994&ed=1995&acc=dfr']
        print(len(catalog_urls))

        # 队列任务
        self.dao.QueueJobTask(key=config.REDIS_YEAR, data=catalog_urls)

    def run(self, catalog_url):
        # 获取cookie
        self.cookie_dict = self.download_middleware.create_cookie()
        # cookie创建失败，停止程序
        if not self.cookie_dict:
            return

        # 访问带年份的期刊种子，获取响应
        index_resp = self.__getResp(func=self.download_middleware.getResp,
                                    url=catalog_url,
                                    mode='GET',
                                    cookies=self.cookie_dict,
                                    referer=self.index_url)
        if not index_resp:
            LOGGING.error('年份页面响应获取失败, url: {}'.format(catalog_url))
            # 队列一条任务
            self.dao.QueueOneTask(key=config.REDIS_YEAR, data=catalog_url)
            return

        index_text = index_resp.text

        # 遍历所有学科，获取到学科名称及种子
        subject_url_list = self.server.getSubjectUrlList(resp=index_text, index_url=catalog_url)
        # return
        if not subject_url_list:
            return

        # 遍历所有各学科列表url,获取详情url
        for subject in subject_url_list:
            first_url = subject['url']
            xueke = subject['xueKeLeiBie']
            # first_url = 'https://www.jstor.org/dfr/results?searchType=facetSearch&cty_journal_facet=am91cm5hbA%3D%3D&sd=&ed=&disc_developmentalcellbiology-discipline_facet=ZGV2ZWxvcG1lbnRhbGNlbGxiaW9sb2d5LWRpc2NpcGxpbmU%3D'

            # 获取cookie
            self.cookie_dict = self.download_middleware.create_cookie()

            if not self.cookie_dict:
                return
            # 请求页面，获取响应
            first_resp = self.__getResp(func=self.download_middleware.getResp,
                                        url=first_url,
                                        mode='GET',
                                        cookies=self.cookie_dict,
                                        referer=catalog_url)
            if not first_resp:
                LOGGING.error('列表首页响应获取失败, url: {}'.format(first_url))
                # 队列一条任务
                self.dao.QueueOneTask(key=config.REDIS_YEAR, data=catalog_url)
                return
            # 响应成功，添加log日志
            LOGGING.info('已进入列表第1页')
            # 获取首页详情url及传递学科名称
            if first_resp:
                first_urls = self.server.getDetailUrl(resp=first_resp.text, xueke=xueke)
                for url in first_urls:
                    # 保存url
                    self.num += 1
                    LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                    self.dao.saveProjectUrlToMysql(table=config.MYSQL_PAPER, memo=url)
                    # detail_urls.append(url)

            # 判断是否有下一页
            next_page = self.server.hasNextPage(resp=first_resp.text)
            # 翻页
            num = 2

            while True:
                # 如果有，请求下一页，获得响应
                if next_page:
                    next_url = next_page
                    # 获取cookie
                    # self.cookie_dict = self.download_middleware.create_cookie()
                    # if not self.cookie_dict:
                    #     return
                    next_resp = self.__getResp(func=self.download_middleware.getResp,
                                               url=next_url,
                                               mode='GET',
                                               cookies=self.cookie_dict,
                                               referer=first_url)

                    # 如果响应获取失败，重新访问，并记录这一页种子
                    if not next_resp:
                        LOGGING.error('第{}页响应获取失败, url: {}'.format(num, next_url))
                        continue
                    # 响应成功，添加log日志
                    LOGGING.info('已翻到第{}页'.format(num))

                    num += 1

                    # 获得响应成功，提取详情页种子
                    next_text = next_resp.text
                    next_urls = self.server.getDetailUrl(resp=next_text, xueke=xueke)
                    # print(next_urls)
                    for url in next_urls:
                        # 保存url
                        self.num += 1
                        LOGGING.info('当前已抓种子数量: {}'.format(self.num))
                        self.dao.saveProjectUrlToMysql(table=config.MYSQL_PAPER, memo=url)
                        # detail_urls.append(url)

                    # print(len(detail_urls))

                    # 判断是否有下一页
                    next_page = self.server.hasNextPage(resp=next_text)

                    # break
                else:
                    LOGGING.info('已翻到最后一页')
                    break

            # break

    def start(self):
        while 1:
            # 获取任务
            task_list = self.dao.getTask(key=config.REDIS_YEAR,
                                         count=2,
                                         lockname=config.REDIS_YEAR_LOCK)
            LOGGING.info('获取{}个任务'.format(len(task_list)))

            if task_list:
                # 创建线程池
                threadpool = ThreadPool()
                for url in task_list:
                    threadpool.apply_async(func=self.run, args=(url,))

                threadpool.close()
                threadpool.join()

                time.sleep(1)
            else:
                LOGGING.info('队列中已无任务，结束程序')
                return

def process_start():
    main = SpiderMain()
    try:
        main.start()
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    main = SpiderMain()
    try:
        main.get_yearTask()
    except:
        LOGGING.error(str(traceback.format_exc()))
    po = Pool(4)
    for i in range(4):
        po.apply_async(func=process_start)
    po.close()
    po.join()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
