from np.core.log import np_logger
from np.core.conf import readConf
from np.core.core import write_history, read_history
from np.core.nplayer_db import querydb
import random

history = {}
history['history'] = []
history['pos'] = len(history['history']) - 1
history['playing_from_history'] = False
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



def get_info_string(filepath):
	strings = []
	qstring = ("filepath = '" + filepath + "'")
	item = querydb(table='series', column='series_name,season,episode_number,episode_name,id', query=qstring)
	try:
		series_name, season, episode_number, episode_name, _id = item[0]
		string = ("series:" + series_name + ":" + str(season) + ":" + str(episode_number) + ":" + episode_name + ":" + str(_id))
	except:
		string = ("Unknown: " + filepath)
	return string



def get_next():
	global history
	conf = readConf()
	if conf['play_type'] == 'series':
		log("get next: series started!")
		_list = querydb(table='series', column='distinct series_name', query='isactive = 1')
		l = len(_list) - 1
		pickno = random.randint(0, l)
		series_name = str(_list[pickno][0])
		qstring = ("series_name like '%" + series_name + "%'")
		items = querydb(table='series', column='filepath', query=qstring)
		_list=[]
		for item in items:
			_list.append(item[0])
		series_history = read_history()
		try:
			last = series_history[series_name]
		except:
			last = None
		if last in _list and last is not None:
			if conf['debug'] == True:
				log("Last in list: {last}", 'info')
			idx = int(_list.index(last))
			idx = idx + 1
			try:
				next = _list[idx]
				selected_playlist_item = get_info_string(next)
				log(f"get_next:Next set! Series Name: {series_name}, Index: {idx}, Next: {next}", 'info')
			except:
				next = _list[0]
				selected_playlist_item = get_info_string(next)
				log(f"get_next:Next not set (reset to 0)! Series Name: {series_name}, Index: {idx}, Next: {next}", 'info')
			if history['playing_from_history'] == False:
				history['history'].append(next)
			elif history['playing_from_history'] == True:
				skip_next()
			series_history[series_name] = next
			write_history(series_history)
		elif last is None:
			next = _list[0]
			series_history[series_name] = next
			write_history(series_history)
		else:
			txt = ("Last file recorded not in playlist:" + last + ", " + str(_list))
			log(txt, 'warning')
		if conf['debug'] == True:
			log(f"DEBUG=True:get_next exited. next={next}", 'info')
		return next
	elif conf['play_type'] == 'movies':
		_list = querydb(table='movies', column='filepath', query='isactive = 1')
		l = len(_list) - 1
		pickno = random.randint(0, l)
		next = str(_list[pickno][0])
		if history['playing_from_history'] == False:
			history['history'].append(next)
		return next
	elif conf['play_type'] == 'music':
		_list = querydb(table='music', column='filepath', query='isactive = 1')
		l = len(_list) - 1
		pickno = random.randint(0, l)
		next = str(_list[pickno][0])
		if history['playing_from_history'] == False:
			history['history'].append(next)
		return next

