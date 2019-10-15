import sys
sys.path.append('.')
import proxy


def init():
    ret = proxy.proxy('https://www.baidu.com')
    if (ret.status_code == 200):
        print(ret.text)


if __name__ == '__main__':
    init()
