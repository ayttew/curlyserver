import requests, json

host = 'http://localhost:5000'

def login(username, password):
	data = {'username' : username, 'password' : password}
	url = host + '/login'
	reques = requests.post(url, json = data)
	print (rq.content)
	return reques

def reg(username, password):
	data = {'username': username, 'password' : password}
	url = host + '/register'
	reques = requests.post(url, json = data)
	print (reques.content)
	return reques

def up(username, password, path):
	file = {'file' : open(path, mode='r')}
	data = {'username' : username, 'password' : password}
	url = host + '/upload'
	reques = requests.post(url, data = data, files = file)
	print (reques.content)
	return reques