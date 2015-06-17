import os
import shutil
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    flash, render_template
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

def get_files(username):
    files = os.listdir(os.path.join(app.config['STORAGE'], username))
    if not files:
        return False
    else:
        return files

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
            return 'OK'
        else:
            return 'ME'
    else:
        return 'AE'


# Functions for administration purposes
@app.route('/')
def show_users():
    db = connect_db()
    cur = db.execute('select username, storage, used_storage from users order by id asc')
    users = [dict(username=row[0], storage=row[1], used_storage=row[2]) for row in cur.fetchall()]
    return render_template('show_users.html', users=users)

def change_space(username, new_value):
    db = connect_db()
    db.execute('update users set storage = (?) where username = (?)', [new_value, username])

@app.route('/change_space/<username>', methods=['POST'])
def change(username):
    db = connect_db()
    value = int(request.form['bytes'])
    db.execute('update users set storage = (?) where username = (?)', [value, username])
    return redirect(url_for('show_users'))

# Administrator login function
@app.route('/root_login', methods=['GET', 'POST'])
def root_login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['ROOT_USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['ROOT_PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in as admin')
            return redirect(url_for('show_users'))
    return render_template('login.html', error=error)

# Administrator logout function
@app.route('/root_logout')
def root_logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_users'))

# Add new user through the form
@app.route('/add_user', methods=['POST'])
def add_user():
    uname = request.form['username']
    db = connect_db()
    try:
        db.execute('insert into users (username, password) values (?, ?)',
            [uname, request.form['password']])
        db.commit()
        os.mkdir(os.path.join(app.config['STORAGE'], uname))
        return redirect(url_for('show_users'))
    except sqlite3.IntegrityError:
        flash('This username already exists')
        return redirect(url_for('show_users'))

@app.route('/show_files', methods=['POST'])
def show_files():
    us = request.form['user']
    if not get_files(us):
        return render_template('show_files.html', [])
    else:
        return render_template('show_files.html', get_files(us))

# Remove existing user
@app.route('/remove_user', methods=['POST'])
def remove_user():
    uname = request.form['username']
    db = connect_db()
    db.execute('delete from users where (username) = (?)', uname)
    db.commit()
    shutil.rmtree(os.path.join(app.config['STORAGE'], uname))
    return redirect(url_for('show_users'))

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

# interfaces for contacting with client
# Sign in
@app.route('/signin', methods=['POST'])
def Nsignin():
    username = request.json.get('username')
    password = request.json.get('password')
    db = connect_db()
    if try_login(username, password):
        return True
    else:
        return False

# Get list of files
@app.route('/listoffiles', methods=['GET', 'POST'])
def Nlistoffiles():
    username = request.json.get('username')
    password = request.json.get('password')
    if try_login(username, password):
        if get_files(username) == []:
            return 'No files'
        else:
            l = get_files(username)
            for a in l:
                print a
            return 'List of all files is above.'


@app.route('/download', methods=['POST'])
def Ndownload():
    username = request.args.get('username')
    password = request.args.get('password')
    file = request.args.get('file')

    if try_login(username, password):
        return send_from_directory(os.path.join(app.config['STORAGE'], username), file)
    else:
        return 'AE'

@app.route('/remove', methods=['POST'])
def Nremove():
    username = request.form.get('username')
    password = request.form.get('password')
    filename = request.form.get('filename')
    
    db = connect_db()

    path = os.path.join(app.config['STORAGE'], username)
    path = os.path.join(path, filename) 
    
    filesize = os.stat(path)
    filesize = filesize.st_size

    if try_login(username, password):
        if os.path.exists(path):
            os.remove(path)
            used_space = db.execute('select used_storage from users where username = (?)', [username])
            used_space = used_space.fetchone()[0]
            used_space = used_space + filesize
            db.execute('update users set used_storage = (?) where username = (?)', [filesize, username])
            db.commit()
        return 'No such file'
    return 'Login is incorrect'


if __name__ == '__main__':
    app.run(host='0.0.0.0')