# -*-coding:utf-8-*-

'''

'''
import sys
import os
import json
import hashlib
import ast
import requests

sys.path.append(os.path.dirname(__file__) + os.sep + "../../../")

import settings
from Utils import timeutils
from Storage import storage
from Project.ZhiWangLunWen import config


class QiKanLunWen_QiKanTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(QiKanLunWen_QiKanTaskDao, self).__init__(logging=logging,
                                                       mysqlpool_number=mysqlpool_number,
                                                       redispool_number=redispool_number)

    def saveData(self, sha, memo):
        new_memo = memo
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_QIKAN, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        print(data_status)
        if data_status:
            old_memo = json.loads(data_status['memo'])
            # old_memo = ast.literal_eval(data_status['memo'])
            print(old_memo)
            old_column_name = old_memo['column_name']
            new_column_name = new_memo['column_name']
            if new_column_name not in old_column_name:
                new_memo['column_name'] = old_column_name + '|' + new_column_name
                # 存储数据
                data = {
                    'sha': sha,
                    'memo': str(new_memo).replace('\'', '"'),
                    'type': config.QIKANLUNWEN_QIKAN_MAIN,
                    'create_at': timeutils.getNowDatetime(),
                }
                self.mysql_client.update(table=config.MYSQL_QIKAN, data=data, where="`sha` = '{}'".format(sha))

        else:
            data = {
                'sha': sha,
                'memo': str(new_memo).replace('\'', '"'),
                'type': config.QIKANLUNWEN_QIKAN_MAIN,
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_QIKAN, data=data)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))


class HuiYiLunWen_QiKanTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(HuiYiLunWen_QiKanTaskDao, self).__init__(logging=logging,
                                                       mysqlpool_number=mysqlpool_number,
                                                       redispool_number=redispool_number)

    def saveLunWenJiUrl(self, url_data):
        sha = hashlib.sha1(url_data['url'].encode('utf-8')).hexdigest()
        url = url_data['url']
        jibie = url_data['jibie']
        memo = {
            'sha': sha,
            'url': url,
            'jibie': jibie
        }
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_QIKAN, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': config.HUIYILUNWEN_QIKAN_MAIN,
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_QIKAN, data=data)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class XueWeiLunWen_QiKanTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(XueWeiLunWen_QiKanTaskDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def saveDanWeiUrl(self, danwei_url):
        sha = hashlib.sha1(danwei_url.encode('utf-8')).hexdigest()
        memo = {
            'sha': sha,
            'url': danwei_url
        }
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_QIKAN, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': config.XUEWEILUNWEN_QIKAN_MAIN,
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_QIKAN, data=data)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class HuiYiLunWen_LunWenTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(HuiYiLunWen_LunWenTaskDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def get_task_from_redis(self):
        sql = "select * from {} where `type` = '{}' and `del` = '{}'".format(config.MYSQL_QIKAN,
                                                                             config.HUIYILUNWEN_QIKAN_MAIN, 0)
        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def saveHuiYiUrlData(self, memo, sha):
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_LUNWEN, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': config.HUIYILUNWEN_LUNWEN_MAIN,
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_LUNWEN, data=data)
                self.logging.info(sha)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class QiKanLunWen_LunWenTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(QiKanLunWen_LunWenTaskDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def get_task_from_redis(self):
        sql = "select * from {} where `type` = '{}' and `del` = '{}'".format(config.MYSQL_QIKAN,
                                                                             config.QIKANLUNWEN_QIKAN_MAIN, 0)
        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def saveProjectUrlToMysql(self, memo):
        url = memo['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_LUNWEN, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': config.QIKANLUNWEN_LUNWEN_MAIN,
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_LUNWEN, data=data)
                self.logging.info(sha)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class XueWeiLunWen_LunWenTaskDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(XueWeiLunWen_LunWenTaskDao, self).__init__(logging=logging,
                                                         mysqlpool_number=mysqlpool_number,
                                                         redispool_number=redispool_number)

    # def getTask(self):
    #     sql = "select * from {} where `type` = '{}' and `del` = '{}'".format(config.MYSQL_QIKAN,
    #                                                                          config.XUEWEILUNWEN_QIKAN_MAIN, 0)
    #     data_list = self.mysql_client.get_results(sql=sql)
    #
    #     return data_list

    def saveLunWenUrlData(self, memo):
        url = memo['url']
        sha = hashlib.sha1(url.encode('utf-8')).hexdigest()
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_LUNWEN, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': config.XUEWEILUNWEN_LUNWEN_MAIN,
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_LUNWEN, data=data)
                self.logging.info(sha)
            except Exception as e:
                self.logging.warning('数据存储警告: {}'.format(e))

        else:
            self.logging.warning('数据已存在: {}'.format(sha))


class QiKanLunWen_LunWenDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(QiKanLunWen_LunWenDataDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def getLunWenUrls(self):
        datas = self.redis_client.queue_spops(key=config.REDIS_QIKANLUNWEN_LUNWEN, count=100,
                                              lockname=config.REDIS_QIKANLUNWEN_LUNWEN_LOCK)

        return datas

    # 从mysql获取任务
    def get_task_list_from_mysql(self, table, where, count):
        sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(table, where, count)

        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def deleteUrl(self, sha):
        sql = "delete from {} where `sha` = '{}'".format(config.MYSQL_LUNWEN, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('论文任务已删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务删除异常: {}'.format(sha))

    def deleteLunWenUrl(self, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=config.MYSQL_LUNWEN, data=data, where="sha = '{}'".format(sha))
            self.logging.info('论文任务已逻辑删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务逻辑删除异常: {}'.format(sha))

    def saveRenWuToMysql(self, memo_list):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_ZUOZHE, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': timeutils.getNowDatetime(),
                }
                try:
                    self.mysql_client.insert_one(table=config.MYSQL_ZUOZHE, data=data)
                    self.logging.info('已保存人物队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('人物队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('人物队列数据已存在: {}'.format(sha))

    def saveJiGouToMysql(self, memo_list):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_JIGOU, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': timeutils.getNowDatetime(),
                }
                try:
                    self.mysql_client.insert_one(table=config.MYSQL_JIGOU, data=data)
                    self.logging.info('已保存机构队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('机构队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('机构队列数据已存在: {}'.format(sha))


class HuiYiLunWen_LunWenDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(HuiYiLunWen_LunWenDataDao, self).__init__(logging=logging,
                                                        mysqlpool_number=mysqlpool_number,
                                                        redispool_number=redispool_number)

    def getLunWenUrls(self):
        datas = self.redis_client.queue_spops(key=config.REDIS_HUIYILUNWEN_LUNWEN, count=100,
                                              lockname=config.REDIS_HUIYILUNWEN_LUNWEN_LOCK)

        return datas

    # 从mysql获取任务
    def get_task_list_from_mysql(self, table, where, count):
        sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(table, where, count)

        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def deleteUrl(self, sha):
        sql = "delete from {} where `sha` = '{}'".format(config.MYSQL_LUNWEN, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('论文任务已删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务删除异常: {}'.format(sha))

    def deleteLunWenUrl(self, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=config.MYSQL_LUNWEN, data=data, where="sha = '{}'".format(sha))
            self.logging.info('论文任务已逻辑删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务逻辑删除异常: {}'.format(sha))

    def saveRenWuToMysql(self, memo_list):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_ZUOZHE, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': timeutils.getNowDatetime(),
                }
                try:
                    self.mysql_client.insert_one(table=config.MYSQL_ZUOZHE, data=data)
                    self.logging.info('已保存人物队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('人物队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('人物队列数据已存在: {}'.format(sha))

    def saveJiGouToMysql(self, memo_list):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_JIGOU, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': timeutils.getNowDatetime(),
                }
                try:
                    self.mysql_client.insert_one(table=config.MYSQL_JIGOU, data=data)
                    self.logging.info('已保存机构队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('机构队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('机构队列数据已存在: {}'.format(sha))


class XueWeiLunWen_LunWenDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(XueWeiLunWen_LunWenDataDao, self).__init__(logging=logging,
                                                         mysqlpool_number=mysqlpool_number,
                                                         redispool_number=redispool_number)

    def getLunWenUrls(self):
        datas = self.redis_client.queue_spops(key=config.REDIS_XUEWEILUNWEN_LUNWEN, count=100,
                                              lockname=config.REDIS_XUEWEILUNWEN_LUNWEN_LOCK)

        return datas

    # 从mysql获取任务
    def get_task_list_from_mysql(self, table, where, count):
        sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(table, where, count)

        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    def saveRenWuToMysql(self, memo_list):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_ZUOZHE, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': timeutils.getNowDatetime(),
                }
                try:
                    self.mysql_client.insert_one(table=config.MYSQL_ZUOZHE, data=data)
                    self.logging.info('已保存人物队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('人物队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('人物队列数据已存在: {}'.format(sha))

    def saveJiGouToMysql(self, memo_list):
        for memo in memo_list:
            sha = memo['sha']
            # 查询数据库是否含有此数据
            data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_JIGOU, sha)
            data_status = self.mysql_client.get_result(sql=data_status_sql)
            if not data_status:
                data = {
                    'sha': sha,
                    'memo': str(memo).replace('\'', '"'),
                    'type': '中国知网',
                    'create_at': timeutils.getNowDatetime(),
                }
                try:
                    self.mysql_client.insert_one(table=config.MYSQL_JIGOU, data=data)
                    self.logging.info('已保存机构队列, 主键sha: {}'.format(sha))
                except Exception as e:
                    self.logging.warning('机构队列数据存储警告: {}'.format(e))

            else:
                self.logging.warning('机构队列数据已存在: {}'.format(sha))

    def deleteUrl(self, sha):
        sql = "delete from {} where `sha` = '{}'".format(config.MYSQL_LUNWEN, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('论文任务已删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务删除异常: {}'.format(sha))

    def deleteLunWenUrl(self, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=config.MYSQL_LUNWEN, data=data, where="sha = '{}'".format(sha))
            self.logging.info('论文任务已逻辑删除: {}'.format(sha))
        except:
            self.logging.warning('论文任务逻辑删除异常: {}'.format(sha))


class ZhiWangLunWen_JiGouDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(ZhiWangLunWen_JiGouDataDao, self).__init__(logging=logging,
                                                         mysqlpool_number=mysqlpool_number,
                                                         redispool_number=redispool_number)

    # def getJiGouUrls(self):
    #     datas = self.redis_client.queue_spops(key=config.REDIS_JIGOU, count=100,
    #                                           lockname=config.REDIS_JIGOU_LOCK)
    #
    #     return datas

    # 物理删除任务
    def deleteUrl(self, sha):
        sql = "delete from {} where `sha` = '{}'".format(config.MYSQL_JIGOU, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('机构任务已删除: {}'.format(sha))
        except:
            self.logging.warning('机构任务删除异常: {}'.format(sha))

    # 逻辑删除任务
    def deleteJiGouUrl(self, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=config.MYSQL_JIGOU, data=data, where="`sha` = '{}'".format(sha))
            self.logging.info('机构任务加载失败，已更改状态: {}'.format(sha))
        except:
            self.logging.warning('机构任务更改状态异常: {}'.format(sha))


class ZhiWangLunWen_ZuoZheDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(ZhiWangLunWen_ZuoZheDataDao, self).__init__(logging=logging,
                                                          mysqlpool_number=mysqlpool_number,
                                                          redispool_number=redispool_number)


    # def getZuoZheUrls(self):
    #     datas = self.redis_client.queue_spops(key=config.REDIS_ZUOZHE, count=100,
    #                                           lockname=config.REDIS_ZUOZHE_LOCK)
    #
    #     return datas

    # 查询redis数据库中有多少任务
    def select_task_number(self, key):
        return self.redis_client.scard(key=key)

    # 从Mysql获取任务
    def get_task_list_from_mysql(self, table, count):
        sql = "select * from {} where `del` = '0' limit {}".format(table, count)

        data_list = self.mysql_client.get_results(sql=sql)

        # 进入redis队列的数据，在mysql数据库中改变`del`字段值为'1'，表示正在执行
        # for data in data_list:
        #     sha = data['sha']
        #     set = {'del': '1'}
        #     self.mysql_client.update(table, data=set, where="`sha` = '{}'".format(sha))

        return data_list

    # 队列任务
    def queue_tasks_from_mysql_to_redis(self, key, data):
        if data:
            for url_data in data:
                url = url_data['memo']
                self.redis_client.sadd(key=key, value=url)

        else:
            return

    # 物理删除任务
    def deleteUrl(self, sha):
        sql = "delete from {} where `sha` = '{}'".format(config.MYSQL_ZUOZHE, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('作者任务已删除: {}'.format(sha))
        except:
            self.logging.warning('作者任务删除异常: {}'.format(sha))

    # 逻辑删除任务
    def deleteZuoZheUrl(self, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=config.MYSQL_ZUOZHE, data=data, where="`sha` = '{}'".format(sha))
            self.logging.info('作者任务因网页无数据或加载失败，已更改状态: {}'.format(sha))
        except:
            self.logging.warning('作者任务更改状态异常: {}'.format(sha))

    def saveJiGouToMysql(self, memo):
        sha = memo['sha']
        # 查询数据库是否含有此数据
        data_status_sql = "select * from {} where `sha` = '{}'".format(config.MYSQL_JIGOU, sha)
        data_status = self.mysql_client.get_result(sql=data_status_sql)
        if not data_status:
            data = {
                'sha': sha,
                'memo': str(memo).replace('\'', '"'),
                'type': '中国知网',
                'create_at': timeutils.getNowDatetime(),
            }
            try:
                self.mysql_client.insert_one(table=config.MYSQL_JIGOU, data=data)
                self.logging.info('已保存机构种子, 主键sha: {}'.format(sha))
            except Exception as e:
                self.logging.warning('机构种子存储警告: {}'.format(e))

        else:
            self.logging.warning('机构种子已存在: {}'.format(sha))


class ZhiWangLunWen_HuiYiDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(ZhiWangLunWen_HuiYiDataDao, self).__init__(logging=logging,
                                                         mysqlpool_number=mysqlpool_number,
                                                         redispool_number=redispool_number)

    # def getWenJiUrls(self):
    #     sql = "select * from {} where `type` = '{}'".format(config.MYSQL_QIKAN, config.HUIYILUNWEN_QIKAN_MAIN)
    #     datas = self.mysql_client.get_results(sql=sql)
    #
    #     return datas

    # 查询redis数据库中有多少任务
    def select_task_number(self, key):
        return self.redis_client.scard(key=key)

    # 从Mysql获取任务
    def get_task_list_from_mysql(self, table, where, count):
        sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(table, where, count)

        datas = self.mysql_client.get_results(sql=sql)

        # 进入redis队列的数据，在mysql数据库中改变`del`字段值为'1'，表示正在执行
        for data in datas:
            whe = data['sha']
            set = {'del':'1'}
            self.mysql_client.update(table, data=set, where='sha', value=whe)

        return datas

    # 队列任务
    def queue_tasks_from_mysql_to_redis(self, key, data):
        if data:
            for url_data in data:
                url = url_data['memo']
                self.redis_client.sadd(key=key, value=url)

        else:
            return


class ZhiWangLunWen_QiKanDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(ZhiWangLunWen_QiKanDataDao, self).__init__(logging=logging,
                                                         mysqlpool_number=mysqlpool_number,
                                                         redispool_number=redispool_number)

    def getQiKanUrls(self):
        sql = "select * from {} where `type` = '{}'".format(config.MYSQL_QIKAN, config.QIKANLUNWEN_QIKAN_MAIN)
        datas = self.mysql_client.get_results(sql=sql)

        return datas

    # 从Mysql获取任务
    def get_task_list_from_mysql(self, table, where, count):
        sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(table, where, count)

        data_list = self.mysql_client.get_results(sql=sql)

        return data_list

    # 物理删除任务
    def deleteUrl(self, sha):
        sql = "delete from {} where `sha` = '{}'".format(config.MYSQL_QIKAN, sha)
        try:
            self.mysql_client.execute(sql=sql)
            self.logging.info('期刊任务已删除: {}'.format(sha))
        except:
            self.logging.warning('期刊任务删除异常: {}'.format(sha))

    # 逻辑删除任务
    def deleteQiKanUrl(self, sha):
        data = {
            'del': '1'
        }
        try:
            self.mysql_client.update(table=config.MYSQL_QIKAN, data=data, where="`sha` = '{}'".format(sha))
            self.logging.info('期刊任务已逻辑删除: {}'.format(sha))
        except:
            self.logging.warning('期刊任务逻辑删除异常: {}'.format(sha))

class ZhiWangLunWen_WenJiDataDao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(ZhiWangLunWen_WenJiDataDao, self).__init__(logging=logging,
                                                         mysqlpool_number=mysqlpool_number,
                                                         redispool_number=redispool_number)

    # def getWenJiUrls(self):
    #     sql = "select * from {} where `type` = '{}'".format(config.MYSQL_QIKAN, config.HUIYILUNWEN_QIKAN_MAIN)
    #     datas = self.mysql_client.get_results(sql=sql)
    #
    #     return datas

    # 从Mysql获取任务
    def get_task_list_from_mysql(self, table, where, count):
        sql = "select * from {} where `type` = '{}' and `del` = '0' limit {}".format(table, where, count)

        data_list = self.mysql_client.get_results(sql=sql)

        return data_list


class Dao(storage.Dao):
    def __init__(self, logging, mysqlpool_number=0, redispool_number=0):
        super(Dao, self).__init__(logging=logging,
                                  mysqlpool_number=mysqlpool_number,
                                  redispool_number=redispool_number)
