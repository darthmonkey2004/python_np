import pickle
import sys, traceback
import os
from np.utils.pbdl.utils import get_torrents, get_files, test_media_type, test_media, parse_series, parse_movies, lookup, verify_series_name, build_data, merge_saved_data, save_data, load_saved_data, clear_data, set_api_key_tmdb, set_api_key_rt, add_to_db, migrate
from np.utils.pbdl.torrentmgr import torrent_mgr
from np.utils.pbdl.ty_isin import ty_isin
from np.utils.pbdl.se_isin import se_isin
from np.utils.pbdl.search import get_url, search
from np.utils.pbdl.rotten_tomatoes import get_episode_data, get_season_data, get_all_series_data, get_seasons, get_movie_data
from np.utils.pbdl.query_series import query_series
from np.utils.pbdl.query_movies import query_movies
from np.core.nplayer_db import get_columns
from np.core.conf import readConf, writeConf
from np.core.log import np_logger
from np.utils.pbdl.torrentmgr_ui import *
from np.utils.pbdl.downloader import start as start_downloader
from np.utils.pbdl.downloader import create_downloader, get_location
log = np_logger().log_msg
	


def set_empty(table='movies'):
	pragma = get_columns(table)
	columns = list(pragma.keys())
	info = {}
	for key in columns:
		dtype = pragma[key]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			info[key] = 0
		elif dtype == 'TEXT':
			info[key] = 'Unknown'
	return info


def crash_detected():
	log(f"Previous crash detected!", 'warning')

class pbdl():
	def __init__(self):
		self.conf = readConf()
		self.info = {}
		self.media_dir = self.conf['media_directories']['main']
		self.music_dir = self.conf['media_directories']['music']
		self.series_dir = self.conf['media_directories']['series']
		self.movies_dir = self.conf['media_directories']['movies']
		self.data_dir = os.path.join(os.path.expanduser("~"), '.np')
		self.play_type = self.conf['play_type']
		self.windows = {}
		self.win = None
		self.mgr = torrent_mgr()
		self.exit_ok = self.conf['exit_ok']
		self.exit = False
		self.event = None
		self.window = None
		self.values = {}
		self.torrents = build_data()
		tids = list(self.torrents.keys())
		try:
			self.tid = tids[0]
		except:
			self.tid = 0
		try:
			self.torrent = self.torrents[self.tid]
		except:
			self.torrent = None
		try:
			self.name = self.torrent['name']
		except:
			self.name = None
		self.selected_files = []
		self.vpn_status = self.mgr.vpn_status()
		self.lookup_type = '-TMDB-'
		self.filepath = None
		if not self.exit_ok:
			crash_detected()
		self.exit_ok = False
		try:
			self.mgr_location = self.conf['locations']['mgr']
			self.dl_location = self.conf['locations']['dl']
		except:
			self.mgr_location = (0, 0)
			self.dl_location = (0, 0)
			self.conf['locations'] = {}
			self.conf['locations']['mgr'] = self.mgr_location
			self.conf['locations']['dl'] = self.dl_location
			writeConf(self.conf)



	def get_field_from_key(self, key):
		columns = list(get_columns(self.play_type).keys())
		try:
			return columns[int(key.split('column')[1])]
		except Exception as e:
			log(f"Error: Couldn't get field from key: {e}, key:{key}", 'error')
			return None


	def shit_fire(self, save="sweaty aardvarks", matches="Mad Libs - The Movie"):
		log(f"Easter bunny just excreted some {save}, if you'd like to purchase some with a side of {matches}...", 'warning')
		

	def create_downloader(self):
		return create_downloader()


	def quit(self):
		log(f"Exiting, updating conf: {self.conf.keys()}", 'info')
		self.conf['exit_ok'] = True
		self.conf['locations'] = {}
		self.conf['locations']['mgr'] = self.mgr_location
		self.conf['locations']['dl'] = self.dl_location
		self.save_data(self.torrents)
		try:
			self.mgr_location = self.windows['Torrent Manager'].current_location()
		except:
			self.mgr_location = self.conf['locations']['mgr']
		for win in self.windows.keys():
			self.windows[win].close()
		self.conf['locations']['mgr'] = self.mgr_location

		writeConf(self.conf)

	def save_data(self, torrents=None):
		if torrents == None:
			torrents = self.torrents
		log(f"Saving current data!", 'info')
		savefile = os.path.join(self.data_dir, 'pbdl.dat')
		try:
			with open(savefile, "wb") as f:
				pickle.dump(torrents, f)
			f.close()
			if self.conf['debug'] == True:
				log(f"Torrent log updated.", 'info')
			return True
		except Exception as e:
			log(f"Error: Unable to write torrent log {e}: data: {torrents}", 'error')
			return False

	def update_media_type(self, play_type=None):
		if play_type == None:
			self.play_type = self.win.AllKeysDict['-MEDIA_TYPE-'].Get()
		else:
			self.play_type = play_type
		columns = list(get_columns(self.play_type).keys())
		idx = -1
		for idx in range(0, 14):
			try:
				column = columns[idx]
				key = f"-dbcolumn{idx}-"
				bkey = f"dbcolumn{idx}"
				self.win[bkey].update('Unknown')
				self.win[key].update(column)
			except:
				column = "None"
		self.win['-MEDIA_TYPE-'].update(play_type)
		self.win.refresh()

	def start_downloader(self):
		#light weight self contained downloader, separate from main loop (blocks main ui until finished.
		title = 'PBDL Downloader'
		#TODO: See if i can find a way to have downloader exit remove itself from self.windows
		win = create_downloader()
		self.dl_location = win.current_location()
		self.windows[win.Title] = win
		win = start_downloader(self.mgr, win)

	def create_torrentmgr_ui(self):
		#creates pbdl ui (runs in main loop)
		win = create_torrentmgr_ui()
		self.mgr_location = win.current_location()
		log(f"Created torrent manager: ({win.Title})", 'info')
		self.windows[win.Title] = win

	def read_windows(self):
		try:
			self.win, self.event, self.values = sg.read_all_windows(timeout=1)
		except Exception as e:
			log(f"Exit exception:{e}", 'error')


	def display_torrents(self, torrents=None):
		if torrents == None:
			torrents = merge_saved_data()
		self.torrents = torrents
		self.active_torrents = []
		for tid in torrents:
			name = self.torrents[tid]['name']
			string = f"{tid}:{name}"
			self.active_torrents.append(string)
		try:
			self.windows['Torrent Manager']['-TORRENT_SELECT-'].update(self.active_torrents)
		except Exception as e:
			log(f"pbdl.display_torrents():Unable to update torrent list! (empty???). Details: {e}", 'warning')


	def refresh(self):
		t = get_torrents()
		self.display_torrents(t)

def start(t='mgr'):
	log(f"TODO: Change save_data/load_data to only save 'files' key in torrents for each torrent id (specifically info), so load does't overwrite currently refreshed torrent data.", 'info')
	log(f"TODO: Update merge_data to not overwrite torremt info (surface keys).", 'info')
	log(f"TODO: Set while loop to poll and auto-refresh torrent data every few seconds.", 'info')
	columns_keys = ['dbcolumn0', 'dbcolumn1', 'dbcolumn2', 'dbcolumn3', 'dbcolumn4', 'dbcolumn5', 'dbcolumn6', 'dbcolumn7', 'dbcolumn8', 'dbcolumn9', 'dbcolumn10', 'dbcolumn11', 'dbcolumn12', 'dbcolumn13']
	p = pbdl()
	if t == 'mgr':
		p.create_torrentmgr_ui()
		log(f"Loading torrents.. please wait!", 'info')
		p.torrents = build_data(rebuild=True)
		p.display_torrents()
		while True:
			p.read_windows()
			window, event, values = p.window, p.event, p.values
			if event == '__TIMEOUT__':
				pass
			elif p.exit == True or event == '-QUIT_PBDL-' or event == 'Exit':
				log(f"EVENT:{event}", 'info')
				p.quit()
				break
			elif event == sg.WIN_CLOSED:
				log(f"EVENT:{event}", 'info')
				title = window.Title
				p.windows.remove(title)
				if len(p.windows) == 0:
					log(f"Exiting (self.win empty!)", 'info')
					#p.quit()
					break
			elif event in columns_keys:
				log(f"EVENT:{event}", 'info')
				val = values[event]
				if val is not None:
					log(f"COLUMN CHANGE: ({event})={values[event]}", 'info')
					field = p.get_field_from_key(event)
					p.info[field] = val
					p.torrents[p.tid]['files'][p.filepath]['info'] = p.info
					save_data(p.torrents)
					log(f"(Updated torrent ({p.tid}): {field}={val}", 'info')
				else:
					log(f"COLUMN CHANGE: Skipped field update (value is Null):field={field}, val={val}, tid={tid}", 'info')
			elif event == '-TORRENT_SELECT-':
				log(f"EVENT:{event}", 'info')
				string = values[event][0]
				p.tid = int(string.split(':')[0])
				p.torrent = p.torrents[p.tid]
				p.name = string.split(':')[1]
				p.torrent_files = p.mgr.get_files(p.tid)
				p.win['-TORRENT_FILES-'].update(p.torrent_files)
				sg.fill_form_with_values(p.win, p.torrent)
			elif event == '-START_TORRENT-':
				log(f"EVENT:{event}:Starting torrent (id={p.tid})", 'info')
				ret = p.mgr.start(p.tid)
				log(f"EVENT:{event}:Results={ret}", 'info')
			elif 'VPN' in event:
				log(f"VPN : {event}", 'info')
				if event == 'VPN Status':
					p.vpn_status = p.mgr.vpn_status()
					log(f"VPN Status: {p.vpn_status}", 'info')
				elif event == 'VPN Off':
					ret = p.mgr.stop_vpn()
					if ret:
						log(f"VPN Enable: {ret}", 'info')
				elif event == 'VPN On':
					ret = p.mgr.start_vpn()
					if ret:
						log(f"VPN Disable: {ret}", 'info')
			elif event == '-TORRENT_FILES-':
				p.selected_files = values[event]
				log(f"EVENT:{event}", 'info')
				if len(p.selected_files) == 1:
					filepath = p.selected_files[0]
					p.filepath = filepath
					p.play_type = test_media(filepath)
					p.update_media_type(p.play_type)
					columns = list(get_columns(p.play_type).keys())
					try:
						p.info = p.torrents[p.tid]['files'][filepath]['info']
						hasinfo = True
					except Exception as e:
						log (f"No info found in torrent data for file {filepath} ({e})", 'warning')
						p.info = set_empty(p.play_type)
						hasinfo = False
					if hasinfo is False:
						if p.play_type == 'series':
							series_name, season, episode_number = test_media(filepath, True)
							p.info = set_empty('series')
							p.info['series_name'] = series_name
							p.info['season'] = season
							p.info['episode_number'] = episode_number
						elif p.play_type == 'movies':
							title, year = test_media(filepath, True)
							p.info = set_empty('movies')
							p.info['title'] = title
							p.info['year'] = year
					d = {}
					for item in list(p.info.keys()):
						if item in columns:
							k = f"dbcolumn{columns.index(item)}"
							if "'" in str(p.info[item]):
								p.info[item] = str(p.info[item]).replace("'", "")
							d[k] = p.info[item]
							log(f"item:{item}, k:{k}", 'info')
					sg.fill_form_with_values(p.win, d)
					p.win['dbcolumn0'].update(p.tid)
					p.win[f"dbcolumn{columns.index('filepath')}"].update(filepath)
			elif event == '-LOOKUP_TYPE-':
				log(f"EVENT:{event}", 'info')
				p.lookup_type = p.win[event].get()
				log(f"Set lookup type to {p.lookup_type}", 'info')
			elif event == '-LOOKUP-':
				log(f"EVENT:{event}", 'info')
				log(f"info:{p.info}", 'info')
				p.info['lookup_type'] = p.lookup_type
				p.info['play_type'] = p.play_type
				fidx = list(get_columns(p.play_type).keys()).index('filepath')
				key = f"dbcolumn{fidx}"
				ret = lookup(p.info)
				if ret is None:
					log(f"Lookup failed for {p.info}", 'info')
				try:
					worked = ret['results']
				except:
					worked = False
				if worked:
					p.info = ret
					p.info['filepath'] = p.win[key]
					columns = list(get_columns(p.play_type).keys())
					for k in list(p.info.keys()):
						if k in columns:
							p.win[f"dbcolumn{columns.index(k)}"].update(p.info[k])
					log(f"Updated menu!", 'info')
				else:
					log(f"Found no results!", 'warning')
			elif event == '-MEDIA_TYPE-' or event == 'series' or event == 'movies' or event == 'music':
				if event == 'series' or event == 'movies' or event == 'music':
					p.play_type = event
				elif event == '-MEDIA_TYPE-':
					p.play_type = values[event]
				p.update_media_type(p.play_type)
				log(f"Media type changes:{p.play_type}", 'info')
			elif event == 'Refresh Torrents' or event == '-REFRESH_DATA-':
				p.torrents = merge_saved_data()
				p.display_torrents()
				log(f"Torrents updated and merged!", 'info')
			elif event == 'Load':
				p.torrents = load_saved_data()
				p.display_torrents()
				log(f"Loaded saved data! (Refresh skipped)", 'info')
			elif event == 'Save' or event == '-SAVE_INFO-':
				save_data(p.torrents)
				log(f"Data saved!", 'info')
			elif event == 'Clear Data':
				p.torrents = clear_data()
				p.display_torrents()
				log(f"Data cleared!", 'info')
			elif event == 'Add To Sql':
				log(f"Adding files to database...", 'info')
				add_to_db(p.torrents)
				log(f"Ok!", 'info')
			elif event == 'Add Torrent':
				log(f"EVENT:{event}", 'info')
				try:
					magnet = p.mgr.get_user_input("Enter magnet link:")
					ret = p.mgr.add(magnet)
					if ret:
						log(f"TORRENTMGR:Add magnet:{ret}", 'info')
				except Exception as e:
					log("Unable to add magnet: {e}", 'error')
			elif event == 'Remove':
				log(f"EVENT:{event}", 'info')
				ret = p.mgr.remove(p.tid)
				if ret:
					log(f"TORRENTMGR:Remove (no delete):{ret}", 'info')
			elif event == 'Remove and Delete' or event == 'Remove+Delete':
				log(f"EVENT:{event}", 'info')
				ret = p.mgr.remove_and_delete(p.tid)
				if ret:
					log(f"TORRENTMGR:Remove and Delete:{ret}", 'info')
				p.torrents = merge_saved_data()
				p.display_torrents()
			elif event == 'Stop All':
				log(f"EVENT:{event}", 'info')
				ret = p.mgr.stop_all()
				if ret:
					log(f"TORRENTMGR:Stop All:{ret}", 'info')
			elif event == 'Start All':
				log(f"EVENT:{event}", 'info')
				ret = p.mgr.start_all()
				if ret:
					log(f"TORRENTMGR:Start All:{ret}", 'info')
			elif event == 'Set Remote Host':
				log(f"EVENT:{event}", 'info')
				ret = p.mgr.set_transmission_ip()
				if ret:
					log(f"TORRENTMGR:Start All:{ret}", 'info')
			elif event == 'View Downloader':
				log(f"Starting downloader!", 'info')
				p.start_downloader()
			elif event == 'Set Wait Task':
				log(f"EVENT:{event}", 'info')
				ret = p.mgr.start_all_with_vpn()
				if ret:
					log(f"TORRENTMGR:Start All:{ret}", 'info')
			elif event == 'Set Api Key:Rotten Tomatoes':
				set_api_key_rt()
			elif event == 'Set Api Key:Search TMDB':
				set_api_key_tmdb()
			elif event == '-Migrate Files-' or event == 'Migrate Data':
				migrate()
							
			else:
				log(f"UNHANDLED_EVENT:{event}", 'info')
				try:
					val == values[event]
				except:
					val = None
				log(f"values: {val}", 'info')
		merge_saved_data()
		p.display_torrents()
	elif t == 'dl':
		p.start_downloader()


if __name__ == "__main__":
	start()
