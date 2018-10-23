# -*-coding:utf-8-*-
'''
redis连接池操作
'''

import redis
import sys
import os

sys.path.append(os.path.dirname(__file__) + os.sep + "../")
import settings
from utils import timeutils


REDIS_HOST=settings.REDIS_HOST
REDIS_PORT=settings.REDIS_PORT
REDIS_PASSWORD=settings.REDIS_PASSWORD


def createRedisPool():
    '''
    创建redis连接池
    :return: redis对象
    '''
    pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    redis_client = redis.StrictRedis(connection_pool=pool)

    return redis_client


def redisLock(func):
    # 锁的过期时间（秒）
    EXPIRY = 3

    def wrapper(*args, **kwargs):
        if kwargs['lockname']:
            lockname = kwargs['lockname']
        else:
            lockname = 'lock.foo'
        redis_client = kwargs['redis_client']
        while True:
            # 获取当前时间戳
            now = timeutils.get_current_millis()
            # 生成锁时间【当前时间戳 + 锁有效时间】
            lock_time_out = now + EXPIRY
            # 设置redis锁
            lock_status = redis_client.setnx(lockname, lock_time_out)
            # 如果返回1， 代表抢锁成功
            if lock_status == 1:
                data = func(*args, **kwargs)
                # 获取当前时间戳
                now = timeutils.get_current_millis()
                # 获取当前redis设置的锁时间戳
                now_redis_lock = redis_client.get(lockname)
                # 如果当前时间戳小于锁设置时间， 解锁
                if int(now) < int(now_redis_lock):
                    redis_client.delete(lockname)

                return data
            # 如果返回0， 代表抢锁失败
            if lock_status == 0:
                # 获取redis中锁的过期时间
                redis_lock_out = redis_client.get(lockname)
                # 判断这个锁是否已超时, 如果当前时间大于锁时间， 说明锁已超时
                if now > int(redis_lock_out):
                    # 生成锁时间【当前时间戳 + 锁有效时间】
                    lock_time_out = now + EXPIRY
                    # 抢锁
                    old_lock_time = redis_client.getset(lockname, lock_time_out)
                    # 判断抢锁后返回的时间是否与之前获取的锁过期时间相等， 相等说明抢锁成功
                    if int(old_lock_time) == int(redis_lock_out):
                        data = func(*args, **kwargs)
                        # 获取当前时间戳
                        now = timeutils.get_current_millis()
                        # 获取当前redis设置的锁时间戳
                        now_redis_lock = redis_client.get(lockname)
                        # 如果当前时间戳小于锁设置时间， 解锁
                        if int(now) < int(now_redis_lock):
                            redis_client.delete(lockname)

                        return data
                    else:
                        # 抢锁失败， 重新再抢
                        continue

    return wrapper

# 获取并删除一个set元素【分布式】
@redisLock
def queue_spop(**kwargs):
    '''
    获取并删除集合中的一个元素
    :param kwargs: 
    :return: 被删除的元素
    使用案例 data = spop(redis_client=redis_client, key='comlieted', lockname='spop_demo')
    注意： 必须设置lockname， 本函数基于分布式， lockname是用来设置redis锁的。不设置会出问题， 名字根据自己喜好起
    '''
    redis_client = kwargs['redis_client']
    data = redis_client.spop(kwargs['key'])
    if data:
        data = data.decode('utf-8')
        return data

    return None

# 获取并删除多个set元素【分布式】
@redisLock
def queue_spops(**kwargs):
    '''
    获取并删除集合中的多个元素
    :param kwargs: 
    :return: 被删除的集合元素
    使用案例 data = srandmember(redis_client=redis_client, key='comlieted', lockname='srandmember_demo', count=3)
    '''
    return_data = []
    redis_client = kwargs['redis_client']
    try:
        count = kwargs['count']
    except:
        count = 1
    for i in range(count):
        data = redis_client.spop(kwargs['key'])
        if data:
            data = data.decode('utf-8')
            return_data.append(data)
        else:
            continue

    return return_data

def lrange(redis_client, key, start, end):
    '''
    获取列表类型内容
    :redis_client: 来自redis链接池的client
    :param key: 列表名
    :param start: 开始索引
    :param end: 结束索引
    :return: 查询出的列表
    '''
    return_data = []
    datas = redis_client.lrange(key, start, end)
    for data in datas:
        data = data.decode('utf-8')
        return_data.append(data)
    return return_data

def lpush(redis_client, key, value):
    '''
    保存单个数据到列表类型
    :param key: 列表名
    :param value: 值
    '''
    len_list = redis_client.lpush(key, value)

    return len_list # 列表中的元素数量

def scard(redis_client, key):
    '''
    获取redis集合内元素数量
    :param key: 集合名
    :return: 元素数量
    '''
    proxy_number = redis_client.scard(key)

    return proxy_number

def sadd(redis_client, key, value):
    '''
    保存单个数据到集合
    :param key: 集合名
    :param value: 元素
    :return: 元素数量
    '''
    ok_number = redis_client.sadd(key, value)

    return ok_number  # 插入成功数量

def srandmember(redis_client, key, num):
    '''
    从集合中随机获取num个元素
    :param key: 集合名
    :param num: 获取数量
    :return: 元素列表
    '''
    data = redis_client.srandmember(key, num)
    data_list = []
    for proxy_b in data:
        proxy = proxy_b.decode('utf8')
        data_list.append(proxy)

    return data_list

def srem(redis_client, key, value):
    '''
    删除redis集合内的value元素
    :param key: 集合名
    :param value: 元素
    '''
    redis_client.srem(key, value)

def sismember(redis_client, key, value):
    '''
    判断数据是否存在集合中
    :param key:
    :param value:
    :return: True | False
    '''

    return redis_client.sismember(key, value)

def smembers(redis_client, key):
    '''
    查询集合内所有元素
    :param key: 键
    :return: 值
    '''
    return_data = []
    datas = redis_client.smembers(key)
    for data in datas:
        data = data.decode('utf-8')
        return_data.append(data)

    return return_data
