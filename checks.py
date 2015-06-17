import requests, json

host = 'http://localhost:5000'

def login(username, password):
	data = {'username' : username, 'password' : password}
	url = host + '/login'
	rq = requests.post(url, json = data)
	print (rq.content)
	return rq

def reg(username, password):
	data = {'username': username, 'password' : password}
	url = host + '/register'
	rq = requests.post(url, json = data)
	print (rq.content)
	return rq

def up(username, password, path):
	file = {'file' : open(path, mode='r')}
	data = {'username' : username, 'password' : password}
	url = host + '/upload'
	rq = requests.post(url, data = data, files = file)
	print (rq.content)
	return rq