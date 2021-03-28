from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, PasswordField, validators, TextAreaField


# control the page
def permission_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You don't have a permission for view this page!", "danger")
            return redirect(url_for("login"))

    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You don't have a permission for view this page!", "danger")
            return redirect(url_for("login"))

    return decorated_function


class RegisterForm(Form):
    name = StringField("Name Surname", validators=[validators.Length(min=4, max=25)])
    username = StringField("Username", validators=[validators.Length(min=4, max=25)])
    email = StringField("Email", validators=[validators.Email(message="Email is not valid!")])
    password = PasswordField("Password:", validators=[
        validators.DataRequired(message="Please write a password"),
        validators.EqualTo(fieldname="confirm", message="Password is not same!")
    ])
    confirm = PasswordField("Password Confirm")


class LoginForm(Form):
    username = StringField("Username", validators=[validators.Length(min=4, max=100)])
    password = PasswordField("Password:", validators=[validators.Length(min=4, max=100)])


class ArticleForm(Form):
    article_title = StringField("Title", validators=[validators.Length(min=4, max=100)])
    article_content = TextAreaField("Content", validators=[validators.Length(min=10)])


app = Flask(__name__)
app.secret_key = "myblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "myblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route('/')
def index():
    numbers = {1, 2, 3, 4, 5}
    return render_template("index.html", answer="Yes", numbers=numbers)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/article/<string:id>')
def article_detail(id):
    cursor = mysql.connection.cursor()
    query = "Select * from articles where id = %s"
    result = cursor.execute(query, (id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")


@app.route('/delete/<string:id>')
@login_required
def article_delete(id):
    cursor = mysql.connection.cursor()
    query = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(query, (session["username"], id))
    if result > 0:
        query_delete = "Delete from articles where id = %s"
        cursor.execute(query_delete, (id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("There is no article like that or you don't have permission to delete the article", "danger")
        return redirect(url_for("index"))


@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "Select * From articles where author = %s"
    result = cursor.execute(query, (session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")
    return render_template("dashboard.html")


@app.route('/edit/<string:id>', methods=["GET", "POST"])
@login_required
def update_article(id):
    cursor = mysql.connection.cursor()

    if request.method == "GET":
        query = "Select * from articles where author = %s and id = %s"
        result = cursor.execute(query, (session["username"], id))
        if result > 0:
            article = cursor.fetchone()
            form = ArticleForm()

            form.article_title.data = article["title"]
            form.article_content.data = article["content"]
            return render_template("update.html", form=form)
        else:

            flash("There is no article like that or you don't have permission to delete the article", "danger")
            return redirect(url_for("index"))
    else:
        form = ArticleForm(request.form)
        new_title = form.article_title.data
        new_content = form.article_content.data
        query_update = "Update articles set title = %s, content=%s where id = %s"
        cursor.execute(query_update, (new_title, new_content, id))
        mysql.connection.commit()
        flash("There is no article like that or you don't have permission to delete the article", "success")
        return redirect(url_for("dashboard"))


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        query = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(query, (name, username, email, password))
        mysql.connection.commit()
        cursor.close()
        flash("Registered successfully", "success")

        return redirect(url_for("index"))
    else:
        return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        query = "select *from users where username=%s"
        result = cursor.execute(query, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            cursor.close()
            if sha256_crypt.verify(password_entered, real_password):
                flash("Login Successfuly!", "success")
                session["logged_in"] = True
                session["username"] = username
                return render_template("index.html")
            else:
                cursor.close()
                flash("username or password is incorrect!", "danger")
                return redirect(url_for("login"))
        else:
            flash("username or password is incorrect!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route('/addarticle', methods=["GET", "POST"])
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.article_title.data
        content = form.article_content.data
        cursor = mysql.connection.cursor()

        query = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(query, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Article added succesfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form)


@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()

    query = "select * from articles"

    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)

    else:
        return render_template("articles.html")

    flash("Registered successfully", "success")


@app.route('/logout')
def logout():
    session.clear()
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)
