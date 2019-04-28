"""
这是模块未合并之前的代码,可能无法正常使用,但是可以学习用,有比较详细的注释
"""

import asyncio
import async_timeout
import aiohttp
import re
import requests
import json
import base64
import urllib.parse
import logging
from pyquery import PyQuery as pq



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


def get_redirect_url(id):  # 第二步,根据ID获取答案页面链接
    redirect_url = 'https://api.ppkao.com/ajax/QZ.Website.mnkc.tiku.index,QZ.Website.ashx?' \
                   '_method=ResponseRedirect&_session=rw'
    # 此网站查看答案是通过页面上的一个按钮跳转至获取答案的Api,所以我们直接以post方式请求Api,form和headers如下,返回答案链接
    data = {
        'id': id,  # 题目Id,如https://www.ppkao.com/tiku/shiti/8813450.html
    }
    headers = {  # cookie是必须的,为了保险,还是加个浏览器头
        'User-Agent': 'Mozilla/5.0(WindowsNT10.0;WOW64)AppleWebKit/537.36(KHTML, likeGecko)Chrome/63.0.3239.26Safari/537.36Core/1.63.6776.400QQBrowser/10.3.2601.400',
        'cookie': 'Tid=101789; VerificationCodeNum=VerificationCodeNum=1; '
    }
    response = requests.post(redirect_url, headers=headers, data=data, verify=False, timeout=5)  # post方式请求Api
    if response.status_code == 200:
        url = response.text
        url = url.replace('/tiku', '')  # 这里是个大坑,返回的是带有XXX/tiku/daan/id.html,但是实际在浏览器查看答案是没有'/tiku'的,不去掉会到其他页面去
        return url
    else:
        print('Get redirect url error:', response.status_code)
        return None


def get_url_list(id_list):
    url_list = []
    async def fetch_async(data):
        with async_timeout.timeout(5):
            async with aiohttp.request("POST", redirect_url, data=data, headers=headers) as r:
                response = (await r.read()).decode('gbk')
                url_list.append(response.replace("'", '').replace('/tiku', ''))

    redirect_url = 'https://api.ppkao.com/ajax/QZ.Website.mnkc.tiku.index,QZ.Website.ashx?' \
                   '_method=ResponseRedirect&_session=rw'
    # 此网站查看答案是通过页面上的一个按钮跳转至获取答案的Api,所以直接以post方式请求Api,form和headers如下,返回答案链接
    headers = {
        'User-Agent': 'Mozilla/5.0(WindowsNT10.0;WOW64)AppleWebKit/537.36(KHTML, likeGecko)Chrome/63.0.3239.26Safari/537.36Core/1.63.6776.400QQBrowser/10.3.2601.400',
        'cookie': 'Tid=101789; VerificationCodeNum=VerificationCodeNum=1; '
        # cookie是必须的,为了保险,还是加个浏览器头
    }
    tasks = []
    for id in id_list:
        data = {
            'id': id,  # 题目id,如https://www.ppkao.com/tiku/shiti/8813450.html
        }
        tasks.append(fetch_async(data))
    event_loop = asyncio.get_event_loop()
    results = event_loop.run_until_complete(asyncio.gather(*tasks))
    # event_loop.close()
    return url_list


# def get_question(url):  # 提取题目
#     response = requests.get(url, verify=False)  # 请求网页
#     if response.status_code == 200:
#         html = response.text
#         doc = pq(html)
#         message_dict = {}
#         message_dict['question'] = doc('.kt').text()
#         message_dict['option'] = doc('.single-siti p').text()
#         message_dict['answer'] = doc('.analysis img').attr('src')
#     return message_dict

def get_messages_list(url_list):
    message_list = []
    async def fetch_async02(url):
        async with aiohttp.request("GET", url) as r:
            html = (await r.read()).decode('gbk')
            doc = pq(html)
            message_dict = {}
            message_dict['question'] = doc('.kt').text()
            message_dict['option'] = doc('.single-siti p').text()
            message_dict['answer'] = doc('.analysis img').attr('src')
            if not message_dict['answer']:
                message_dict['answer'] = doc('.siti-answer .w600').text()
            message_list.append(message_dict)

    tasks02 = []
    for url in url_list:
        tasks02.append(fetch_async02(url))
    event_loop02 = asyncio.get_event_loop()
    results = event_loop02.run_until_complete(asyncio.gather(*tasks02))
    event_loop02.close()
    return message_list


def ppk(question):
    # section1 = time.time()
    logging.captureWarnings(True)
    id_list = get_question_id(question)
    # section2 = time.time()
    # print('第一阶段:', section2 - section1)
    # print(id_list)
    url_list = get_url_list(id_list)

    # print(url_list)
    # section3 = time.time()
    # print('第二阶段:', section3 - section2)

    message_list = get_messages_list(url_list)
    # print(message_list)
    # section4 = time.time()
    # print('第三阶段:', section4 - section3)

    # print('总耗时:', section4 - section1)
    return message_list

# if __name__ == '__main__':