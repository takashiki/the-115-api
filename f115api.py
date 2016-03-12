#!/usr/bin/env python
# coding=utf-8
import requests,ssl,json,time,os
import threading
import sys
from pyquery import PyQuery as pq
QRImagePath = os.path.join(os.getcwd(), 'qrcode.jpg')

def getInfos():
    global uid,uidTime,sign,session_id
    url = 'http://passport.115.com'
    params = {
        'ct': 'login',
        'ac': 'qrcode_token',
        'is_ssl': '1',
    }

    r= mySession.get(url=url, params=params)
    r.encoding = 'utf-8'
    data = r.text
    try:
        uid = json.loads(data)['uid']
        uidTime = json.loads(data)['time']
        sign = json.loads(data)['sign']
    except Exception, e:
        return False
    url = 'http://msg.115.com/proapi/anonymous.php'
    params = {
        'ac':'signin',
        'user_id':uid,
        'sign':sign,
        'time':uidTime,
        '_': str(int(time.time()*1000)),
    }
    r = mySession.get(url=url, params=params)
    session_id = json.loads(r.text)['session_id']
    return True




def getQrcode():
    global QrcodeUrl
    url = 'http://qrcode.115.com/api/qrcode.php'
    params = {
        'qrfrom':'1',
        'uid':uid,
        '_'+str(uidTime):'',
        '_t':str(int(time.time()*1000)),
    }

    r = mySession.get(url=url, params=params)
    QrcodeUrl = r.url
    r.encoding = 'utf-8'
    f = open(QRImagePath, 'wb')
    f.write(r.content)
    f.close()
    print(u"使用115手机客户端扫码登录")
    time.sleep(1) 


def getUserinfo():
    global userid
    url = 'http://passport.115.com/'
    params = {
        'ct':'ajax',
        'ac':'islogin',
        'is_ssl':'1',
        '_'+str(int(time.time()*1000)):'',
    }
    uinfos = json.loads(mySession.get(url=url, params=params).text)
    userid = uinfos['data']['USER_ID']
    
    print("====================")
    print(u"用户ID："+userid)
    print(u"用户名："+uinfos['data']['USER_NAME'])
    if uinfos['data']['IS_VIP'] == 1:
        print(u"会员")
        url = 'http://115.com/web/lixian/?ct=lixian&ac=task_lists'
        data = {
            'page':'1',
            'uid':userid,
            'sign': tsign,
            'time': ttime,
        }
        quota = json.loads(mySession.post(url=url, data=data).text)['quota']
        total = json.loads(mySession.post(url=url, data=data).text)['total']
        print(u"本月离线配额："+str(quota)+u"个，总共"+str(total)+u"个。")  
    else:
        print(u"非会员")   
    print("===================")



def keepLogin():
    while True:
        url = 'http://im37.115.com/chat/r'
        params = {
            'VER':'2',
            'c':'b0',
            's':session_id,
            '_t':str(int(time.time()*1000)),
        }
        r = mySession.get(url=url, params=params)
        time.sleep(60)


def waitLogin():
    while True:
        url = 'http://im37.115.com/chat/r'
        params = {
            'VER':'2',
            'c':'b0',
            's':session_id,
            '_t':str(int(time.time()*1000)),
        }
        r = mySession.get(url=url, params=params)
        try:
            status = json.loads(r.text)[0]['p'][0]['status']
            if status == 1001:
                print(u"请点击登录")
            elif status == 1002:
                print(u"登录成功")
                return
            else:
                return
        except Exception, e:
            print(u"超时，请重试")
            sys.exit(0)

def login(): # 触发登陆
    url = 'http://passport.115.com/'
    params = {
        'ct':'login',
        'ac':'qrcode',
        'key':uid,
        'v':'android',
        'goto':'http%3A%2F%2Fwww.J3n5en.com'
    }
    r = mySession.get(url=url, params=params)


def getTasksign(): # 获取登陆后的sign
    global tsign,ttime
    url = 'http://115.com/'
    params = {
        'ct':'offline',
        'ac':'space',
        '_':str(int(time.time()*1000)),
    }
    r = mySession.get(url=url, params=params)
    tsign = json.loads(r.text)['sign']
    ttime = json.loads(r.text)['time']

def addLinktask(link):
    url = "http://115.com/web/lixian/?ct=lixian&ac=add_task_url"
    data = {
        'url':link,
        'uid':userid,
        'sign':tsign,
        'time':ttime
    }
    linkinfo = json.loads(mySession.post(url,data=data).content)
    try:
        print(linkinfo['error_msg'])
    except Exception, e:
        print(linkinfo['name'])  

def addLinktasks(linklist):
    if len(linklist) > 15:
        for i in range(0,len(linklist),15):
            newlist = linklist[i:i+15]
            addLinktasks(newlist)
    else:
        url = "http://115.com/web/lixian/?ct=lixian&ac=add_task_urls"
        data = {
            'uid':userid,
            'sign':tsign,
            'time':ttime
        }
        for i in range(len(linklist)):
            data['url['+str(i)+']'] = linklist[i]
        linksinfo = json.loads(mySession.post(url,data=data).text)
        # print linksinfo['result']
        for linkinfo in linksinfo['result']:
            try:
                print(linkinfo['error_msg'])
            except Exception, e:
                print(linkinfo['name']) 


def main():
    global mySession
    ssl._create_default_https_context = ssl._create_unverified_context
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2663.0 Safari/537.36'}
    mySession = requests.Session()
    mySession.headers.update(headers)
    if not getInfos(): 
        print(u'获取信息失败')
        return
    getQrcode() # 取二维码
    waitLogin() # 等待手机确认登录
    login() # 触发登陆
    print('开启心跳线程')
    threading.Thread(target=keepLogin) # 开启心跳，防止掉线
    getTasksign() # 获取操作task所需信息
    getUserinfo() # 获取登陆用户信息
    # addLinktask("magnet:?xt=urn:btih:690ba0361597ffb2007ad717bd805447f2acc624")
    # addLinktasks([link]) 传入一个list



if __name__ == '__main__':
    main()
