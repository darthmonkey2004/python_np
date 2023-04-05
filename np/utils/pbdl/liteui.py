import math
from np.core.conf import readConf
from np.utils.pbdl.utils import migrate_series, migrate_movies, test_sftp_mount, mount_sftp, test_media
from np.utils.pbdl.query_series import query_series
from np.utils.pbdl.query_movies import query_movies
from np.utils.pbdl.search import search
from np.core.conf import *
from np.core.core import shell
from urllib.parse import quote,unquote
from np.utils.pbdl.torrentmgr import *
import json
import requests
import subprocess
import PySimpleGUI as sg
from np.utils.pbdl.pbdl import start as mgr_start
from np.core.log import np_logger
from np.utils.pbdl.ty_isin import *
import os
log = np_logger().log_msg
win_x, win_y = None, None
conf = readConf()
DATA_DIR = os.path.join(os.path.expanduser("~"), '.np')
SFTP_DIR = os.path.join(DATA_DIR, 'sftp')
HOME = os.path.expanduser("~")

def ssh(com):
	remote_ip = conf['pbdl']['remote_ip']
	user = os.getlogin()
	com = f"ssh {user}@{remote_ip} \"{com}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print("Error in ssh command:", e)
		ret = []
	if ret is not None:
		if "\n" in ret:
			ret = ret.splitlines()
		elif ret == '':
			ret = None
	return ret


class pbdl():
	def __init__(self, transmission_ip=None, start_paused=True):
		self.t = torrent_mgr()
		self.conf = readConf()
		self.media_dir = self.conf['media_directories']['movies']
		db = os.path.join(DATA_DIR, 'nplayer.db')
		if transmission_ip is None:
			transmission_ip = self.conf['pbdl']['remote_ip']
		self.transmission_ip = transmission_ip
		if start_paused is None:
			start_paused = self.conf['pbdl']['start_paused']
		self.start_paused = start_paused
		self.torrents = self.t.torrents
		self.windows = {}
		self.info = None
		self.win = None
		self.win_x = None
		self.win_y = None
		self.series = []
		self.movies = []
		self.tid = 'All'
		self.query = None
		self.results = None

	def mk_torrent(self, filepath, target):
		com = f"transmission-create -o \"{filepath}\" \"{target}\" -t udp://tracker.coppersurfer.tk:6969/announce -t udp://tracker.openbittorrent.com:6969/announce -t udp://tracker.opentrackr.org:1337 -t udp://tracker.leechers-paradise.org:6969/announce -t udp://tracker.dler.org:6969/announce -t udp://opentracker.i2p.rocks:6969/announce -t udp://47.ip-51-68-199.eu:6969/announce -t udp://tracker.internetwarriors.net:1337/announce -t udp://9.rarbg.to:2920/announce -t udp://tracker.pirateparty.gr:6969/announce -t udp://tracker.cyberia.is:6969/announce"
		ret = shell(com)
		if 'done!' in ret:
			return True
		else:
			return False

	def migrate(self, tid=None):
		if tid is None:
			tid = 'All'
		self.tid = tid
		log(f"Migrating ids:{self.tid}", 'info')
		self.t.migrate(self.tid)


	def getlocalip(self):
		i = subprocess.check_output("ifconfig", shell=True).decode().strip().split('192.168.')[1].split(' ')[0]
		return f"192.168.{i}"

	def getSessionId(self, transmission_remote_ip=None, transmission_remote_port=9091):
		return self.t.getSessionId()

	def post(self, com=None, transmission_remote_ip=None, transmission_remote_port=9091):
		return self.t.post(com)

	def get_files(self, tid, transmission_remote_ip=None, transmission_remote_port=9091):
		return self.t.get_files()




	def get_series_info(self, filepath, window_title='Enter Series Info', series_name=None, episode_number=None, season=None):
		#might  need sn, s, and en set in ui class???
		return self.t.get_series_info(series_name=series_name, season=season, episode_number=episode_number)


	def save_downloads(dl_data=None, datfile=None):
		if dl_data is None:
			dl_data = get_downloads()
		if datfile is None:
			datfile = os.path.join(os.path.expanduser("~"), '.np', 'downloads.dat')
		with open(datfile, 'wb') as f:
			pickle.dump(dl_data, f)
			f.close()

	def load_downloads(datfile=None):
		if datfile is None:
			datfile = os.path.join(os.path.expanduser("~"), '.np', 'downloads.dat')
		with open(datfile) as f:
			dl_data = pickle.load(f)
			f.close()
		return dl_data


	def get_movie_info(self, filepath, title=None, year=None, window_title='Enter Series Info'):
		layout = []
		user_input = None
		fname_line = [sg.Text(filepath)]
		title_line = [sg.Text('Title'), sg.Input(default_text=title, enable_events=True, change_submits=True, do_not_clear=True, key='-TITLE-', expand_x=True)]
		year_line = [sg.Text('Year'), sg.Input(default_text=year, enable_events=True, change_submits=True, do_not_clear=True, key='-YEAR-', expand_x=True)]
		output_line = [sg.Text('', key='-OUTPUT-')]
		submit = [sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-SUBMIT-')]
		layout.append(fname_line)
		layout.append(title_line)
		layout.append(year_line)
		layout.append(output_line)
		layout.append(submit)
		win_key = window_title.lower().replace(' ', '_')
		win = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
		self.windows[win_key] = win
		while True:
			event, values = win.read()
			if event == sg.WIN_CLOSED:
				del self.windows[win_key]
				break
			elif event == '-SUBMIT-':
				if year is None:
					year = 0000
				if title is not None:
					win.close()
				else:
					win['-OUTPUT-'].update('Error: Ensure all fields complete before continuing!')
			elif event == '-TITLE-':
				title = values[event]
				win['-OUTPUT-'].update(f"title set:{title}!")
			elif event == '-YEAR-':
				try:
					year = int(values[event])
					win['-OUTPUT-'].update(f"Year set:{year}!")
				except Exception as e:
					win['-OUTPUT-'].update(f"Error setting year:{e}!")
					year = None
		return title, year


	def get_play_type(self, filepath):
		fname = os.path.basename(filepath)
		log(f"self.get_play_type running...", 'info')
		layout = []
		window_title = 'Select play type:'
		fname_line = [sg.Text(f"Setting info for:{fname}...")]
		play_type_combo = [sg.Combo(['series', 'movies', 'music'], 'series', enable_events=True,key='-PLAY_TYPE-')]
		layout.append(play_type_combo)
		layout.append(fname_line)
		win_key = window_title.lower().replace(' ', '_')
		win = sg.Window(window_title, layout, size=(650, 120), keep_on_top=False, element_justification='center', finalize=True)
		self.windows[win_key] = win
		data = None
		while True:
			event, values = win.read()
			if event == sg.WIN_CLOSED:
				del self.windows[win_key]
				break
			else:
				play_type = values[event]
				win.close()
		log(f"play_type:{play_type}", 'info')
		return play_type



	def secs_to_mins(self, secs):
		mins = secs / 60
		secs = round(float(f".{round(float(str(mins).split('.')[1]))}") * 60)
		return mins, secs


	def mins_to_hrs(self, mins):
		hrs = mins / 60
		mins = float(f".{str(hrs).split('.')[1]}") * 60
		secs = round(float(f".{str(mins).split('.')[1]}") * 60)
		mins = int(str(mins).split('.')[0])
		return hrs, mins, secs

	def hrs_to_days(self, hrs):
		days = hrs / 24

	def convert_eta(self, eta):
		mins, secs = self.secs_to_mins(eta)
		if mins > 60:
			hrs, mins, secs = self.mins_to_hrs(mins)
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


	def convert_rate(self, rate):
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


	def convert_size(self, size_bytes):
		if size_bytes == 0:
			return "0B"
		size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
		i = int(math.floor(math.log(size_bytes, 1024)))
		p = math.pow(1024, i)
		s = round(size_bytes / p, 2)
		return "%s %s" % (s, size_name[i])


	def update_info(self, data=None):
		info = {}
		self.torrents = self.t.get_torrents()
		for tid in self.torrents.keys():
			percent = round(float(self.torrents[tid]['percentDone']) * 100, 2)
			eta = self.convert_eta(self.torrents[tid]['eta'])
			rate = self.convert_rate(self.torrents[tid]['rateDownload'])
			s = int(self.torrents[tid]['status'])
			status = 'Stopped'
			if s == 0:
				status = 'Stopped'
			elif s == 1:
				log("Status unknown! 1", 'warning')
			elif s == 2:
				log("Status unknown! 2", 'warning')
			elif s == 3:
				status = f"Queued:{self.torrents[tid]['queuePosition']}"
			elif s == 4:
				status = 'Downloading'
			size = self.convert_size(int(self.torrents[tid]['totalSize']))
			string = f"Status:{status}, Percent:{percent}%, ETA:{eta}, Download Rate:{rate}, Peers:{self.torrents[tid]['peersConnected']}, Size:{size}, Name:{self.torrents[tid]['name']}"
			info[tid] = string
		return info


	def gui(self, info):
		try:
			win_x, win_y = self.load_win_location()
		except Exception as e:
			log("pbdl.gui():Error = {e}", 'error')
			win_x, win_y = 510, 1000
			self.save_win_location(win_x, win_y)
		layout = []
		results = []
		play_type_combo = [sg.Combo(['series', 'movies', 'music'], self.conf['play_type'] , enable_events=True,key='-DL_MEDIA_TYPE-'), sg.Checkbox(text="VPN On/Off", auto_size_text=True, change_submits=True, enable_events=True, key='-TOGGLE_VPN-'), sg.Checkbox(text="Remove on migrate:", auto_size_text=True, change_submits=True, enable_events=True, key='-REMOVE_ON_MIGRATE-'), sg.Text('Public IP Address:'), sg.Text('', key='-PUBLIC_IP-')]
		layout.append(play_type_combo)
		search_line = [sg.Text('Enter search query here:'), sg.Input('', enable_events=True, change_submits=True, key='-PBDL_SEARCH_QUERY-', expand_x=True), sg.Button('Search', key='-PBDL_SEARCH-'), sg.Button('Quit!', key='-DOWNLOADER_EXIT-')]
		layout.append(search_line)
		results_box = [sg.Listbox(values=results, change_submits=True, size = (200, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-PBDL_RESULTS-')]
		layout.append(results_box)
		#torrent_info_box = [sg.Listbox([], select_mode = None, change_submits = True, enable_events = True, size = (None, None), auto_size_text = True, key = '-TORRENT_INFO-', expand_x = True, expand_y = True)]
		torrent_info_box = []
		for tid in list(info.keys()):
			line = [sg.Radio(tid, key=f"-{tid}-", group_id=0, enable_events=True), sg.Text(key=f"info-{tid}")]
			torrent_info_box.append(line)
		torrent_info_box.append(sg.Radio('all', key='-ALL-', group_id=0, enable_events=True))
		layout.append(torrent_info_box)
		magnet_line = [sg.Text('Enter magnet link here:'), sg.Input('', key='-MAGNET-', enable_events=True), sg.Button('Add')]
		layout.append(magnet_line)
		buttons = [sg.Button('Start!'), sg.Button('Stop'), sg.Button('Remove'), sg.Button('Delete'), sg.Button('Manager'), sg.Button('Migrate Files')]
		layout.append(buttons)
		output_box = [sg.Multiline(default_text = "", enter_submits = True, disabled = False, autoscroll = True, border_width = None, size = (200, 40), auto_size_text = None, background_color = None, text_color = None, horizontal_scroll = False, change_submits = False, enable_events = False, do_not_clear = True, key = '-OUTPUT-', write_only = False, auto_refresh = False, reroute_stdout = False, reroute_stderr = False, reroute_cprint = False, echo_stdout_stderr = False, justification = 'left', no_scrollbar = False, expand_x = False, expand_y = False, rstrip = True)]
#		output_box = [sg.Multiline(default_text = "", enter_submits = True, disabled = False, autoscroll = True, border_width = None, size = (200, 40), auto_size_text = None, background_color = None, text_color = None, horizontal_scroll = False, change_submits = True, enable_events = True, do_not_clear = True, key = '-OUTPUT-', write_only = False, auto_refresh = True, reroute_stdout = True, reroute_stderr = True, reroute_cprint = True, echo_stdout_stderr = True, justification = 'left', no_scrollbar = False, expand_x = False, expand_y = False, rstrip = True)]
		layout.append(output_box)
		self.win = sg.Window(title='Torrent Info', layout=layout, size = (1100, 600), location = (win_x, win_y))
		self.windows['main'] = self.win
		self.win.finalize()
		return self.win

	def add(self, magnet, paused=False, download_dir="/var/lib/transmission-daemon/downloads"):
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
		self.post(com)

	def start(self):
		global win_x, win_y
		info = None
		try:
			info = self.update_info()
			log(f"pbdl.start():Info = '{info}'", 'info')
		except Exception as e:
			log(f"pbdl.start():Error updating info:{e}", 'error')
		try:
			win_x, win_y = self.load_win_location()
			self.win = self.gui(info)
		except Exception as e:
			log(f"pbdl.start():Error - {e}", 'error')
			self.win = self.gui(info)
			win_x, win_y = win.current_location()
			self.save_win_location(win_x, win_y)
		if self.results is not None:
			self.win['-PBDL_RESULTS-'].update(self.results)
		if self.query is not None:
			self.win['-PBDL_SEARCH_QUERY-'].update(self.query)
		return info, self.win, win_x, win_y

	def load_win_location(self, filepath='/home/monkey/.np/tmgr_location.txt'):
		with open(filepath, 'r') as f:
			win_x, win_y = f.read().split(':')
			f.close()
		log(f"Window location loaded! x={win_x}, y={win_y}", 'info')
		return int(win_x), int(win_y)

	def save_win_location(self, x, y, filepath='/home/monkey/.np/tmgr_location.txt'):
		with open(filepath, 'w') as f:
			data = f"{x}:{y}"
			f.write(data)
			f.close()
		log(f"Window location saved! x={x}, y={y}", 'info')
		#com = {"method":"session-stats"}

	def send(self, com):
		com = f"{com} 2>/dev/null"
		print("com:", com)
		try:
			#ret = subprocess.check_output(com, timeout=2, shell=True).decode().strip()
			ret = ssh(com)
			if ret == '':
				ret = None
				return ret
		except Exception as e:
			print("Command failed:", e)
			return None


	def get_gateway(self):
		return self.send("dig +short myip.opendns.com @resolver1.opendns.com")


	#def test_vpn_status(self):
	#	return self.t.vpn_status()


	def test_vpn(self):
		return self.t.vpn_status()


	def check_active_downloads(self):
		for tid in self.torrents.keys():
			status = int(self.torrents[tid]['status'])
			if status != 0:
				return True
			else:
				pass
		return False

	def ensure_safe_downloads(self, t, win):
		have_active = self.check_active_downloads()
		if have_active:
			vpn_active = self.test_vpn()
			win['-TOGGLE_VPN-'].update(vpn_active)
			if not vpn_active:
				log(f"VPN not enabled and torrents are downloading! Executing stop all...", 'warning')
				t.stop_all()
				return False
			else:
				return True
		else:
			return True


def update(p):
	info = p.update_info()
	for tid in info.keys():
		try:
			key = f"-{tid}-"
			p.win[f"info-{tid}"].update(info[tid])
		except Exception as e:
			log("Error updating window: {e}", 'error')


#data = {"method":"torrent-stop","arguments":{"ids":[2]}}
def run_ui(pbdl_obj=None):
	if pbdl_obj is None:
		global pbdl
		p = pbdl()
	else:
		p = pbdl_obj
	t = torrent_mgr()
	info, win, win_x, win_y = p.start()
	win['-TOGGLE_VPN-'].update(t.vpn_status())
	pos = 0
	ct = 1500
	ct2 = 4500
	magnet = None
	exit = False
	update(p)
	tid = None
	while True:
		if exit:
			win_x, win_y = win.current_location()
			p.save_win_location(win_x, win_y)
			break
		pos += 1
		window, event, values = sg.read_all_windows(timeout=1)
		if event != '__TIMEOUT__':
			#print("event:", event)
			if event == 'Start!':
				if p.tid is None:
					t.start_all()
					log("Started all!", 'info')
				else:
					t.start(p.tid)
					log("Started id: {p.tid}", 'info')
			elif event == 'Stop':
				if p.tid is None:
					t.stop_all()
					log("Stopped all!", 'info')
				else:
					t.stop(p.tid)
					log("Stopped id: {p.tid}", 'info')
			elif event == '-MAGNET-':
				magnet = unquote(values[event])
				win['-MAGNET-'].update(magnet)
			elif event == 'Add':
				p.add(magnet)
				log(f"adding magnet: {magnet}", 'info')
				win.close()
				info, win, win_x, win_y = p.start()
			elif event == 'Delete':
				if p.tid is not None:
					t.remove_and_delete(p.tid)
					log(f"Deleted id (plus data): {p.tid}", 'info')
					win.close()
					info, win, win_x, win_y = p.start()
				else:
					log("Cannot delete all!", 'warning')
			elif event == 'Remove':
				if p.tid is not None:
					t.remove(p.tid)
					log(f"Removed id: {p.tid}", 'info')
					win.close()
					info, win, win_x, win_y = p.start()
				else:
					log(f"cannot remove all!", 'warning')
			elif event == 'Manager':
				mgr_start()
			elif event == sg.WIN_CLOSED or event=='-Close PBDL-' or event == "Exit" or event == '-DOWNLOADER_EXIT-':
				exit = True
			elif event == '-DL_MEDIA_TYPE-':
				play_type = values[event]
				log(f"Play type set: {play_type}", 'info')
			elif event == '-PBDL_SEARCH-':
				log(f"p.downloader():searching {pbdl_query}...", 'info')
				results = search(p.query)
				p.results = results
				window['-PBDL_RESULTS-'].update(p.results)	
			elif event == '-PBDL_SEARCH_QUERY-':
				pbdl_query = values[event]
				p.query = pbdl_query
			elif event == '-TOGGLE_VPN-':
				#state = t.vpn_status()
				state = window['-TOGGLE_VPN-'].get()
				print(event, state)
				if state:
					log("Starting vpn...", 'info')
					t.start_vpn()
					log("VPN Started!", 'info')
				else:
					log("Stopping vpn...", 'info')
					t.stop_vpn()
					log("VPN Stopped!", 'info')
			elif event == '-PBDL_RESULTS-':
				try:
					picked = values[event][0]
					log(f"p.downloader():Downloading:{picked}", 'info')
					magnet = results[picked]['magnet']
					magnet = unquote(magnet)
					win['-MAGNET-'].update(magnet)
				except Exception as e:
					log(f"p.downloader():list empty? {e}", 'error')
			elif event == 'Migrate Files':
				p.migrate(p.tid)
				if p.t.remove_on_migrate:
					win.close()
					info, win, win_x, win_y = p.start()
			elif event == 'VID_OUT':
				pass
			elif event == '-ALL-':
				p.tid = 'all'
				log("Selected: 'all'...", 'info')
			elif event == '-REMOVE_ON_MIGRATE-':
				p.t.remove_on_migrate = values[event]
				log(f"Set remove on migrate:{p.t.remove_on_migrate}", 'info')
			else:
				for tid in list(p.torrents.keys()):
					k = f"-{tid}-"
					if k == event:
						p.tid = int(event.split('-')[1])
						log(f"Tid selected:{p.tid}", 'info')
						break
				else:
					log(f"Unhandled event: {event}, values:{values}", 'debug')
		if pos == ct:
			win['-PUBLIC_IP-'].update(t.get_public_ip())
			update(p)
			p.ensure_safe_downloads(t, win)
			pos = 0
		#win.refresh()
	win.close()




if __name__ == "__main__":
	p = pbdl()
	run_ui(p)
