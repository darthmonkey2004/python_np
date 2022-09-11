import json
import PySimpleGUI as sg
import requests
import os.path
from np.utils.xrandr import xrandr
import urllib
from np.utils.pbdl.se_isin import parse as se_isin
from np.core.nplayer_db import get_columns
from np.core.log import np_logger
logger = np_logger().log_msg
from np.core.conf import readConf, writeConf
conf = readConf()


def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)



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
	


def set_api_key_tmdb():
	conf = readConf()
	api_key = get_user_input("Enter TMDB api key:")
	try:
		haskeys = conf['api_keys']
	except:
		conf['api_keys'] = {}
		log(f"Api keys not found in conf! Adding...", 'warning')
	conf['api_keys']['TMDB'] = api_key
	writeConf(conf)
	log(f"Updated TMDB API Key: {api_key}", 'info')
	return api_key


try:
	haskeys = conf['api_keys']
	API_KEY = conf['api_keys']['TMDB']
except:
	API_KEY = set_api_key_tmdb()



def set_empty():
	pragma = get_columns('movies')
	columns = list(pragma.keys())
	info = {}
	for key in columns:
		dtype = pragma[key]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			info[key] = 0
		elif dtype == 'TEXT':
			info[key] = 'Unknown'
	info['results'] = False
	return info


def query_series(series_name, season, episode_number):
	info = set_empty()
	info['series_name'] = str(series_name)
	info['season'] = int(season)
	info['episode_number'] = int(episode_number)
	series_name_nw = urllib.parse.quote(series_name)
	global API_KEY
	url = ("https://api.themoviedb.org/3/search/tv?api_key=" + str(API_KEY) + "&language=en-US&query=" + series_name_nw)
	r = requests.get(url)
	if r.status_code != 200:
		out = ("Error:", r.status_code)
		return out
	data = r.text
	json_data = json.loads(data)
	try:
		tmdbid = json_data['results'][0]['id']
	except Exception as e:
		print ("Error getting tmdbid:", e)
	try:
		still_path = json_data['results'][0]['backdrop_path']
	except Exception as e:
		print ("Still path was error:", e)
		try:
			still_path = json_data['results'][0]['poster_path']
		except:
			still_path = 'No image found'
	try:
		if "'" in json_data['results'][0]['name']:
			temp = json_data['results'][0]['name']
			temp = temp.split("'")
			j = "_"
			json_data['results'][0]['name'] = j.join(temp)
		url = "https://api.themoviedb.org/3/tv/" + str(tmdbid) + "/season/" + str(season) + "/episode/" + str(episode_number) + "?api_key=" + str(API_KEY) + "&language=en-US"
		r = requests.get(url)
		if r.status_code != 200:
			out = ("Error:", r.status_code, "URL:", url)
			info['error'] = True
			info['response'] = out
			info['filepath'] = filepath
			info['tmdbid'] = tmdbid
			info['series_name'] = series_name
			info['season'] = season
			info['episode_number'] = episode_number
			info['episode_name'] = 'Unknown'
			info['description'] = 'Unknown'
			info['air_date'] = 'Unknown'
			info['still_path'] = 'Unknown'
			info['duration'] = 'Unknown'
			info['md5'] = 'Unknown'
			info['url'] = url
			info['results'] = False
			return info
		else:
			data = r.text
			json_data = json.loads(data)
			out = ("OK:", r.status_code, "URL:", url)
			info['response'] = out
			info['error'] = False
			info['tmdbid'] = tmdbid
			info['series_name'] = series_name
			info['season'] = season
			info['episode_number'] = episode_number
			info['episode_name'] = json_data['name']
			info['description'] = json_data['overview']
			info['air_date'] = json_data['air_date']
			info['still_path'] = json_data['still_path']
			info['duration'] = 'null'
			info['md5'] = 'null'
			info['url'] = url
			info['results'] = True
			return info
	except Exception as e:
		out = ("Error:{e}", 'error')
		info['error'] = True
		info['response'] = out
		info['tmdbid'] = 'Unknown'
		info['series_name'] = series_name
		info['season'] = season
		info['episode_number'] = episode_number
		info['episode_name'] = 'Unknown'
		info['description'] = 'Unknown'
		info['air_date'] = 'Unknown'
		info['still_path'] = 'Unknown'
		info['duration'] = 'Unknown'
		info['md5'] = 'Unknown'
		info['url'] = url
		info['results'] = False
		return info


if __name__ == "__main__":
	import sys
	filepath = str(sys.argv[1])
	data = lookup(filepath)
	print (data)
	exit()
