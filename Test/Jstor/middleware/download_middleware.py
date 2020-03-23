# -*-coding:utf-8-*-

'''

'''
import sys
import os
import time
import requests
import random

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")
from Downloader import downloader_mod
from Utils import user_agent_u
from Utils import proxy
from settings import DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY


class Downloader(downloader_mod.BaseDownloaderMiddleware):
    def __init__(self, logging, timeout, proxy_type, proxy_country, proxy_city):
        super(Downloader, self).__init__(logging=logging, timeout=timeout)
        self.proxy_type = proxy_type
        self.proxy_obj = proxy.ProxyUtils(logging=logging, type=proxy_type, country=proxy_country, city=proxy_city)

    def get_headers(self):
        headers_list = [
            {
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Sec-Fetch-Mode': 'navigate',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Scheme': 'https',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Scheme': 'https',
                'Cache-Control': 'max-age=0',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Scheme': 'https',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Scheme': 'https',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Cache-Control': 'max-age=0',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Upgrade-Insecure-Requests': '1',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            },
            {
                'Authority': 'www.jstor.org',
                'Cache-Control': 'max-age=0',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
                'Connection': 'close',
                'User-Agent': user_agent_u.get_ua()
            }
        ]

        headers = random.choice(headers_list)
        return headers

    def getResp(self, url, mode, s=None, data=None, cookies=None, referer=None):
        # 请求异常时间戳
        err_time = 0
        # 响应状态码错误时间戳
        stat_time = 0
        while 1:
            # 下载延时
            time.sleep(random.uniform(DOWNLOAD_MIN_DELAY, DOWNLOAD_MAX_DELAY))

            # 设置参数
            param = {'url': url}
            # 设置请求方式：GET或POST
            param['mode'] = mode
            # 设置请求头
            param['headers'] = {
                # 'authority': 'www.jstor.org',
                'method': 'GET',
                'scheme': 'https',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                # 'accept-language': 'zh-CN,zh;q=0.9',
                # 'accept-encoding': 'gzip, deflate, br',
                # 'sec-fetch-mode': 'navigate',
                'referer': referer,
                'connection': 'close',
                'user-agent': user_agent_u.get_ua()
            }
            # 设置post参数
            param['data'] = data
            # 设置cookies
            param['cookies'] = cookies
            # 设置proxy
            if self.proxy_type:
                param['proxies'] = self.proxy_obj.getProxy()

            down_data = self._startDownload(param=param, s=s)

            if down_data['code'] == 0:
                return {'code': 0, 'data': down_data['data']}

            if down_data['code'] == 1:
                status_code = str(down_data['status'])
                if status_code != '404':
                    if stat_time == 0:
                        # 获取错误状态吗时间戳
                        stat_time = int(time.time())
                        continue
                    else:
                        # 获取当前时间戳
                        now_time = int(time.time())
                        if now_time - stat_time >= 120:
                            return {'code': 1, 'data': url}
                        else:
                            continue
                else:
                    return {'code': 1, 'data': url}

            if down_data['code'] == 2:
                '''
                如果未设置请求异常的时间戳，则现在设置；
                如果已经设置了异常的时间戳，则获取当前时间戳，然后对比之前设置的时间戳，如果时间超过了3分钟，说明url有问题，直接返回
                {'code': 1}
                '''
                if err_time == 0:
                    err_time = int(time.time())
                    continue

                else:
                    # 获取当前时间戳
                    now = int(time.time())
                    if now - err_time >= 120:
                        return {'code': 1, 'data': url}
                    else:
                        continue

    # 创建COOKIE
    def create_cookie(self):
        url = 'https://www.jstor.org/'
        try:
            resp = self.getResp(url=url, mode='GET')
            if resp['code'] == 0:
                # print(resp.cookies)
                self.logging.info('cookie创建成功')
                return requests.utils.dict_from_cookiejar(resp['data'].cookies)

        except:
            self.logging.error('cookie创建异常')
            return None

