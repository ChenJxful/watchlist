from flask import Flask
from flask import url_for
from markupsafe import escape
# 首先我们从 flask 包导入 Flask 类，通过实例化这个类，创建一个程序对象 app
app = Flask(__name__)

# 我们要注册一个处理函数，这个函数是处理某个请求的处理函数，
# Flask 官方把它叫做视图函数（view funciton），你可以理解为“请求处理函数”。
@app.route('/') #我们只需要写出相对地址，主机地址、端口号等都不需要写出。
def hello():
    # 视图函数的名字是自由定义的，和 URL 规则无关
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'

# 一个视图函数也可以绑定多个 URL，这通过附加多个装饰器实现，比如：
# @app.route('/')
# @app.route('/index')
# @app.route('/home')
# def hello():
#     return 'Welcome to My Watchlist!'

# 我们之所以把传入 app.route 装饰器的参数称为 URL 规则，
# 是因为我们也可以在 URL 里定义变量部分。比如下面这个视图函数会处理所有类似 /user/<name> 的请求：
@app.route('/user/<name>')
def user_page(name):
    # WARN: 注意 用户输入的数据会包含恶意代码，所以不能直接作为响应返回，
    # 需要使用 MarkupSafe（Flask 的依赖之一）提供的 escape() 函数对 name 变量进行转义处理，
    # 比如把 < 转换成 &lt;。这样在返回响应时浏览器就不会把它们当做代码执行。
    return f'User: {escape(name)}'

@app.route('/test')
def test_url_for():
    print(url_for('hello')) # /
    print(url_for('user_page', name='Jiaxiang')) # /user/Jiaxiang
    print(url_for('user_page', name='Wu Fei')) # /user/Wu%20Fei
    print(url_for('test_url_for'))  # 输出：/test
    # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL 后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2
    return 'test page'