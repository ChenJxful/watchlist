import os
import sys

from flask import Flask, render_template
from flask import url_for, request, flash, redirect
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from werkzeug.security import generate_password_hash, check_password_hash # 加密密码
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'
# 首先我们从 flask 包导入 Flask 类，通过实例化这个类，创建一个程序对象 app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev' ---- 设置签名所需的密钥
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)  # 初始化扩展，传入程序实例 app

# 用户登录
login_manager = LoginManager(app)  # 实例化扩展类
login_manager.login_view = 'login'
# login_manager.login_message 设置错误提示消息
@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

# 我们要注册一个处理函数，这个函数是处理某个请求的处理函数，
# Flask 官方把它叫做视图函数（view funciton），你可以理解为“请求处理函数”。
@app.route('/', methods=['GET', 'POST']) #我们只需要写出相对地址(我们希望这个函数要处理的收到请求的 url 地址)，主机地址、端口号等都不需要写出。
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 重定向到主页
        title = request.form.get('title')
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')  # 显示错误提示
            return redirect(url_for('index'))  # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')  # 显示成功创建的提示
        return redirect(url_for('index'))  # 重定向回主页

    # 视图函数的名字是自由定义的，和 URL 规则无关
    # user = User.query.first()  # 读取用户记录
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', movies=movies)

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
@app.route('/test1')
def test_url_for():
    print(url_for('index')) # /
    print(url_for('user_page', name='Jiaxiang')) # /user/Jiaxiang
    print(url_for('user_page', name='Wu Fei')) # /user/Wu%20Fei
    print(url_for('test_url_for'))  # 输出：/test1 （最后一个注册的 url 
    # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL 后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2
    print(url_for('edit', movie_id=2))  # /movie/edit/2  输入的是 view function 的 name，会返回它所注册的 url
    return 'test page'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20)) # name
    username = db.Column(db.String(20)) # username
    password_hash = db.Column(db.String(128)) # hash for password

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)  # 返回布尔值

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

# 注册一个创建假用户的命令：forge
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

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')

@app.errorhandler(404)
def page_not_found(e): # 接受异常对象作为参数
    return render_template('404.html'), 404

# 模板上下文处理函数
@app.context_processor
def inject_user_name():
    user = User.query.first()
    return {'user': user}

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')

@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')