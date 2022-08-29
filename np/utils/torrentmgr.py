import subprocess
from np import readConf,HOME,writeConf,log


class torrent_mgr():
	def __init__(self):
		self.remote_ip = None
		self.user = HOME.split('/home/')[1]

	def set_remote_host(self, remote_ip=None):
		conf = readConf()
		if remote_ip == None:
			self.remote_ip = conf['pbdl_url']
		else:
			self.remote_ip = remote_ip
			conf['pbdl_url'] = self.remote_ip
			writeConf(conf)
		

	def vpn_status(self):
		com = f"nordvpn status | grep \"Status:\" | cut -d ' ' -f 4"
		status = subprocess.check_output(com, shell=True).decode().strip()
		if status == 'Disconnected':
			return False
		else:
			return True


	def start_vpn(self):
		com = f"nordvpn connect"
		status = subprocess.check_output(com, shell=True).decode().strip()
		return status

	def stop_vpn(self):
		com = f"nordvpn disconnect"
		status = subprocess.check_output(com, shell=True).decode().strip()
		return status

	def get_data(self):
		com=f"transmission-remote {self.remote_ip} -l | grep -v \"ID\" | grep -v \"Sum:\""
		results = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		tids = []
		for item in results:
			tid = item.strip().split(' ')[0]
			tids.append(tid)
		self.tdata = {}
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
	
	def start(self, tid):
		com=f"transmission-remote {self.remote_ip} -t{tid} -s"
		ret = subprocess.check_output(com, shell=True).decode().strip().split('"')[1]
		return ret

	def add(self, magnet):
		com=f"transmission-remote {self.remote_ip} -t{tid} -a {magnet}"
		ret = subprocess.check_output(com, shell=True).decode().strip().split(':')[1].split('"')[1]
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
		while True:
			pos = 0
			for tid in data:
				percent = data[tid]['percent']
				if percent == '100%':
					pos += 1
			if ct == pos:
				print (f"Done! ({pos} of {ct})")
				break
			else:
				print (f"Progress: {pos} of {ct}")
				status = self.vpn_status()
				if status == False:
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
	
