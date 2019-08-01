# -*-coding:utf-8-*-

'''
下载器
'''

import sys
import os
import requests
import time
import random
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY
from Utils import proxy


def _error(func):
    def wrapper(self, *args, **kwargs):
        try:
            data = func(self, *args, **kwargs)
            if data.status_code == 200:
                return {'code': 0, 'data': data, 'status': data.status_code, 'message': 'OK'}

            else:
                return {'code': 1, 'data': None, 'status': data.status_code, 'message': 'OK'}

        except ConnectTimeout or ReadTimeout as e:
            # self.logging.error("Downloader" + " | " + "request timeout: {}s".format(kwargs['timeout']) + " | "
            #                         + kwargs['url'])
            return {'code': 2, 'data': None, 'status': None, 'message': e}

        except ConnectionError as e:
            # self.logging.error("Downloader" + " | " + "connection error" + " | " + kwargs['url'] + " | " + str(e))
            return {'code': 2, 'data': None, 'status': None, 'message': e}

        except Exception as e:
            # self.logging.error("Downloader" + " | " + "unknown error" + " | " + kwargs['url'] + " | " + str(e))
            return {'code': 2, 'data': None, 'status': None, 'message': e}

    return wrapper


class BaseDownloaderMiddleware(object):
    def __init__(self, logging, timeout):
        self.logging = logging
        self.downloader = Downloader(logging=logging, timeout=timeout)

    def _startDownload(self, param):
        try:
            url = param['url']
        except:
            url = None
        try:
            mode = param['mode'].upper()
        except:
            mode = None
        try:
            headers = param['headers']
        except:
            headers = None
        try:
            data = param['data']
        except:
            data = None
        try:
            cookies = param['cookies']
        except:
            cookies = None
        try:
            proxies = param['proxies']
        except:
            proxies = None

        if not url:
            raise Exception("Please specify URL")

        if not mode:
            raise Exception('Please specify request for GET or POST')

        if mode == 'GET':
            resp = self.downloader.begin(url=url, connect_type='GET', headers=headers, proxies=proxies, cookies=cookies)
            return resp

        if mode == 'POST':
            resp = self.downloader.begin(url=url, connect_type='POST', headers=headers, proxies=proxies, data=data, cookies=cookies)
            return resp


class Downloader(object):
    def __init__(self, logging, timeout):
        self.logging = logging
        self.timeout = timeout

    @_error
    def get(self, url, headers, cookies, timeout, proxies):
        # requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
        # s = requests.session()
        # s.keep_alive = False  # 关闭多余连接
        # start_time = float(time.time())
        r =requests.get(url=url, headers=headers, proxies=proxies, timeout=timeout, cookies=cookies)
        # end_time = float(time.time())
        # print(round(end_time - start_time, 4))
        # print(r.elapsed.total_seconds())
        return r

    @_error
    def post(self, url, headers, data, cookies, timeout, proxies):
        r = requests.post(url=url, headers=headers, data=data, proxies=proxies, timeout=timeout, cookies=cookies)
        return r

    def start(self, url, headers, data, cookies, timeout, proxies, connect_type):
        # time.sleep(int(DOWNLOAD_DELAY))
        time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

        if connect_type == 'GET':
            return self.get(url=url, headers=headers, cookies=cookies,
                                 timeout=timeout, proxies=proxies)

        if connect_type == 'POST':
            return self.post(url=url, headers=headers, data=data,
                                  cookies=cookies, timeout=timeout, proxies=proxies)

    def begin(self, url, headers=None, data=None, proxies=None, cookies=None, connect_type='GET'):
        start_time = int(time.time())
        down_data = self.start(url=url, headers=headers, data=data,
                               cookies=cookies, timeout=self.timeout, proxies=proxies,
                               connect_type=connect_type.upper())
        # print(headers)

        end_time = int(time.time())

        # try:
        #     code = down_data['code']
        # except:
        #     code = None

        self.logging.info("request for url: {} | code: {} | status: {} | message: {} | mode: {} | data: {} | proxy: {} | use time: {}".format(
            url, down_data['code'], down_data['status'], down_data['message'], connect_type, data, proxies, '{}s'.format(end_time - start_time)
        ))

        return down_data

