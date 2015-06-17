import os
import shutil
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, send_from_directory
from datetime import datetime
from werkzeug.utils import secure_filename
from contextlib import closing
from werkzeug import utils

# configuration
DATABASE = '/tmp/curlyserver.db'
DEBUG = True
SECRET_KEY = 'dev key'
ROOT_USERNAME = 'admin'
ROOT_PASSWORD = 'admin'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('CURLYSERV_CONF', silent=True)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()



# Check if user is root
@app.route('/root_login', methods = ['POST'])
def root_login(username, password):
	if username == app.config['ROOT_USERNAME'] and password == app.config['ROOT_PASSWORD']:
		return True
	return False

@app.route('/login', methods=['GET', 'POST'])
def login():
	username = request.json.get('username')
	password = request.json.get('password')
	db = connect_db()
	if root_login(username, password):
		session['user'] = username
		return 'Logged in as administrator'
	else:
		us = db.execute('select * from users where username = (?)', [username])
		if us is None:
			return 'Wrong username'
		elif us['password'] != password:
			return 'Invalid password'
		else:
			session['user_id'] = username
			return 'Logged in as user'

if __name__ == '__main__':
    app.run(host='0.0.0.0')