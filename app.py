
from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def index():
    numbers = {1, 2, 3, 4, 5}
    return render_template("index.html", answer="Yes", numbers=numbers)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/articles/<string:id>')
def detail(id):
    return "Article id: " + id


if __name__ == '__main__':
    app.run()
