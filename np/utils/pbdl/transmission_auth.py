import json
import subprocess
import os
from np.core.conf import readConf
from np.core.core import get_local_ip

conf = readConf()

def shell(com):
	try:
		out = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print("Error running command:", e)
		return None
	if out == '':
		out = None
	elif "\n" in out:
		out = out.splitlines()
	else:
		out = [out]
	return out


def send(com, user=None, remote_ip=None):
	if user is None:
		user = os.getlogin()
	if remote_ip is None:
		remote_ip = conf['pbdl']['remote_ip']
	com = f"ssh {user}@{remote_ip} \"{com}\""
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret == '':
		ret = None
	return ret
	

def service_is_running():
	status = send("sudo service transmission-daemon status > /home/monkey/temp.txt; cat temp.txt").splitlines()
	for line in status:
		if 'Active:' in line:
			if 'active (running)' in line:
				return True
			elif 'inactive (dead)' in line:
				return False
		
def backup_settings():
	backups = send("cd /etc/transmission-daemon; sudo ls *.json* | grep -v \"settings.json\" | grep -v \"README\"").splitlines()
	fname = f"settings.bak.json.{len(backups) + 1}"
	path = os.path.join('etc', 'transmission-daemon', fname)
	send(f"sudo cp /etc/transmission-daemon/settings.json /etc/transmission-daemon/{fname}")

def push_settings(data, user=None, remote_ip=None):
	if user is None:
		user = os.getlogin()
	if remote_ip is None:
		remote_ip = conf['pbdl']['remote_ip']
	fname = 'temp.settings.json'
	with open(fname, "w") as f:
		json.dump(data, f)
		f.close()
	com = f"scp {fname} {user}@{remote_ip}:/home/{user}/{fname}"
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		print("Error pushing file:", ret)
		return False
	else:
		ret = send(f"sudo mv /home/monkey/temp.settings.json /etc/transmission-daemon/settings.json")
		if ret is not None and ret != '':
			print("Error pushing data:", ret)
			return False
	return True


def authorize():
	backup_settings()
	if service_is_running():
		send("sudo service transmission-daemon stop")
	data = json.loads(send("sudo cat /etc/transmission-daemon/settings.json"))
	keys = ['rpc-host-whitelist', 'rpc-whitelist']
	for key in keys:
		hosts = data[key]
		if ',' in hosts:
			hosts = hosts.split(',')
		else:
			hosts = [hosts]

		localip = get_local_ip()
		if localip not in hosts:
			hosts.append(localip)

		hosts = ",".join(hosts)
		data[key] = hosts
	push_settings(data)
	send("sudo service transmission-daemon start")

if __name__ == "__main__":
	authorize()

