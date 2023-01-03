from np.utils.pbdl.downloader import start as dlstart
from urllib.parse import quote,unquote
from np.utils.pbdl.torrentmgr import *
import json
import requests
import subprocess
import PySimpleGUI as sg
from np.utils.pbdl.pbdl import start as mgr_start
win_x, win_y = None, None


def mk_torrent(filepath, target):
	com = f"transmission-create -o \"{filepath}\" \"{target}\" -t udp://tracker.coppersurfer.tk:6969/announce -t udp://tracker.openbittorrent.com:6969/announce -t udp://tracker.opentrackr.org:1337 -t udp://tracker.leechers-paradise.org:6969/announce -t udp://tracker.dler.org:6969/announce -t udp://opentracker.i2p.rocks:6969/announce -t udp://47.ip-51-68-199.eu:6969/announce -t udp://tracker.internetwarriors.net:1337/announce -t udp://9.rarbg.to:2920/announce -t udp://tracker.pirateparty.gr:6969/announce -t udp://tracker.cyberia.is:6969/announce"
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if 'done!' in ret:
		return True
	else:
		return False


def getlocalip():
	i = subprocess.check_output("ifconfig", shell=True).decode().strip().split('192.168.')[1].split(' ')[0]
	return f"192.168.{i}"

def getSessionId(transmission_remote_ip=None, transmission_remote_port=9091):
	if transmission_remote_ip is None:
		transmission_remote_ip = getlocalip()
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	data={"method":"session-get"}
	r = requests.post(url, data=data)
	headers = {}
	headers["X-Transmission-Session-Id"] = r.text.split('<code>')[1].split('</')[0].split(' ')[1]
	return headers

def post(com=None, transmission_remote_ip=None, transmission_remote_port=9091):
	if transmission_remote_ip is None:
		transmission_remote_ip = getlocalip()
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	headers = getSessionId()
	r = requests.post(url, json=com, headers=headers)
	if r.status_code == 200:
		json_data = json.loads(r.text)
		return json_data
	else:
		print(f"Failed to post to url: Status Code {r.status_code}, data={r.text}")
		return None


def get_torrents():
	com = {"method":"torrent-get","arguments":{"fields":["id","addedDate","name","totalSize","error","errorString","eta","isFinished","isStalled","leftUntilDone","metadataPercentComplete","peersConnected","peersGettingFromUs","peersSendingToUs","percentDone","queuePosition","rateDownload","rateUpload","recheckProgress","seedRatioMode","seedRatioLimit","sizeWhenDone","status","trackers","downloadDir","uploadedEver","uploadRatio","webseedsSendingToUs"]}}
	ret = post(com)
	keepers = ['addedDate', 'downloadDir', 'eta', 'id', 'isFinished', 'isStalled', 'name', 'peersConnected', 'percentDone', 'queuePosition', 'rateDownload', 'rateUpload', 'seedRatioLimit', 'seedRatioMode', 'status', 'totalSize', 'trackers', 'uploadRatio', 'uploadedEver']
	torrents = {}
	for t in ret['arguments']['torrents']:
		tid = t['id']
		torrents[tid] = {}
		for key in keepers:
			torrents[tid][key] = t[key]
	return torrents

def secs_to_mins(secs):
	mins = secs / 60
	secs = round(float(f".{round(float(str(mins).split('.')[1]))}") * 60)
	return mins, secs


def mins_to_hrs(mins):
	hrs = mins / 60
	mins = float(f".{str(hrs).split('.')[1]}") * 60
	secs = round(float(f".{str(mins).split('.')[1]}") * 60)
	mins = int(str(mins).split('.')[0])
	return hrs, mins, secs

def hrs_to_days(hrs):
	days = hrs / 24

def convert_eta(eta):
	mins, secs = secs_to_mins(eta)
	if mins > 60:
		hrs, mins, secs = mins_to_hrs(mins)
		if hrs > 24:
			
			days = hrs / 24
			r = float(f".{str(hrs).split('.')[1]}")
			days = float(str(days).split('.')[0])
			hrs = round(r * 60)
			hrs = r * 24
			days = round(days)
			hrs = round(hrs)
			return f"{days} days, {hrs} hours"
		else:
			mins = round(mins)
			secs = round(secs)
			hrs = round(hrs)
			return f"{hrs}:{mins}:{secs}"
	else:
		mins = round(mins)
		secs = round(secs)
		return f"0:{mins}:{secs}"


def convert_rate(rate):
	kb = round(rate / 1024)
	if kb <= 1000:
		return f"{kb} KBps"
	else:
		mb = round(kb / 1024)
		if mb <= 1000:
			return f"{mb} MBps"
		else:
			gb = round(mb / 1024)
			return f"{gb} GBps"

def update_info(data=None):
	if data is None:
		data = get_torrents()
	info = {}
	for tid in data.keys():
		percent = round(float(data[tid]['percentDone']) * 100, 2)
		eta = convert_eta(data[tid]['eta'])
		rate = convert_rate(data[tid]['rateDownload'])
		s = int(data[tid]['status'])
		if s == 0:
			status = 'Stopped'
		elif s == 1:
			print("Status unknown! 1")
		elif s == 2:
			print("Status unknown! 2")
		elif s == 3:
			status = f"Queued:{data[tid]['queuePosition']}"
		elif s == 4:
			status = 'Downloading'
		
		string = f"Status:{status}, Percent:{percent}%, ETA:{eta}, Download Rate:{rate}, Peers:{data[tid]['peersConnected']}, Name:{data[tid]['name']}"
		info[tid] = string
	return info


def gui(info):
	try:
		win_x, win_y = load_win_location()
	except:
		win_x, win_y = 510, 1000
		save_win_location(win_x, win_y)
	layout = []
	#torrent_info_box = [sg.Listbox([], select_mode = None, change_submits = True, enable_events = True, size = (None, None), auto_size_text = True, key = '-TORRENT_INFO-', expand_x = True, expand_y = True)]
	torrent_info_box = []
	for tid in list(info.keys()):
		line = [sg.Radio(tid, key=f"-{tid}-", group_id=0, enable_events=True), sg.Text(key=f"info-{tid}")]
		torrent_info_box.append(line)
	torrent_info_box.append(sg.Radio('all', key='-ALL-', group_id=0, enable_events=True))
	layout.append(torrent_info_box)
	magnet_line = [sg.Button('Add'), sg.Input('Enter magnet link here:', key='-MAGNET-', enable_events=True)]
	layout.append(magnet_line)
	buttons = [sg.Button('Start!'), sg.Button('Stop'), sg.Button('Remove'), sg.Button('Delete'), sg.Button('Downloader'), sg.Button('Manager')]
	layout.append(buttons)
	win = sg.Window(title='Torrent Info', layout=layout, size = (900, 200), location = (win_x, win_y))
	win.finalize()
	return win

def add(magnet, paused=False, download_dir="/var/lib/transmission-daemon/downloads"):
	com = {}
	com['method'] = "torrent-add"
	com['arguments'] = {}
	if not paused:
		paused = 'false'
	elif paused:
		paused = 'true'
	com['arguments']['paused'] = paused
	com['arguments']['download-dir'] = download_dir
	com['arguments']['filename'] = magnet
	post(com)


def start():
	global win_x, win_y
	t = torrent_mgr()
	info = update_info()
	print(info)
	try:
		win_x, win_y = load_win_location()
		win = gui(info)
	except:
		win = gui(info)
		win_x, win_y = win.current_location()
		save_win_location(win_x, win_y)
	return t, info, win, win_x, win_y


def load_win_location(filepath='/home/monkey/.np/tmgr_location.txt'):
	with open(filepath, 'r') as f:
		win_x, win_y = f.read().split(':')
		f.close()
	print("Window location loaded!", win_x, win_y)
	return int(win_x), int(win_y)

def save_win_location(x, y, filepath='/home/monkey/.np/tmgr_location.txt'):
	with open(filepath, 'w') as f:
		data = f"{x}:{y}"
		f.write(data)
		f.close()
	print("Window location saved!", x, y)
#com = {"method":"session-stats"}

#data = {"method":"torrent-stop","arguments":{"ids":[2]}}
def run_ui():
	t, info, win, win_x, win_y = start()
	pos = 0
	ct = 500
	active = None
	magnet = None
	while True:
		pos += 1
		window, event, values = sg.read_all_windows(timeout=1)
		if event != '__TIMEOUT__':
			print(event, values)
			if event == 'Start!':
				if active is None:
					t.start_all()
					print("Started all!")
				else:
					t.start(active)
					print("Started id:", active)
			elif event == 'Stop':
				if active is None:
					t.stop_all()
					print("Stopped all!")
				else:
					t.stop(active)
					print("Stopped id:", active)
			elif event == '-MAGNET-':
				magnet = unquote(values[event])
				win['-MAGNET-'].update(magnet)
			elif event == 'Add':
				add(magnet)
				print("adding magnet:", magnet)
				win.close()
				t, info, win, win_x, win_y = start()
			elif event == 'Delete':
				if active is not None:
					t.remove_and_delete(active)
					print("Deleted id (plus data):", active)
					win.close()
					t, info, win, win_x, win_y = start()
				else:
					print("Cannot delete all!")
			elif event == 'Remove':
				if active is not None:
					t.remove(active)
					print("Removed id:", active)
					win.close()
					t, info, win, win_x, win_y = start()
				else:
					print("cannot remove all!")

			elif event == 'Downloader':
				dlwin = dlstart()
				win.close()
				t, info, win, win_x, win_y = start()
			elif event == 'Manager':
				mgr_start()
			elif event == sg.WIN_CLOSED:
				win_x, win_y = win.current_location()
				save_win_location(win_x, win_y)
				break
			else:
				try:
					active = int(event.split('-')[1])
					print("Selected:", active)
				except Exception as e:
					print("can't parse key:", e, "event:", event)
		if pos == ct:
			pos = 0
			info = update_info()
			for tid in info.keys():
				try:
					key = f"-{tid}-"
					win[f"info-{tid}"].update(info[tid])
				except Exception as e:
					print("Error updating window:", e)
	win.close()


if __name__ == "__main__":
	run_ui()
