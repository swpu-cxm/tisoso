"""
这是模块未合并之前的代码,可能无法正常使用,但是可以学习用,有比较详细的注释
"""

import requests
import re
import json
import random
import copy

"""
    此程序是上学吧APP端抓包分析的数据,APP名为搜题
    数据组成:
    keyword=查找的关键字
    id=题的id
    username就是电话号码,找个接码平台注册一个就好
    userid就是用户id,抓包能看见你自己的id
    如果不登录的话,它的token是一直在变化的,而登录后token则不会变化
    重要!!!:
        iden参数
        此参数就是限制客户端每天免费查询的次数,经试验,用随机数随便构造一下就好了
    其余参数都不是很重要
"""
token = 'CCA7FFF7E4F7C18DDD234633592FA996'


def search_question(keyword):  # 根据题目关键字去查询,返回查到的题目ID,如果异常,则返回None
    questions_id = []
    search_url = 'http://app.shangxueba.com/ask/search.ashx'  # 查询的api
    search_data = {
        'source': '3',  # 不知道
        'username': '18207729487',  # 手机号
        'token': token,  # 抓包的token,和手机号也是一一对应的
        'iden': 'E3A4F83A7142675845EDB759FFC9FF06_xxx',  # 这个不用构造,最后获取答案时才需要
        'keyword': keyword,  # 查询的关键词
        'GlobalAppType': '6',  # 不知道
        'type': 'IPHONE100',  # 手机类型,没啥用
        'page': '1',  # 查询信息的页数,一般第一页就比较准确了
        'userid': '6807647',  # 用户ID,和手机号是一一对应的
    }
    search_response = requests.post(search_url, data=search_data)  # 模拟http发送搜索请求
    if search_response.status_code == 200:  # 判断是否请求正常
        text = search_response.text
        text = json.loads(text)  # 解析返回的json数据
    else:
        return {'status': 'error:',
                'message': 'search question id error ,error code:' + search_response.status_code}  # 如果异常,返回异常状态码
    if text['code'] == 'success':  # 即使请求状态码为200,可能依旧请求失败,会返回一个状态码,success或者fail
        for question in text['list']:
            questions_id.append(question['id'])
        return {'status': 'ok', 'message': questions_id}  # ,questions_title,questions_content
    else:
        return {'status': 'fail', 'message': 'search:' + text['msg']}


def get_info(id):  # 根据题目的ID去获取题目的信息,如果获取成功,则返回完整的题目的内容,题目＋选项,失败则返回None
    get_info_url = 'http://app.shangxueba.com/ask/getinfo.ashx'
    data = {
        'username': '18207729487',
        'id': id,
        'token': token,
        'iden': 'E3A4F83A7142475845EDB759FAC9FF06_xxx',
        'GlobalAppType': '6',
        'type': 'IPHONE100',
        'userid': '6807647',
    }
    search_response = requests.post(url=get_info_url, data=data)
    if search_response.status_code == 200:
        text = search_response.text
        text = json.loads(text)
    else:
        return {'status': 'error:', 'message': 'search question title error ,error code:' + search_response.status_code}
    if text['code'] == 'fail':
        return {'status': 'error:', 'message': 'get_info:' + text['msg']}
        # return None
    else:
        questions_context = text['data']['AskInfo']['context']
        return {'status': 'ok', 'message': questions_context}


def get_best(id):  # 根据题目的id去查询题目的答案,成功则返回答案(＋解析),失败则返回None
    get_best_url = 'http://app.shangxueba.com/ask/getzuijia.ashx'
    iden = ''
    for i in range(5):  # 五位随机数,一天应该用不完了,需要可以多加几位,一个iden可以免费4次
        iden += str(random.randrange(1, 10))
    data = {
        'username': '18207729487',
        'id': id,
        'token': token,
        'iden': iden + 'E3A4F83A74445EDB759FFC9FF06_xxx',  # 随机iden
        'GlobalAppType': '6',
        'type': 'IPHONE100',
        'userid': '6807647',
    }
    search_response = requests.post(url=get_best_url, data=data)
    if search_response.status_code == 200:
        text = search_response.text
        text = json.loads(text)
        # print(text)
    else:
        return {'status': 'error:', 'message': 'search question title error ,error code:' + search_response.status_code}
    if text['code'] == 'fail':
        return {'status': 'error:', 'message': 'get_best:' + text['msg']}
        # print('get_best:' + text['msg'])
        # return None
    else:
        # print(text)
        try:
            first_question_id = text['data']['ZJAnswer'][0]['Context']  # 获取第一个最佳答案
            # print(first_question_id)
            return {'status': 'ok', 'message': first_question_id}
            # print(first_question_id)
        except Exception as e:
            print(e)
            first_question_id = None  # 如果没有答案
            return {'status': 'error:', 'message': first_question_id}


def sxb(question):
    # system('color 70')
    # question = input('请输入要搜索的问题:')
    questions_context = []
    context_answer_list = []
    questions_answer = []
    # print(context_answer_list)
    questions_id = search_question(question)  # 搜索问题,返回ID列表
    if questions_id['status'] == 'ok':  # 查询是否成功
        id_list = questions_id['message']
        for id in id_list:
            context = get_info(id)  # 获取题目内容
            if context['status'] == 'ok':  # 是否获取到题目内容
                # print(context['message']+'+++++')
                questions_context.append(context['message'])
            else:
                continue  # 获取题目失败就查找下一个ID的题目和答案
                # return {'status': 'error', 'message': context['message']}
                # print('Get context error...')
            answer = get_best(id)
            # print(answer, answer['message'])
            if answer['status'] == 'ok':  # 是否获取到题目答案
                questions_answer.append(answer['message'])
            else:
                continue
                # return {'status': 'error', 'message': 'Get answer error...'}
                # print('Get answer error...')
        length = len(questions_answer)
        for l in range(length - 1):  # 最后一条数据有问题,去掉了
            try:
                context = re.sub('((<br/>)+)|(请帮忙给出正确答案和分析，谢谢！)', '\n', questions_context[l], re.S)
                answer = re.sub('(<br/>)+', '\n', questions_answer[l], re.S)  # 除去与题目不相关的
            except:
                context = questions_context[l]
                answer = questions_answer[l]  # 防止没有答案
            finally:
                context_answer = {'context': context, 'answer': answer}
                # print(context_answer)
                context_answer_list.append(context_answer)
        message_list = []
        # del message_list[:]
        # print(message_list)
        # del questions_id
        # del questions_context
        # del questions_answer
        message_list = copy.deepcopy(context_answer_list)  # =
        # del context_answer_list
        # print(context_answer_list)
        # print(message_list)
        return {'status': 'ok', 'message': message_list}
    else:
        return {'status': 'error', 'message': questions_id['message']}
    # input()


def login():
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
        'username': '18207729487',
        'GlobalAppType': '6',
        'token': '3E09BF9E7078345360A3F97F21381161',
        'type': 'NX595J',
        'pass': '0659C7992E268962384EB17FAFE88364',
        'iden': '65D52172298A9C67177878E737F9854F_xxx'
    }
    response = requests.post('http://app.shangxueba.com/user/Login.ashx', headers=headers, data=data)
    # print(requests.status_codes)
    response = json.loads(response.text)
    print(response['data']['user']['token'])

# if __name__ == '__main__':
#     #login()
#     token = 'CCA7FFF7E4F7C18DDD234633592FA996'
#     print(sxb('数据结构'))
