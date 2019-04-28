# Django+爬虫,实现一个在线题库搜索引擎
## 环境:Django 2.1.7,aiohttp 3.5.4,,pyquery 1.4.0,requests 2.21.0
## <font color='red'>声明:本项目仅供个人学习,请勿作商用,如有侵权请联系我删除,请不要让警察叔叔抓走我</font>
## 预览图:
![image](https://github.com/swpu-cxm/tisoso/blob/master/tss.png)
![image](https://github.com/swpu-cxm/tisoso/blob/master/tss2.png)
## 项目浏览: [题搜搜](http://tss.cxmgxj.cn "题搜搜")
## 项目介绍:
	 输入题目,通过异步爬虫爬取考试资料网,上学吧两个在线搜题网站,然后将爬取的题目及答案显示在网页
## 项目核心:
	 此项目的关键是爬取搜题网站,主要涉及的是题目数据的清洗,
	 获取答案链接请求参数的破解.
	 答案请求方式的分析.
	 限制免费次数的分析.
## 核心程序为index/tisoso.py
### 开发版的程序为index/shangxueba.py和index/ppkao.py里面有详细的注释
   
## 上学吧接口分析,关于上学吧,我是通过Fiddler进行app抓包分析的,主要有3个阶段:
1.  输入问题,获取返回问题ID列表
2.  根据ID去获取题目的信息,如果获取成功,则返回完整的题目的内容即题目＋选项
3.  根据ID去获取题目答案,关键在于post请求data中的iden参数,此参数是服务的验证用户是否已经用完免费次数,所以只<br>需要每次请求答案是更换不同的iden,就可以去除限制

## 考试资料网接口分析,主要有3个阶段 :
1.  输入问题,获取问题ID列表
2.  此网站查看答案是通过页面上的一个按钮跳转至获取答案的Api再重定向到答案页面,其中会有云盾和用户登录验证,所<br>以我们直接以post方式请求Api,直接获取答案链接,进而直接访问答案链接,免去中间登录和云盾的验证.注意,返回的是带<br>有XXX/tiku/daan/id.html,但是实际在浏览器查看答案是没有'/tiku'的,即应该是XXX/daan/id.html
3.  直接在答案页面爬取完整的题目,选项,及答案图片的base64编码

## 如何开始?
    git clone git@github.com:swpu-cxm/tisoso.git
    cd tisoso
    pipenv install
    pipenv shell
    python manager.py runserver
    
