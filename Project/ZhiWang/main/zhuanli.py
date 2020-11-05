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
import requests
from datetime import datetime
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Log import log
from Project.ZhiWang.middleware import download_middleware
from Project.ZhiWang.service import service
from Project.ZhiWang.dao import dao
from Project.ZhiWang import config

log_file_dir = 'ZhiWang'  # LOG日志存放路径
LOGNAME = '<知网_专利数据修改_data>'  # LOG名
NAME = '知网_专利数据修改_data'  # 爬虫名
LOGGING = log.ILog(log_file_dir, LOGNAME)

INSERT_SPIDER_NAME = False  # 爬虫名入库
INSERT_DATA_NUMBER = False  # 记录抓取数据量


class BastSpiderMain(object):
    def __init__(self):
        self.download_middleware = download_middleware.ShiYongDownloader(logging=LOGGING,
                                                                  proxy_type=config.PROXY_TYPE,
                                                                  timeout=config.TIMEOUT,
                                                                  proxy_country=config.COUNTRY,
                                                                  proxy_city=config.CITY)
        self.server = service.Server(logging=LOGGING)
        self.dao = dao.Dao(logging=LOGGING,
                           mysqlpool_number=config.MYSQL_POOL_NUMBER,
                           redispool_number=config.REDIS_POOL_NUMBER)

        # 数据库录入爬虫名
        if INSERT_SPIDER_NAME is True:
            self.dao.save_spider_name(name=NAME)


class SpiderMain(BastSpiderMain):
    def __init__(self):
        super().__init__()

    def patent(self, sha):
        save_data = {}
        # 获取专利类型
        save_data['zhuanLiLeiXing'] = "发明公开"
        # 生成sha
        save_data['sha'] = sha
        # 生成ss ——实体
        save_data['ss'] = '专利'
        # 生成es ——栏目名称
        save_data['es'] = '发明公开'
        # 生成clazz ——层级关系
        save_data['clazz'] = '专利'

        # 存储数据
        success = self.dao.save_data_to_hbase(data=save_data)
        if success:
            LOGGING.info('专利数据存储成功, sha: {}'.format(sha))
        else:
            LOGGING.error('专利数据存储失败, sha: {}'.format(sha))

    def start(self):
        with open ('zhuanli.txt') as f:
            for line in f:
                sha = line.replace('\n', '')
                print(sha)
                self.patent(sha)

            # while True:
            #     sha = f.readline()
            #     if not sha:
            #         break
            #     self.patent(sha)

def process_start():
    main = SpiderMain()
    try:
        main.start()
        # main.patent(sha='0ea3c6d368232fe48e304fd1c025c47ef9d49831')
    except:
        LOGGING.error(str(traceback.format_exc()))


if __name__ == '__main__':
    begin_time = time.time()
    process_start()
    end_time = time.time()
    LOGGING.info('======The End!======')
    LOGGING.info('======Time consuming is {}s======'.format(int(end_time - begin_time)))
