import requests
from pyquery import PyQuery as pq
import pymysql
import threading
import time

# Config
MYSQL = {
    'host': 'localhost',
    'username': 'root',
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


# 获取代理
def getProxy(protocal, link, page=1):
    try:
        url = f'https://www.xicidaili.com/{link}/{page}'
        res = requests.get(url, headers={'User-Agent': UA['PC']})
        if (res and res.status_code == 200):
            html = pq(res.text)('#ip_list tr')

            # 线程回调
            def threadCallBack(i):
                tds = pq(html[int(i)]).find('td')
                if (tds.length > 2):
                    host = pq(tds[1]).text()
                    port = pq(tds[2]).text()
                    if (host and port):
                        try:
                            # 建立连接
                            mysql = connect()
                            if not mysql:
                                return
                            # 检查代理是否有效
                            power = checkProxy(f'https://{host}:{port}')
                            # 检查proxy 是否存在，否则插入DB
                            mysql['cursor'].execute(
                                f'select count(*) from proxy where host = "{host}" and port = "{port}"',
                            )
                            has_proxy = mysql['cursor'].fetchone()[0]
                            # 如果代理有效 && DB 无数据
                            if power and not has_proxy:
                                mysql['cursor'].execute(
                                    f'insert into proxy(host,port,protocal) values("{host}","{port}","{protocal}")'
                                )
                                mysql['db'].commit()
                            # 如果代理无效 && DB 有数据
                            if not power and has_proxy:
                                mysql['cursor'].execute(
                                    f'delete from proxy where host = "{host}" and port = "{port}"'
                                )
                                mysql['db'].commit()
                            # 关闭mysql
                            mysql['db'].close()
                        except Exception as e1:
                            print('---e1---', e1)

            threadList = []
            for i in range(html.length):
                if (i > 0):
                    t = threading.Thread(
                        target=threadCallBack,
                        args=(f'{i}', ),
                    )
                    t.start()
                    threadList.append(t)
            for t in threadList:
                t.join()
    except Exception as e:
        print('---e---', e)


# 检查代理是否有效
def checkProxy(proxylink):
    try:
        ret = requests.get(
            'https://www.baidu.com',
            proxies={'https': proxylink},
            timeout=5,
        )
        if (ret and ret.status_code == 200):
            print(proxylink)
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


def init():
    types = {'https': 'wn', 'http': 'wt'}
    for protocal in types:
        for i in range(30):
            print('---page----', i + 1)
            getProxy(protocal, types[protocal], i + 1)


init()
