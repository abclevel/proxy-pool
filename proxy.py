import requests
from pyquery import PyQuery as pq
import pymysql
import threading
import time
import random

# Config
MYSQL = {
    'host': 'localhost',
    'username': 'admin',
    'password': 'password',
    'dbname': 'ml',
}

# UA
UA = {
    'MOBILE':
    'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Mobile Safari/537.36',
    'PC':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
}


# 检查代理是否有效
def checkProxy(proxylink):
    try:
        ret = requests.get(
            'https://www.baidu.com',
            proxies={'https': proxylink},
            timeout=5,
        )
        if (ret and ret.status_code == 200):
            return True
    except Exception as e:
        pass


# 链接数据库
def connect():
    try:
        db = pymysql.connect(
            MYSQL['host'],
            MYSQL['username'],
            MYSQL['password'],
            MYSQL['dbname'],
        )
        cursor = db.cursor()
        return {'db': db, 'cursor': cursor}
    except Exception as e:
        print('connect error:', e)


# 删除无效proxy
def deleteProxy(id):
    try:
        mysql = connect()
        if not mysql:
            print('mysql 链接失败')
        mysql['cursor'].execute(
            f'select count(*) from proxy where id = "{id}"')
        has = mysql['cursor'].fetchone()[0]
        if has:
            mysql['cursor'].execute(f'delete from proxy where id = "{id}"')
            mysql['db'].commit()
    except Exception as e:
        pass


# 获取随机proxy
def randomproxy():
    try:
        mysql = connect()
        if not mysql:
            print('mysql 链接失败')
            return
        mysql['cursor'].execute(f'select count(*) from proxy')
        proxycount = mysql['cursor'].fetchone()[0]
        if proxycount < 50:
            print('代理数小于50，请尽快爬取')
        if proxycount:
            mysql['cursor'].execute(
                f'select id,host,port,protocal from proxy limit 1 offset {random.randint(0,proxycount-1)} '
            )
            proxyrow = mysql['cursor'].fetchone()
            if proxyrow:
                return {
                    'id': proxyrow[0],
                    'link': f'{proxyrow[3]}://{proxyrow[1]}:{proxyrow[2]}'
                }
    except Exception as e:
        print(e)


# 代理方法
def proxy(url, method='get', params={}, headers={}, count=1):
    try:
        proxylink = randomproxy()
        if not proxylink:
            return
        proxies = {
            'https': proxylink['link'],
            'http': proxylink['link'],
        }
        if method == 'get':
            ret = requests.get(url, headers=headers, proxies=proxies)
            return ret
        else:
            ret = requests.post(
                url,
                data=params,
                headers=headers,
                proxies=proxies,
            )
            return ret
    except Exception as e:
        if count < 6:
            print('proxy error', proxylink['id'])
            deleteProxy(proxylink['id'])
            return proxy(url, method, params, headers, count + 1)
        print('proxy error 2:', e)


# 线程回调
def threadCallback(protocal, host, port):
    def cb():
        try:
            # 建立连接
            mysql = connect()
            if not mysql:
                return
            # 检查代理是否有效
            power = checkProxy(f'{protocal}://{host}:{port}')
            # 检查proxy 是否存在，否则插入DB
            mysql['cursor'].execute(
                f'select count(*) from proxy where host = "{host}" and port = "{port}"',
            )
            has_proxy = mysql['cursor'].fetchone()[0]
            # 如果代理有效 && DB 无数据
            if power and not has_proxy:
                print(f'insert:{host}:{port}')
                mysql['cursor'].execute(
                    f'insert into proxy(host,port,protocal) values("{host}","{port}","{protocal}")'
                )
                mysql['db'].commit()
            # 如果代理无效 && DB 有数据
            if not power and has_proxy:
                print(f'delete:{host}:{port}')
                mysql['cursor'].execute(
                    f'delete from proxy where host = "{host}" and port = "{port}"'
                )
                mysql['db'].commit()
            # 关闭mysql
            mysql['db'].close()
        except Exception as e1:
            print('---e1---', e1)

    t = threading.Thread(target=cb)
    t.start()
    return t


# 西刺客代理
def xiciProxy(protocal, link, page=1):
    try:
        url = f'https://www.xicidaili.com/{link}/{page}'
        res = requests.get(
            url,
            headers={'User-Agent': UA['PC']},
        )
        if (res and res.status_code == 200):
            html = pq(res.text)('#ip_list tr')
            threadList = []
            for i in range(html.length):
                if (i > 0):
                    tds = pq(html[int(i)]).find('td')
                    if (tds.length > 2):
                        host = pq(tds[1]).text()
                        port = pq(tds[2]).text()
                        if (host and port):
                            t = threadCallback(protocal, host, port)
                            threadList.append(t)
            for t in threadList:
                t.join()
        if res and res.status_code != 200:
            print('xici----', res.status_code)
    except Exception as e:
        print('---e---', e)


# 快代理
def kuaiProxy(link='inha', page=1):
    try:
        url = f'https://www.kuaidaili.com/free/{link}/{page}/'
        res = requests.get(url, headers={'User-Agent': UA['PC']})
        if res and res.status_code == 200:
            html = pq(res.text)('#list tr')
            if html.length:
                threadList = []
                for i in range(html.length):
                    if i > 0:
                        tds = pq(html[int(i)]).find('td')
                        if (tds.length > 2):
                            host = pq(tds[0]).text()
                            port = pq(tds[1]).text()
                            protocal = pq(tds[3]).text().lower()
                            if (host and port and protocal):
                                t = threadCallback(protocal, host, port)
                                threadList.append(t)
                for t in threadList:
                    t.join()
        if res and res.status_code != 200:
            print('kuai---', res.status_code)
    except Exception as e:
        print('kuai proxy:', e)


def init():
    # kuaiProxy()
    # return
    def xici():
        types = {'https': 'wn', 'http': 'wt'}
        for i in range(30):
            for protocal in types:
                print('---page----', i + 1)
                time.sleep(2)
                xiciProxy(protocal, types[protocal], i + 1)

    def kuai():
        links = {'link1': 'inha', 'link2': 'intr'}
        for i in range(30):
            for link in links:
                print('---page----', i + 1)
                time.sleep(2)
                kuaiProxy(link, i + 1)

    cbs = [xici, kuai]
    # threadList = []
    for cb in cbs:
        cb()
    # for cb in cbs:
    #     t = threading.Thread(target=cb)
    #     t.start()
    #     threadList.append(t)
    # for i in threadList:
    #     i.join()


if __name__ == '__main__':
    init()
