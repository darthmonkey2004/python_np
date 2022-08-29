#!/usr/bin/env python3

#NOTE: This is not my creation, I just found it useful and modified it to fit my needs.
#You can find the original websocket_server at 'https://github.com/Pithikos/python-websocket-server.git'

import time
import np
import subprocess
from np.ws.websocket_server import WebsocketServer
conf = np.readConf()

# Called for every client connecting (after handshake)
def new_client(client, server):
	add, port = client['address']
	client['mac'] = get_mac(add)
	update_client(client)
	_id = client['id']
	mac = client['mac']
	#server.send_message_to_all(f"DEVICE_CONNECT:({_id}@{add} (MAC={mac})")
	np.log(f"DEVICE_CONNECTED:{_id}:{add}:{port}:{mac}", 'info')

# Called for every client disconnecting
def client_left(client, server):
	add, port = client['address']
	_id = client['id']
	mac = client['mac']
	np.log(f"DEVICE_CONNECTED:{_id}:{add}:{port}:{mac}", 'info')


# Called when a client sends a message
def message_received(client, server, message):
	add, port = client['address']
	_id = client['id']
	mac = client['mac']
	if len(message) > 200:
		message = message[:200]+'..'
	ret = remote_exec(message)
	if ret is None:
		ret = "Ok"
	server.send_message(client, ret)

def get_mac(ip=None):
	localip = get_localip()
	mac = None
	if ip == None:
		return None
	elif ip == '127.0.0.1' or ip == localip:
		com = (f"ifconfig")
		ret = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		for i in ret:
			if 'ether' in i:
				mac = i.strip().split(' ')[1]
				return mac
	else:
		com = (f"ping -c 1 {ip}")
		ret = subprocess.check_output(com, shell=True).decode().strip()
	com = (f"arp -n {ip}")
	string = subprocess.check_output(com, shell=True).decode().strip().split(' ')
	for chunk in string:
		if ':' in chunk:
			mac = chunk
			return mac

def get_localip():
	com = (f"ifconfig")
	ret = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for i in ret:
		if 'inet' in i and '192.168' in i:
			ret = i
	return ret.strip().split(' ')[1]


def remote_exec(com):
	remote_commands = ['create_viewer', 'help', 'commands', 'play', 'create_gui', 'close_gui', 'close_viewer', 'pause', 'stop', 'skip_next', 'skip_prev', 'vol_set', 'vol_up', 'vol_down', 'mute', 'unmute', 'quit', 'load', 'play_mode', 'play_type', 'seek', 'move_gui', 'move_player', 'get_pos', 'get_window_location', 'media_pick', 'media_get', 'debug']
	ret = None
	with open(np.COMFILE, "w") as f:
		f.write(com)
	f.close()
	time.sleep(1)
	response = []
	with open(np.LOGFILE, "r") as f:
		data = f.read().split("\n")
	f.close()
	for item in data:
		if 'REMOTE: ' in item:
			response.append(item)
	if len(response) > 0:
		ct = len(response) - 1
		ret = response[ct]
		s = 'REMOTE: '
		_list = ret.split(s)
		ct = len(_list) - 1
		ret = _list[ct]
		np.log(f"EVENT: Remote command executed: '{com}'", 'info')
	else:
		ret = None
	return ret



def update_client(client):
	idx =  server.clients.index(client)
	server.clients[idx] = client

def start():
	global server
	try:
		server = WebsocketServer()
		server.set_fn_new_client(new_client)
		server.set_fn_client_left(client_left)
		server.set_fn_message_received(message_received)
		state = conf['remote']['server']['state']
		if state == 0:
			np.log(f"Server running at '127.0.0.1' (state={state}) on port {conf['remote']['server']['port']}", 'info')
		elif state == 1:
			np.log(f"Server running at {conf['remote']['server']['address']} (state={state}) on port {conf['remote']['server']['port']}", 'info')
		server.run_forever()
	except Exception as e:
		np.log(f"Exception running server: {e}. (Already running?)", 'warning')

if __name__ == "__main__":
	start()
