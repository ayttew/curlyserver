from flask import Flask
import json, requests

# configuration
DEBUG = True
SERVER = 'http://192.168.1.104:5000'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('CURLYSERV_CONF', silent=True)

# Get list of files
def uploads(username, password):
	url = app.config['SERVER'] + '/listoffiles'
	data = {'username' : username, 'password' : password}
	requesting = requests.post(url, json=data)
	print requesting.content
	return requesting

# Upload 
def upload(username, password, file):
	file = {'file' : open(file, mode='r')}
	data = {'username' : username, 'password' : password}
	url = app.config['SERVER'] + '/upload'
	requesting = requests.post(url, data = data, files = file)
	print requesting.content
	return requesting

# Download file
def download(username, password, filename):
	args = {'username' : username, 'password' : password, 'filename' : filename}
	url = app.config['SERVER'] + '/download'
	requesting = requests.get(url, params=args, stream=True)
	return requesting

# Remove file from server
def remove_file(username, password, filename):
	url = app.config['SERVER'] + '/remove'
	data = {'username' : username, 'password' : password, 'filename' : filename}
	requesting = requests.post(url, data=data)
	return requesting

if __name__ == '__main__':
    app.run(host='0.0.0.0')