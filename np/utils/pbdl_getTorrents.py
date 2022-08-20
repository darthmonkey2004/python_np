import subprocess
from np import readConf, log, get_columns
conf = readConf()

def send_command(com):
	try:
		ret = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode().split("\n")
		if ret is not None:
			return ret
		else:
			return True
	except Exception as e:
		log(f"Command failed:{e}, Command: {com}", 'error')
		return False

def get_torrents():
	torrents = {}
	com = (f"transmission-remote {conf['pbdl_url']} -l")
	data = subprocess.check_output(com, shell=True).decode().strip().split('\n')
	outlist = []
	pos = -1
	for line in data:
		pos += 1
		outstr = None
		if pos > 0:
			line = line.strip()
			chunks = line.split(" ")
			for chunk in chunks:
				if chunk != '':
					if outstr == None:
						outstr = str(chunk)
					else:
						outstr = (outstr + "|" + str(chunk))
			outlist.append(outstr)
	for line in outlist:
		data = {}
		if line is not None:
			if line.split('|')[0] == 'ID' or line.split('|')[0] == 'Sum:':
				pass
			else:
				chunks = line.split('|')
				tid = chunks[0]
				if '*' in tid:
					tid = int(tid.split('*')[0])
				else:
					tid = int(tid)
				data['percent'] = chunks[1]
				data['have'] = chunks[2]
				data['size_unit'] = chunks[3]
				data['eta'] = chunks[4]
				data['up'] = chunks[5]
				data['down'] = chunks[6]
				data['ratio'] = chunks[7]
				data['status'] = chunks[8]
				length = len(chunks)
				name_pieces = chunks[9:length]
				j = ' '
				data['name'] = j.join(name_pieces)
				string = (str(tid) + ":" + str(data['name']) + "|" + str(data['percent']))
				#if string not in active_torrents:
				#	active_torrents.append(string)
				torrents[tid] = data
	#try:
		#pbdl_win['-TORRENT_SELECT-'].update(active_torrents)
	#except:
	#	pass
	torrents = torrents
	return torrents

def get_files(tid):
	com = (f"transmission-remote 192.168.2.2 -t{tid} -f | grep '100%' | grep -v \".jpg\" | grep -v \"sample\" | grep -v \".srt\" | grep -v \".nfo\" | grep -v \".txt\" | cut -d \"/\" -f 2")
	data = send_command(com)
	files = {}
	for item in data:
		if item != '':
			item = item.strip()
			play_type = test_media_type(item)
			files['play_type'] = play_type
			files['filepath'] = item
	try:
		pbdl_win['-TORRENT_FILES-'].update(files)
	except:
		pass
	return files

def test_media_type(filepath):
	filepath = filepath
	sinfo = None
	season = None
	episode_number = None
	try:
		sinfo, season, episode_number = np.seinfo(filepath)
		play_type = 'series'
		length = len(filepath.split(sinfo)) - 1
		series_name = filepath.split(sinfo)[0]
		if '/' in series_name:
			series_name = series_name.split('/')[1]
			out_list = [series_name, sinfo, season, episode_number]
			out = ('series', filepath, out_list)
			return out
	except Exception as e:
		log(f"Filepath doesn't appear to be a series, trying type: movie.", 'info')
		play_type = 'movies'
		if '(' in filepath and ')' in filepath:
			year = int(filepath.split('(')[1].split(')')[0])
			if year >= 1900:
				string = f" ({year}) "
				if string in filepath:
					title = filepath.split(string)[0]

				else:
					string = ('(' + str(year) + ')')
					title = filepath.split(string)[0]
					out_list =  [title, year]
					out = ('movie', filepath, out_list)
					return out
		else:
			temp = filepath.split('.')
			if len(temp) > 2:
				title = 'Unknown'
			else:
				title = filepath.split('.')[0]
			out_list =  [title, 'Unknown']
			out = ('movie', filepath, out_list)
			return out

def build_torrents():
	data = {}
	torrents = get_torrents()
	for tid in list(torrents.keys()):
		data[tid] = {}
		if torrents[tid]['percent'] == '100%':
			files = get_files(tid)
			filepath = files['filepath']
			table, filepath, fileinfo = files['play_type']
			print ("fileinfo:", fileinfo)
			if table == 'series':
				series_name, sinfo, season, episode_number = fileinfo
				print (table, fileinfo)
				print ("table:", table)
				pragma = get_columns(table)
				columns = list(pgragma.keys())
				torrents[tid]['sinfo'] = sinfo
				for key in columns:
					if key == 'series_name':
						torrents[tid]['series_name'] = torrents[tid]['files']['name']
					elif key == 'season':
						torrents[tid]['season'] = season
					elif key == 'episode_number':
						torrents[tid]['episode_number'] = episode_number
					elif key == 'filepath':
						torrents[tid]['filepath'] = torrents[tid]['files']['filepath']
					else:
						torrents[tid][key] = 'Unknown'
			elif table == 'movies':
				title, year = fileinfo
				for key in columns:
					if key == 'title':
						torrents[tid]['title'] = torrents[tid]['filepath']['name']
					elif key == 'filepath':
						torrents[tid]['filepath'] = torrents[tid]['files']['filepath']
					elif key == 'year':
						torrents[tid]['year'] = year
					else:
						torrents[tid][key] = 'Unknown'
			
			
	return torrents
if __name__ == "__main__":
	data = build_torrents()
	print (data)
	
