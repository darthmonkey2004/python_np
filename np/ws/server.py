#!/usr/bin/env python3

#NOTE: This is not my creation, I just found it useful and modified it to fit my needs.
#You can find the original websocket_server at 'https://github.com/Pithikos/python-websocket-server.git'

import time
import queue
from np.core.log import np_logger
from np.core.conf import readConf
import subprocess
from np.ws.websocket_server import WebsocketServer
conf = readConf()
logger = np_logger().log_msg

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)


class server():
	def __init__(self, com_q, ret_q):
		self.com_q = com_q
		self.ret_q = ret_q
		self.clients = {}
		self.localip = self.get_localip
		self.message = None
		try:
			self.server = WebsocketServer()
			self.server.set_fn_new_client(self.new_client)
			self.server.set_fn_client_left(self.client_left)
			self.server.set_fn_message_received(self.message_received)
		except Exception as e:
			log(f"Exception running server: {e}. (Already running?)", 'warning')



	# Called for every client connecting (after handshake)
	def new_client(self, client, server):
	
		client = client
		add, port = client['address']
		mac = self.get_mac(add)
		client['mac'] = mac
		self.update_client(client)
		_id = client['id']
		self.server.send_message_to_all(f"DEVICE_CONNECT:({_id}@{add} (MAC={mac})")
		log(f"DEVICE_CONNECTED:{_id}:{add}:{port}:{mac}", 'info')

# Called for every client disconnecting
	def client_left(self, client, server):
		add, port = client['address']
		_id = client['id']
		mac = client['mac']
		log(f"DEVICE_DISCONNECTED:{_id}:{add}:{port}:{mac}", 'info')


	# Called when a client sends a message
	def message_received(self, client, server, message):
		add, port = client['address']
		_id = client['id']
		mac = client['mac']
		if len(message) > 200:
			message = message[:200]+'..'
		ret = self.remote_exec(client, message)
		
		self.message = message

	def get_mac(self, ip=None):
		mac = None
		if ip == None:
			return None
		elif ip == '127.0.0.1' or ip == self.localip:
			com = (f"ifconfig")
			ret = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			for i in ret:
				if 'ether' in i:
					mac = i.strip().split(' ')[1]
					return mac
		else:
			try:
				com = (f"ping -c 1 {ip}")
				ret = subprocess.check_output(com, shell=True).decode().strip()
			except Exception as e:
				log(f"Ping shell command failed for {ip}:{e}", 'error')
				pass
		try:
			com = (f"arp -n {ip}")
			string = subprocess.check_output(com, shell=True).decode().strip().split(' ')
			for chunk in string:
				if ':' in chunk:
					mac = chunk
					return mac
		except Exception as e:
			log(f"Unable to get mac address for ip {ip}:{e}", 'error')
			mac = 'Unknown'
			return mac

	def get_localip(self):
		com = (f"ifconfig")
		ret = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		for i in ret:
			if 'inet' in i and '192.168' in i:
				ret = i
				break
		self.localip = ret.strip().split(' ')[1]
		return self.localip


	def remote_exec(self, client, com):
		if com is not None:
			log(f"EVENT: Remote command executed: '{com}'", 'info')
			remote_commands = ['create_viewer', 'help', 'commands', 'play', 'create_gui', 'close_gui', 'close_viewer', 'pause', 'stop', 'skip_next', 'skip_prev', 'vol_set', 'vol_up', 'vol_down', 'mute', 'unmute', 'quit', 'load', 'play_mode', 'play_type', 'seek', 'move_gui', 'move_player', 'get_pos', 'get_window_location', 'media_pick', 'media_get', 'debug']
			ret = None
			self.com_q.put(com)
			response = self.ret_q.get()
			self.server.send_message(client, response)
			if response is not None:
				log(f"EVENT: Remote command response: '{response}'", 'info')	
		else:
			log(f"server.py, command is None! {com}", 'warning')



	def update_client(self, client):
		client = client
		idx = self.server.clients.index(client)
		self.server.clients[idx] = client
		self.clients = self.server.clients

	def start(self):
		state = conf['remote']['server']['state']
		if state == 0:
			log(f"Server running at '127.0.0.1' (state={state}) on port {conf['remote']['server']['port']}", 'info')
		elif state == 1:
			log(f"Server running at {conf['remote']['server']['address']} (state={state}) on port {conf['remote']['server']['port']}", 'info')
		self.server.run_forever()

if __name__ == "__main__":
	s = server()
	s.start()
