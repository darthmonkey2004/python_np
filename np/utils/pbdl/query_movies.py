import traceback, sys
import urllib
import requests
import json
from np.core.log import np_logger
log = np_logger().log_msg
import time
from np.core.nplayer_db import get_columns
import PySimpleGUI as sg
from np.core.conf import readConf
conf = readConf()

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



def query_movies(title):
	info = set_empty()
	info['title'] = title
	attempts = 0
	log (f"Looking up movie... Title: '{title}'", 'info')
	title_nw = urllib.parse.quote(title)
	global API_KEY
	tmdb_url = (f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&language=en-US&query={title_nw}&page=1&include_adult=false")
	r = requests.get(tmdb_url)
	if r.status_code != 200:
		log(f"TMDB Query Error: Response code {r.status_code}", 'error')
		return info
	try:
		data = None
		json_data = json.loads(r.text)
		ret = json_data['results']
		for i in range(len(ret)):
			if title == ret[i]['title']:
				data = ret[i]
				#log(f"query_movies():Results={data}", 'info')
				break
		errmsg = None
		if data is None:
			data = json_data['results'][0]
		info['title'] = data['title']
		info['year'] = data['release_date'].split('-')[0]
		info['tmdbid'] = data['id']
		info['description'] = data['overview']
		info['poster'] = data['poster_path']
		info['results'] = True
		return info
	except Exception as e:
		log("Error: {e}", 'error')
		return info


if __name__ == "__main__":
	import sys
	try:
		title = sys.argv[1]
	except:
		log("no title provided!", 'error')
		exit()
	info = query_imdb(title)
	log(f"Query Movies Results: {info}", 'info')
