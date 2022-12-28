import os
import sys

from flask import Flask, render_template
from flask import url_for
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'
# 首先我们从 flask 包导入 Flask 类，通过实例化这个类，创建一个程序对象 app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)  # 初始化扩展，传入程序实例 app


# 我们要注册一个处理函数，这个函数是处理某个请求的处理函数，
# Flask 官方把它叫做视图函数（view funciton），你可以理解为“请求处理函数”。
@app.route('/') #我们只需要写出相对地址，主机地址、端口号等都不需要写出。
def hello():
    # 视图函数的名字是自由定义的，和 URL 规则无关
    user = User.query.first()  # 读取用户记录
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', name=user.name, movies=movies)

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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20)) # name

class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份

# 自定义命令 initdb
# 默认情况下，如果没有指定，函数名称就是命令的名字（注意函数名中的下划线会被转换为连接线）
import click
@app.cli.command() # 注册命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialize databse.')

@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    # 全局的两个变量移动到这个函数内
    name = 'Jiaxiang Chen'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')