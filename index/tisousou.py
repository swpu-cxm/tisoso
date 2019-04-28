import asyncio
import aiohttp
import random
import re
import time
import requests
import json
import base64
import urllib.parse
import logging
from pyquery import PyQuery as pq
import async_timeout


def login():
    """
    shangxueba用户登录,token口令是有时间的,大概十几天,所以需要动态更新口令
    :return:
    """
    headers = {
        'User-Agent': 'com.shangxueba.newsxb',
        'AppVersion': '1.5',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': '167',
        'Host': 'app.shangxueba.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    }
    data = {
        'username': '18207729487',  # 用户名
        'GlobalAppType': '6',
        'token': '3E09BF9E7078345360A3F97F21381161',
        'type': 'NX595J',
        'pass': '0659C7992E268962384EB17FAFE88364',  # 密码,MD5加密
        'iden': '65D52172298A9C67177878E737F9854F_xxx'
    }
    response = requests.post('http://app.shangxueba.com/user/Login.ashx', headers=headers, data=data)
    # print(requests.status_codes)
    response = json.loads(response.text)
    return response['data']['user']['token']


token = login()


def get_question_id(question):  # 第一步,输入问题,获取questionID
    question = urllib.parse.quote(question.encode('gb2312'))  # 将问题进行编码
    url = 'https://api.ppkao.com/Interface/UserQueryApi.ashx?action=GetUserQuery&word=' + question \
          + '&page=1&source=Android&sign=9acbfd8145328f814a02220ec374f68e'  # 本次用的是Android的Api接口,因为网页端是JS动态生成的,不方便处理
    response = requests.get(url, verify=False)  # 请求Api,获取响应结果
    msg = json.loads(response.text)  # json反序列化
    id_list = []
    for i in range(10 if len(msg['UserQueryList']) > 10 else len(msg['UserQueryList'])):
        urlPC = msg['UserQueryList'][i]['urlPC']  # 默认只取了第一个搜索结果,如https://www.ppkao.com/shiti/4273158/
        urlPC = base64.b64decode(urlPC).decode('utf-8')  # 此网站的Api接口都是base64编码的,所以需要解码
        id = re.findall('/(\d+)(/|\.)', urlPC)[0][0]  # 从获取的url中找到题目ID
        id_list.append(id)
    return id_list


def get_id_list(keyword):
    """
    根据题目关键字去查询,返回查到的题目ID列表,如果异常,则返回None
    method : POST
    :param keyword: 需要查询的问题关键字
    :return: 问题id列表
    """
    questions_id = []
    search_url = 'http://app.shangxueba.com/ask/search.ashx'  # 查询的api
    search_data = {
        'source': '3',  # 不重要
        'username': '18207729487',  # 手机号
        'token': token,  # 抓包的token,和手机号也是一一对应的
        'iden': 'E3A4F83A7142675845EDB759FFC9FF06_xxx',  # 这个不用构造,最后获取答案时才需要
        'keyword': keyword,  # 查询的关键词
        'GlobalAppType': '6',  # 不重要
        'type': 'IPHONE100',  # 手机类型,没啥用
        'page': '1',  # 查询信息的页数,一般第一页就比较准确了
        'userid': '6807647',  # 用户ID,和手机号是一一对应的
    }
    search_response = requests.post(search_url, data=search_data)
    text = search_response.text
    text = json.loads(text)  # 解析返回的json数据
    for question in text['list']:
        questions_id.append(question['id'])
    return questions_id


def get_msg_list(id_list_1, id_list_2):
    """
    异步根据ID获取题目及解答,传入两个ID_list,返回两个问题及解答列表
    :param id_list_1:  引擎一的ID列表 [str(id1),str(id2),str(id3)]
    :param id_list_2:  #引擎二的ID列表 [str(id1),str(id2),str(id3)]
    :return: message_list_1,message_list_2: [{'question':question,'answer':answer}]
    """
    message_list_1 = []
    redirect_url = 'https://api.ppkao.com/ajax/QZ.Website.mnkc.tiku.index,QZ.Website.ashx?' \
                   '_method=ResponseRedirect&_session=rw'
    # 此网站查看答案是通过页面上的一个按钮跳转至获取答案的Api,所以直接以post方式请求Api,form和headers如下,返回答案链接
    headers = {
        'User-Agent': 'Mozilla/5.0(WindowsNT10.0;WOW64)AppleWebKit/537.36(KHTML, likeGecko)Chrome/63.0.3239.26Safari/537.36Core/1.63.6776.400QQBrowser/10.3.2601.400',
        'cookie': 'Tid=101789; VerificationCodeNum=VerificationCodeNum=1; '
        # cookie是必须的
    }

    async def fetch_async_1(id):
        message_dict = {}
        data = {
            'id': id,  # 题目id,如https://www.ppkao.com/tiku/shiti/8813450.html
        }
        try:
            with async_timeout.timeout(3):
                async with aiohttp.request("POST", redirect_url, data=data, headers=headers) as r:
                    response = (await r.read())
                    response = response.decode()
                    url = response.replace("'", '').replace('/tiku', '')
                async with aiohttp.request("GET", url) as r:
                    html = (await r.text())
                    doc = pq(html)
                    message_dict['question'] = doc('.kt').text()
                    message_dict['option'] = doc('.single-siti p').text()
                    message_dict['answer'] = doc('.analysis img').attr('src')
                    if not message_dict['answer']:
                        message_dict['answer'] = doc('.siti-answer span').text()
                    message_list_1.append(message_dict)
        except Exception as e:
            print(e)

    """"""""""""""""""""""""""""""""""""""""""""""""""""""""

    get_info_url = 'http://app.shangxueba.com/ask/getinfo.ashx'
    get_best_url = 'http://app.shangxueba.com/ask/getzuijia.ashx'
    message_list_2 = []

    async def fetch_async_2(id):
        msg_dict = {}
        get_info_data = {
            'username': '18207729487',
            'id': id,
            'token': token,
            'iden': 'E3A4F83A7142475845EDB759FAC9FF06_xxx',
            'GlobalAppType': '6',
            'type': 'IPHONE100',
            'userid': '6807647',
        }
        iden = ''
        for i in range(6):  # 模拟的口令
            iden += str(random.randrange(1, 10))
        get_best_data = {
            'username': '18207729487',
            'id': id,
            'token': token,
            'iden': iden + '3A4F83A74445EDB759FFC9FF06_xxx',  # 随机iden
            'GlobalAppType': '6',
            'type': 'IPHONE100',
            'userid': '6807647',
        }
        try:
            with async_timeout.timeout(3):
                async with aiohttp.request("POST", get_info_url, data=get_info_data) as r1:
                    html = await r1.read()
                    text = json.loads(html)
                    if text['code'] == 'success':
                        questions = text['data']['AskInfo']['context']
                    else:
                        questions = None
                async with aiohttp.request("POST", get_best_url, data=get_best_data) as r2:
                    html = await r2.read()
                    text = json.loads(html)
                    if text['code'] == 'success':
                        try:
                            answer = text['data']['ZJAnswer'][0]['Context']  # 获取第一个最佳答案
                        except Exception as e:
                            answer = None  # 如果没有答案
                    else:
                        answer = None
                msg_dict['question'] = questions
                msg_dict['answer'] = answer
                message_list_2.append(msg_dict)
        except Exception as e:
            print(e)

    tasks = []
    for id_1 in id_list_1:
        tasks.append(fetch_async_1(id_1))
    for id_2 in id_list_2:
        tasks.append(fetch_async_2(id_2))
    asyncio.set_event_loop(asyncio.new_event_loop())
    event_loop = asyncio.get_event_loop()
    results = event_loop.run_until_complete(asyncio.gather(*tasks))
    event_loop.close()
    return message_list_1, message_list_2


def tisousou(question):
    logging.captureWarnings(True)
    id_list_1 = get_question_id(question)
    id_list_2 = get_id_list(question)
    message_list_1, message_list_2 = get_msg_list(id_list_1, id_list_2)
    return message_list_2, message_list_1
