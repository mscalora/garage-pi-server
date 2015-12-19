# -*- coding: utf-8 -*-
from collections import OrderedDict
import os
import re
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, send_file, jsonify  # , logging as flask_logging
from flask.ext.bcrypt import Bcrypt
import time
import datetime
import camera
import gpio
import sys

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'garage-pi.db'),
    DEBUG=True,
    SECRET_KEY='so-so-secret',
    TMP_IMAGES_PATH='/var/tmp',
    GDOOR_CODE='1234'
))
app.config.from_envvar('SETTINGS_FILE', silent=True)


if 'REMOTE_DEBUG' in app.config or 'REMOTE_DEBUG' in os.environ:
    import pydevd
    con = (app.config['REMOTE_DEBUG'] if 'REMOTE_DEBUG' in app.config else os.environ['REMOTE_DEBUG']).split(':')
    pydevd.settrace(con[0], port=int(con[1]), stdoutToServer=True, stderrToServer=True)


if 'LOG_FILE' in app.config:
    from logging.handlers import TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(app.config['LOG_FILE'])
    handler.setLevel(app.config['LOG_LEVEL'] if 'LOG_LEVEL' in app.config else 'WARNING')
    app.logger.addHandler(handler)


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


@app.cli.command('test')
def test():
    print()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    print("Initializing: %s" % app.config['DATABASE'])
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print('Initialized the database. Use create_admin to create your fist admin user.')


@app.cli.command('create_admin')
def create_admin():
    """Create admin user.

    run on command line in project folder like:

        USER=joe PW=secret flask -a garage-pi create_admin

    """
    userid = os.getenv('USER', False)
    if not userid or os.getenv('PW', False) == False:
        print("You must set environment variables USER and PW.")
        print("Example:")
        print("    USER=joe PW=secret flask -a garage-pi create_admin")
        return
    print("Adding admin user %s to: %s" % (userid, app.config['DATABASE']))
    db = get_db()
    cur = db.execute('select id, userid, pwhash, admin from user where userid = ?', [userid])
    entries = cur.fetchall()
    if len(entries):
        for entry in entries:
            print("%s user with the userid '%s' exists." % ('Admin' if int(entry['admin']) else 'Non-admin', entry['userid']))
        return
    db.execute('insert into user (id, userid, pwhash, admin) values (null, ?, ?, ?)', [
        userid,
        bcrypt.generate_password_hash(os.getenv('PW')),
        1
    ])
    db.commit()
    print("Admin user '%s' created." % userid)


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


def get_app_state():
    return {
        "gpio": gpio.get_all()
    }


def get_camera_by_name(name):
    # TODO: create camera table to translate camera name to cam
    return None


recently_used_cam = None
recently_used_camera = None


@app.route('/camera')
def get_image():
    global recently_used_cam, recently_used_camera
    camera_id = None
    if 'cam' in request.args:
        cam = request.args['cam']
        if re.match(ur'^/dev/video\d$', cam):
            camera_id = cam
        elif recently_used_cam == cam:
            camera_id = recently_used_camera
        else:
            camera_id = get_camera_by_name(cam)
            if camera_id is not None:
                recently_used_cam = cam
                recently_used_camera = camera_id
    filename = os.path.join(app.config['TMP_IMAGES_PATH'], 'live-%s.jpeg' % (int(time.time()) % 10))
    camera.get_webcam_image(filename, camera=camera_id, rotation=app.config['CAMERA_ROTATION'] if 'CAMERA_ROTATION' in app.config else None)
    return send_file(filename if os.path.exists(filename) else 'static/gdoor.jpg', mimetype='image/jpeg')


@app.route('/action/gdoor')
def action_gdoor():
    gpio.pulse(1)
    # TODO: schedule door check here
    return jsonify(**get_app_state())


@app.route('/action/light')
def action_light():
    gpio.toggle(2, max_duration=60*10)
    return jsonify(**get_app_state())


@app.route('/action/buzzer')
def action_buzer():
    gpio.pulse(3, duration=5)
    return jsonify(**get_app_state())


@app.route('/')
def home():
    cameras = OrderedDict(sorted(camera.get_webcams().items(), key=lambda item: item[1]['name']))
    return render_template('home.html', confirm_code=app.config['GDOOR_CODE'], cameras=cameras)


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
        try:
            cur = db.execute('select id, userid, pwhash, admin from user where userid = ?', [request.form['username']])
        except sqlite3.OperationalError, e:
            if e.message == 'no such table: user':
                return render_template('error.html', error_type='Initialization',
                                       error_message=e.message,
                                       error_help='You probably need to run initdb or configure the DATABASE path correctly',
                                       db_path=app.config['DATABASE'])
            else:
                raise
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


sys.stderr.write("All routes installed.\n")
app.logger.debug("All routes installed")
