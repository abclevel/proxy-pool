## 目的

爬虫过程中，遭遇站点反爬虫策略，需要定期切换 IP。所以我构建一个有效的 IP 池，用于之后的爬虫工作

## 做法

爬取[西刺免费代理 IP 网](https://www.xicidaili.com/)，筛选有效的代理 IP 入库

## 依赖

-   [requests](https://github.com/psf/requests): HTTP 请求

-   [pyquery](https://github.com/gawel/pyquery): Python 版的 jquery ,解析 HTML 元素

-   [PyMySQL](https://github.com/PyMySQL/PyMySQL)：mysql ，本实例存储在 mysql 中。对于数据的操作，数据库还是更加方便。

## 实现

#### 爬取网页，获取数据

```
def getProxy(protocal, link, page=1):
    try:
        url = f'https://www.xicidaili.com/{link}/{page}'
        res = requests.get(url, headers={'User-Agent': UA['PC']})
        if (res and res.status_code == 200):
            html = pq(res.text)('#ip_list tr')

            for i in range(html.length):
                host = pq(tds[1]).text()
                port = pq(tds[2]).text()

```

如上所示的代码(截取了部分),我们解析`西刺免费代理IP网`,获取目标 IP 和 端口

#### 检测 IP，端口的有效性

`西刺免费代理IP网`提供的很多 IP 不具备有效性，所以需要做出过滤才可入库

```
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
```

我们使用上面的方法，代理请求百度地址，检测代理的有效性

#### 将有效的 IP 入库，已在数据库中但是无效的 IP，移除

```
# 连接数据库
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

*****
mysql = connect()
# 检查DB 是否已存在某代理地址
mysql['cursor'].execute(
    f'select count(*) from proxy where host = "{host}" and port = "{port}"',
)
# 如果代理有效，且不存在DB中，代理入库
mysql['cursor'].execute(
    f'insert into proxy(host,port,protocal) values("{host}","{port}","{protocal}")'
)
mysql['db'].commit()
# 如果代理无效，但是又存在于DB中，删除代理
mysql['cursor'].execute(
    f'delete from proxy where host = "{host}" and port = "{port}"'
)
mysql['db'].commit()
# 关闭连接
mysql['db'].close()
```

因为需要对每个代理检测有效性，所有的检测 IP 有效性、IP 入库都基于多线程实现。每个线程独享一个 MYSQL 连接。

上面阐述的比较碎片，具体的实现可以看源码，代码包含 SQL 结构。
