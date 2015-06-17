import os
import shutil
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    flash
from werkzeug.utils import secure_filename
from contextlib import closing
from werkzeug import utils, secure_filename

# configuration
DATABASE = '/tmp/curlyserver.db'
DEBUG = True
SECRET_KEY = 'dev key'
ROOT_USERNAME = 'admin'
ROOT_PASSWORD = 'admin'
STORAGE = '/tmp/curlyserver'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('CURLYSERV_CONF', silent=True)
# Connection to database
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def try_login(username, password):
    db = connect_db()
    us = db.execute('select username from users where exists (select * from users where (username) = (?))',
            [username])
    if us is None:
        return False
    else:
        ps = db.execute('select password from users where username = (?)',
                [username])
        ps = ps.fetchone()[0]
        if ps == password: 
            return True
        else:
            return False

def get_space(username):
    db = connect_db()
    cur = db.cursor()
    space = cur.execute('select storage from users where username = (?)', [username])
    space = space.fetchone()[0]
    used_space = cur.execute('select used_storage from users where username = (?)', [username])
    used_space = used_space.fetchone()[0]
    return (space - used_space)

# Check if you can upload file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# Main upload function
@app.route('/upload', methods=['POST'])
def upload():
    username = request.form.get('username')
    password = request.form.get('password')
    if try_login(username, password):
        file = request.files['file']
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        if file_length <= get_space(username):
            filename = secure_filename(file.filename)
            file.save(os.path.join(os.path.join(app.config['STORAGE'], username), filename))
            db = connect_db()
            used_space = db.execute('select used_storage from users where username = (?)', [username])
            used_space = used_space.fetchone()[0]
            used_space = used_space + file_length
            db.execute('update users set used_storage = (?) where username = (?)', [used_space, username])
            db.commit()
            return 'Success!'
        else:
            return 'You do not have enough space!'
    else:
        return 'Error authorization'

# Check if user is root
@app.route('/root_login', methods = ['POST'])
def root_login():
    
	if username == app.config['ROOT_USERNAME'] and password == app.config['ROOT_PASSWORD']:
		return 
    else:
        flash ('Wrong username')

# Main login function
@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    db = get_db()
    if root_login(username, password):
        session['logged_in'] = True
        session['username'] = username
        return 'Logged in as administrator'
    else:
        us = db.execute('select username from users where exists (select * from users where (username) = (?))',
            [username])
        us = us.fetchone()
        if us is None:
            return 'Wrong username'
        else:
            db = db.cursor()
            ps = db.execute('select password from users where username = (?)',
                [username])
            ps = ps.fetchone()[0]
            if ps == password:
                session['logged_in'] = True
                session['username'] = username
                return 'Logged in as user'
            else:
                return 'Wrong password'

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return True

@app.route('/register', methods = ['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    db = connect_db()
    try:
        db.execute('insert into users (username, password) values (?, ?)', [username, password])
        db.commit()
        os.mkdir(os.path.join(app.config['STORAGES'], username))
    except sqlite3.IntegrityError:
        return 'Username already exists'
    return 'Registration is successful'

@app.route('/logged_in')
def logged_in():
    if session['logged_in']:
        return 'Yes'
    else:
        return 'No'

if __name__ == '__main__':
    app.run(host='0.0.0.0')