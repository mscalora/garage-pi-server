# -*- coding: utf-8 -*-

import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask.ext.bcrypt import Bcrypt
import time
import datetime

# create our little application :)
import sys

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'garage-pi.db'),
    DEBUG=True,
    SECRET_KEY='so-so-secret'
))
app.config.from_envvar('SETTINGS_FILE', silent=True)


def unauthenticated(func):
    if 'unauthenticated_list' not in globals():
        globals()['unauthenticated_list'] = ["static"]
    """decorator to identify requests which don't need authentication"""
    globals()['unauthenticated_list'].append(func.__name__)
    return func


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    bcrypt.generate_password_hash('hunter2')
    print('Initialized the database.')


@app.cli.command('hashpw')
def hashpw_command():
    """Output a password hash."""
    print('Password hash: %s' % bcrypt.generate_password_hash(app.config['PASSWORD']))
    print("Don't forget to set the BCRYPT setting to True")


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.before_request
def before_request():
    """require authentication on all request which are not specifically decorated with @unauthenticated"""
    if 'unauthenticated_list' not in globals():
        globals()['unauthenticated_list'] = ["static"]
    if 'logged_in' not in session and request.endpoint not in globals()['unauthenticated_list']:
        return redirect(url_for('login'))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/log')
def log():
    db = get_db()
    cur = db.execute('select id, type, detail, `timestamp` from log order by id desc')
    entries = cur.fetchall()
    return render_template('log.html', entries=entries)


def add_log_entry(log_entry_type, log_entry_detail, ts=None):
    try:
        db = get_db()
        db.execute('insert into log (id, type, detail, timestamp) values (null, ?, ?, ?)', [
            log_entry_type,
            log_entry_detail,
            datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        ])
        db.commit()
    except sqlite3.DatabaseError as e:
        sys.stderr.write("Database error: %s\n" % repr(e))
        return False
    return True


@app.route('/add', methods=['POST'])
def add_entry():
    db_ok = add_log_entry(request.form['type'], request.form['detail'])
    if db_ok:
        flash('New log entry was made.', category='message')
    else:
        flash('Database making log entry.', category='error')
    return redirect(url_for('log'))


@app.route('/login', methods=['GET', 'POST'])
@unauthenticated
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        cur = db.execute('select id, userid, pwhash, admin from user where userid = ?', [request.form['username']])
        users = cur.fetchall()
        if len(users):
            user = dict(users[0])
            if bcrypt.check_password_hash(user['pwhash'], request.form['password']):
                session['logged_in'] = user
                return redirect(url_for('home'))
    return render_template('login.html', error=error)


@app.route('/create_user', methods=['GET', 'POST'])
@unauthenticated
def create_user():
    error = None
    if request.method == 'POST':
        db = get_db()
        db.execute('insert into user (id, userid, pwhash, admin) values (null, ?, ?, ?)', [
            request.form['username'],
            bcrypt.generate_password_hash(request.form['password']),
            1 if 'admin' in request.form else 0
        ])
        db.commit()
        flash('New user was successfully created')
    return render_template('create_user.html', error=error)


@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))
