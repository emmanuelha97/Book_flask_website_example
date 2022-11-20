import os
from flask import Flask, request, make_response, redirect, abort, render_template, session, url_for, flash, escape
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime

# importing flask forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

# set the base directory for the SQLAlchemy DB
basedir = os.path.abspath(os.path.dirname(__file__))

# our base server name
app = Flask(__name__)
# configure the database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join('data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# configure a hidden key to protect against session tampering
# app.config is used to store configuration variables
app.config['SECRET_KEY'] = 'supersecretpassword'
# wrapping our base server with the bootstrap
bootstrap = Bootstrap(app)
# wrapping our base server with time keeping package
moment = Moment(app)

# set up the database
db = SQLAlchemy(app)


# creating a class for the forms
class NameForm(FlaskForm):
    name = StringField("What is your name?", validators=[DataRequired()])
    message = StringField("Message:", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField("Enter your username:", validators=[DataRequired()])
    password = StringField("Enter your password:", validators=[DataRequired()])
    submit = SubmitField("Login")


# creating classes for the SQL DB to follow [these will be the models for the DB]
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


# main index example returns the page html and the response status
# can return a third argument I forgot which rn
# specify which methods if not then default is just 'GET'
@app.route('/', methods=["GET", "POST"])
def index():
    # store a session data_base
    session['database'] = {}
    form = NameForm()
    if request.method == "POST":
        if form.validate_on_submit():
            old_name = session.get('name')
            if old_name is not None and old_name != form.name.data:
                flash('Looks like you have changed your name!')
            session['name'] = form.name.data
            if session.get('message') is None:
                session['message'] = [form.message.data]
            else:
                session['message'].append(form.message.data)
            return redirect(url_for('index'))
    # user_agent = request.headers.get('User-Agent')
    if request.method == "GET":
        return render_template(
            'index.html',
            form=form,
            name=session.get('name'),
            messages=session.get('message'),
            current_time=datetime.utcnow()
        ), 404


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
            session['name'] = form.name.data
            form.name.data = ''
            return redirect(url_for('homepage'))
    return render_template('indexv2.html',
                           form=form,
                           name=session.get('name'),
                           known=session.get('known', False))


@app.route('/loggedin', methods=['GET'])
def logged_in_page():
    if session.get('database') is None or session['database']['logged_in_status'] is None:
        return render_template('404.html'), 404

    return render_template(
        'logged.html',
        name=session.get('name'),
        logged_in_status=session.get('logged_in_status'),
        username=session['database']['logged_in_status']['username'],
        password=session['database']['logged_in_status']['password'],
        current_time=datetime.utcnow()
    )


@app.route('/login', methods=["GET", "POST"])
def login_page():
    session['database'] = {}
    login_form = LoginForm(request.form)
    if request.method == "POST":
        if login_form.validate_on_submit():
            session['database']['logged_in_status'] = {
                "username": login_form.username.data,
                "password": login_form.password.data,
            }
            session['logged_in_status'] = True
            return redirect(url_for('logged_in_page'))
    if request.method == "GET":
        return render_template(
            'login.html',
            form=login_form,
        ), 200
    flash(login_form.errors)
    return render_template('404.html'), 404


# aborts the request if the given query string does not match an item in the database
@app.route('/abortme/<id>')
def abort_site():
    if id is int:
        abort(404)
    return '<h1>Hello World!</h1>'


# redirects to a different page
@app.route('/uturn')
def u_turn():
    return redirect('https://www.google.com')


# sets a cookie to the response
@app.route('/cookies')
def cookiecookie():
    response = make_response('<h1>I am giving you a cookie</h1>')
    response.set_cookie('session',
                        '.eJwVyEEKgzAQRuG7_OssmkmCo3fwBFJkYmZcFFMwbkS8ey28zfcuLG23-fh-tGIAJSZeklrvU-ZYOm8k2uUSKLy8sOVorMHgUOSQLE0xXLfDpq3J-mBCpEDxH94OVbZnYpRaT9w_Ng8g0g.Y3Gh_g.UhGiOcyj1v5lE9IF669Y6SeqZg8')
    return response, 200


# dynamically sets the name and greets with Hello, NAME!
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


#
# @app.route('/user/<username>')
# def show_user_profile(username):
#     # show the user profile for that user
#     return f'User {escape(username)}'


@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return f'Post {post_id}'


@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return f'Subpath {escape(subpath)}'


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
