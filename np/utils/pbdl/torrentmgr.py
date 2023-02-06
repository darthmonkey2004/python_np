from queue import Queue
from threading import Thread
import subprocess
from np.core.conf import readConf, writeConf
from np.core.log import np_logger
from np.utils.pbdl.torrentmgr_ui import *
from np.utils.pbdl.utils import get_torrents, get_files
import os
import json
import requests
log = np_logger().log_msg
public_ip = None



def get_public_ip():
	public_ip = None
	url = 'https://www.showmyip.com/'
	r = requests.get(url)
	data = r.text.split("\n")
	for line in data:
		if 'Your IPv4' in line:
			public_ip = line.split('<b>')[1].split('</b>')[0]
	return public_ip

def vpn_status():
	try:
		ret = subprocess.check_output(f"pgrep openvpn", shell=True).decode().strip().splitlines()
	except:
		ret = []
	if len(ret) == 1:
		vpn_state = True
	elif len(ret) > 1:
		log(f"WARNING: openvpn process running multiple times! {ret}", 'warning')
		vpn_state = True
	elif len(ret) == 0:
		vpn_state = False
	return vpn_state


def get_user_input(window_title='User Input', txt=None):
	user_input = None
	input_box = sg.Input(default_text='', enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	if txt is not None:
		input_txt = sg.Text(txt)
		layout = [[input_box], [input_txt], [input_btn]]
	else:
		layout = [[input_box], [input_btn]]
	input_window = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
	return user_input

def get_user_yn(window_title='Yes/No'):
	yes_btn = sg.Button(button_text='Yes', auto_size_button=True, pad=(1, 1), key='-YES-')
	no_btn = sg.Button(button_text='No', auto_size_button=True, pad=(1, 1), key='-NO-')
	layout = [[yes_btn], [no_btn]]
	input_window = sg.Window(window_title, layout, size=(300, 100), keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-YES-':
			user_input = True
			input_window.close()
		elif event == '-NO-':
			user_input = False
		user_input = user_input
		break
	return user_input


def ipinfo():
	ipinfo_api_token = '4d3f83adf329f8'
	com = f"curl \"ipinfo.io?token={ipinfo_api_token}\""
	try:
		ret = '{\n  "ip": "45.128.36.194",\n  "city": "Chicago",\n  "region": "Illinois",\n  "country": "US",\n  "loc": "41.8798,-87.6285",\n  "org": "AS9009 M247 Europe SRL",\n  "postal": "60603",\n  "timezone": "America/Chicago"\n}'
		#ret = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print(f"Error:{e}")
		ret = None
	print(ret)
	input()


class torrent_mgr():
	def __init__(self, win=None, remote_ip=None):
		self.win = win
		conf = readConf()
		self.start_paused = True
		self.do_not_seed = True
		try:
			self.settings = conf['pbdl']
		except:
			conf['pbdl'] = {}
			conf['pbdl']['remote_ip'] = get_user_input("Enter transmission ip: ")
			yn = get_user_yn("Start all torrents paused?")
			if yn == 'No':
				conf['pbdl']['start_paused'] = False
			else:
				conf['pbdl']['start_paused'] = True
			writeConf(conf)
			self.settings = conf['pbdl']
		if remote_ip == None:
			self.remote_ip = conf['pbdl_url']['remote_ip']
		else:
			self.remote_ip = remote_ip
		if self.settings['start_paused'] == False:
			self.set_start_unpaused()
		else:
			self.set_start_paused()
		self.set_global_ratio(0)
		self.user = os.path.expanduser("~").split('/home/')[1]
		self.public_ip = self.get_public_ip()
		if self.win is not None:
			self.win['-PUBLIC_IP-'].update(self.public_ip)
		self.vpn_thread = None
		self.vpn_state = self.vpn_status()
		self.monitor_q = Queue(maxsize=5)
		self.start_monitor()


	def set_remote_host(self, remote_ip=None):
		conf = readConf()
		if remote_ip == None:
			self.remote_ip = conf['pbdl_url']['remote_ip']
		else:
			self.remote_ip = remote_ip
			conf['pbdl_url']['remote_ip'] = self.remote_ip
			writeConf(conf)

	def set_transmission_ip(self, remote_ip=None):
		conf = readConf()
		if remote_ip is None:
			conf['pbdl_url']['remote_ip'] = get_user_input("IP Address:", "Enter remote transmission-rpc server address:")
		else:
			conf['pbdl_url']['remote_ip'] = remote_ip
		writeConf(conf)
		log(f"Updated transmision ip: {remote_ip}")
		

	def _vpn_status(self):
		com = f"nordvpn status | grep \"Status:\" | cut -d ' ' -f 4"
		try:
			status = subprocess.check_output(com, timeout=5, shell=True).decode().strip()
			if status == 'Disconnected':
				self.vpn_state = False
			else:
				self.vpn_state = True
		except Exception as e:
			log(f"Unable to get vpn status:{e}", 'error')
			self.vpn_state = False
		return self.vpn_state

	def get_user_input(self, window_title='User Input'):
		return get_user_input(window_title)


	def get_public_ip(self):
		url = 'https://www.showmyip.com/'
		r = requests.get(url)
		data = r.text.split("\n")
		for line in data:
			if 'Your IPv4' in line:
				self.public_ip = line.split('<b>')[1].split('</b>')[0]
				return self.public_ip


	def vpn_status(self):
		try:
			ret = subprocess.check_output(f"pgrep openvpn", shell=True).decode().strip().splitlines()
		except:
			ret = []
		if len(ret) == 1:
			self.vpn_state = True
		elif len(ret) > 1:
			log(f"WARNING: openvpn process running multiple times! {ret}", 'warning')
			self.vpn_state = True
		elif len(ret) == 0:
			self.vpn_state = False
		return self.vpn_state

	def _start_nordvpn(self):
		com = f"nordvpn connect"
		status = subprocess.check_output(com, shell=True).decode().strip()
		self.vpn_state = self.vpn_status()
		return status

	def _start_vpn(self):
		log(f"Starting torguard process...", 'info')
		com = f"cd /etc/openvpn; sudo openvpn torguard.ubuntu.chicago.ovpn"
		subprocess.check_output(com, shell=True)
			

	def ip_monitor(self, q):
		print("IP Monitor running!")
		self.run_monitor = True
		while self.run_monitor:
			self.vpn_state = vpn_status()
			self.public_ip = get_public_ip()
			if not q.full():
				q.put_nowait((self.vpn_state, self.public_ip))
			if self.win is not None:
				self.win['-PUBLIC_IP-'].update(self.public_ip)
				self.win['-TOGGLE_VPN-'].update(self.vpn_state)
		print("IP Monitor exited!")
		return


	def start_monitor(self):
		self.monitor_thread = Thread(target=self.ip_monitor, args=(self.monitor_q,))
		self.monitor_thread.setDaemon(True)
		self.monitor_thread.start()
		return self.monitor_thread


	def start_vpn(self):
		self.vpn_thread = Thread(target=self._start_vpn)
		self.vpn_thread.setDaemon(True)
		self.vpn_thread.start()
		print("VPN Client thread started!")
		return self.vpn_thread


	def _stop_vpn(self):
		try:
			self.stop_all()
		except:
			pass
		com = f"nordvpn disconnect"
		status = subprocess.check_output(com, shell=True).decode().strip()
		self.vpn_state = self.vpn_status()
		self.public_ip = self.get_public_ip
		return status

	def stop_vpn(self):
		try:
			subprocess.check_output(f"sudo kill $(pgrep openvpn)", shell=True)
			self.vpn_state = False
			self.public_ip = self.get_public_ip()
			return True
		except Exception as e:
			print("Couldn't kill torguard process:", e)
			return False

	def get_data(self):
		self.tdata = {}
		try:
			com=f"transmission-remote {self.remote_ip} -l | grep -v \"ID\" | grep -v \"Sum:\""
			results = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			tids = []
			for item in results:
				tid = item.strip().split(' ')[0]
				tids.append(tid)
		except Exception as e:
			log(f"pbdl.torrentmgr.get_data():Unable to get torrent data (no active torrents?) {e}", 'info')
			return self.tdata
		keys = ['Name', 'Hash', 'Magnet', 'State', 'Location', 'Percent Done', 'ETA', 'Download Speed', 'Upload Speed', 'Have', 'Total size', 'Downloaded', 'Uploaded', 'Ratio', 'Corrupt DL', 'Peers']
		dkeys = ['name', 'hash', 'magnet', 'state', 'location', 'percent', 'eta', 'download_speed', 'upload_speed', 'have', 'total_size', 'downloaded', 'uploaded', 'ratio', 'corrupt', 'peers']
		for tid in tids:
			self.tdata[tid] = {}
			com = f"transmission-remote {self.remote_ip} -t{tid} --info"
			data = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			for line in data:
				for key in keys:
					idx = keys.index(key)
					dkey = dkeys[idx]
					test = f"{key}: "
					if test in line:
						self.tdata[tid][dkey] = line.split(test)[1]
		return self.tdata


	def get_torrents(self):
		self.torrents = get_torrents()
		return self.torrents

	def get_files(self, tid):
		return get_files(tid)
	
	def start(self, tid):
		com=f"transmission-remote {self.remote_ip} -t{tid} -s"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def add(self, magnet):
		self.status = self.vpn_status()
		if self.status == True:
			pass
		else:
			self.start_vpn()
		if self.start_paused == True:
			self.set_start_paused()
		else:
			self.set_start_unpaused()
		self.start_all()
		com=f"transmission-remote {self.remote_ip} -a {magnet}"
		ret = subprocess.check_output(com, shell=True).decode().strip()
		self.stop_seeds()
		self.stop_all()
		return ret

	def stop(self, tid):
		com=f"transmission-remote {self.remote_ip} -t{tid} -S"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def start_all(self):
		j = "\n"
		out = []
		data = self.get_data()
		for tid in list(data.keys()):
			ret = self.start(tid)
			out.append(f"{tid}:{ret}")
		out = j.join(out)
		return out

	def stop_all(self):
		j = "\n"
		out = []
		data = self.get_data()
		for tid in list(data.keys()):
			ret = self.stop(tid)
			out.append(f"{tid}:{ret}")
		out = j.join(out)
		return out

	def set_global_ratio(self, ratio=0):
		com=f"transmission-remote {self.remote_ip} -gsr {ratio}"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def set_ratio(self, tid, ratio=0):
		com=f"transmission-remote {self.remote_ip} -t{tid} -sr {ratio}"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def stop_seeds(self):
		j = "\n"
		out = []
		self.set_global_ratio(0)
		data = self.get_data()
		for tid in list(data.keys()):
			ret = self.set_ratio(tid, 0)
			out.append(f"{tid}:{ret}")
		out = j.join(out)
		return out

	def set_start_paused(self):
		com=f"transmission-remote {self.remote_ip} --start-paused"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret
	
	def set_start_unpaused(self):
		com=f"transmission-remote {self.remote_ip} --no-start-paused"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def remove(self, tid):
		com=f"transmission-remote {self.remote_ip} -t{tid} -r"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def remove_and_delete(self, tid):
		com=f"transmission-remote {self.remote_ip} -t{tid} -rad"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def set_on_finished(self, script_path):
		if not os.path.exists(script_path):
			log("Error: Script file not found at {script_path}", 'error')
			return False
		com=f"transmission-remote {self.remote_ip} --torrent-done-script \"{script_path}\""
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def remove_on_finished(self):
		com=f"transmission-remote {self.remote_ip} --no-torrent-done-script"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def start_all_with_vpn(self, host=None):
		if host is not None:
			self.set_remote_host(host)
			log(f"Remote host set to '{host}'.", 'info')
		state = self.vpn_status()
		if state == False:
			log("VPN offline. Starting..", 'info')
			self.start_vpn()
			state = self.vpn_status()
			if state == True:
				log("VPN Active.", 'info')
			elif  state == False:
				log("Error: Unable to activate vpn. Aborting...", 'error')
				self.stop_all()
				return False
				
		self.start_all()
		self.stop_seeds()
		data = self.get_data()
		ct = len(list(data.keys()))
		pos = 0
		while True:
			if not self.monitor_q.empty():
				self.vpn_state, self.public_ip = self.monitor_q.get_nowait()
				self.monitor_q.task_done()

			for tid in data:
				percent = data[tid]['percent']
				if percent == '100%':
					pos += 1
			if ct == pos:
				pos = 0
			else:
				log(f"Progress: {pos} of {ct}", 'info')
				if not self.vpn_state:
					log(f"VPN not active! Restarting...", 'warning')
					self.start_vpn()
		self.stop_all()
		self.stop_vpn()
		log(f"All torrents finished! VPN deactivated.", 'info')
		return True
				
if __name__ == "__main__":
	import sys
	try:	
		remote_ip = sys.argv[1]
	except:
		remote_ip = input("Enter remote host ip: ")
	mgr = torrent_mgr()
	mgr.set_remote_host(remote_ip)
	mgr.start_all_with_vpn()
	
