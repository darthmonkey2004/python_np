#!/usr/bin/env python3
import os
from np.core.log import readConf
conf = readConf()


def set_empty():
	pragma = get_columns('series')
	columns = list(pragma.keys())
	info = {}
	for key in columns:
		dtype = pragma[key]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			info[key] = 0
		elif dtype == 'TEXT':
			info[key] = 'Unknown'
	return info




def mk_list():
	_list = []
	for s in range(0, 99):
		for e in range(0, 99):
			if len(str(s)) == 1:
				season = f"0{s}"
			else:
				season = str(s)
			if len(str(e)) == 1:
				ep = f"0{e}"
			else:
				ep = str(e)
			_list.append(f"S{season}E{ep}")
			_list.append(f"S{season}e{ep}")
			_list.append(f"s{season}E{ep}")
			_list.append(f"s{season}e{ep}")
	return _list

def parse(filepath):
	_list = mk_list()
	out = []
	for item in _list:
		if item in filepath:
			return item
	return None


def get_info_from_filepath(filepath):
	# use only if in local directory structure, expects specific naming ritual
	info = set_empty()
	info['filepath'] = filepath
	info['series_name'] = filepath.split(media_dir)[1].split(os.path.sep)[2]
	info['season'] = int(filepath.split(media_dir)[1].split(os.path.sep)[3].split('S')[1])
	info['episode_number'] = int(filepath.split(media_dir)[1].split(os.path.sep)[4].split(f"S{season}E")[1].replace('.', ' ').split(' ')[0])
	try:
		info['episode_name'] = os.path.splitext(filepath.split(media_dir)[1].split(os.path.sep)[4])[0].replace('.', ' ').split(f"S{season}E{episode_number}")[1].strip()
	except:
		pass
	return info


def se_isin(filepath, return_data=False):
	string = parse(filepath)
	s = None
	e = None
	media_dir = conf['media_directories']['main']
	if media_dir in filepath:# if filepath in structured system already, we can parse info from filepath
		play_type = filepath.split(media_dir)[1].split(os.path.sep)[1].lower()
		if return_data == False:
			#if just type requested, check to see if matches series, return accordingly.
			if play_type == 'series':
				return True
			else:
				return False
			#else, return info dict
		elif return_data == True:
			s = int(filepath.split(media_dir)[1].split(os.path.sep)[3].split('S')[1])
			e = int(filepath.split(media_dir)[1].split(os.path.sep)[4].split(f"S{s}E")[1].replace('.', ' ').split(' ')[0])
			return (s, e, string)
		
	else:
		if string is not None:
			nstring = string.upper()
			s = nstring.split('S')[1].split('E')[0]
			e = nstring.split('E')[1]
			if '0' in s:
				d0 = s[:1]
				d1 = s[1:]
				if d0 == '0':
					s = d1
				else:
					s = (f"{d0}{d1}")
			if '0' in e:
				d0 = e[:1]
				d1 = e[1:]
				if d0 == '0':
					e = d1
				else:
					e = (f"{d0}{d1}")
		if return_data == True:
			return (s, e, string)
		else:
			if s is not None and e is not None:
				return True
			else:
				return False
			


if __name__ == "__main__":
	import sys
	try:
		filepath = sys.argv[1]
	except:
		log(f"No filepath provided!", 'error')
	ret = se_isin(filepath)
	log(ret, 'info')
