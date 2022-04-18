from PIL import Image, ImageTk
import eyed3
import urllib
import requests
import np
import json
import PySimpleGUI as sg
import subprocess

class music_mgr():
	def __init__(self):
		self.query_joiner = ' AND '
		self.api_url = "https://musicbrainz.org/ws/2"
		self.gui = None
		self.data = {}
		self.conf = np.readConf()
		self.screen = self.conf['screen']
		self.w = int(self.conf['screens'][self.screen]['w'])
		self.h = int(self.conf['screens'][self.screen]['h'])
		self.pos_x =  int(self.conf['screens'][self.screen]['pos_x'])
		self.pos_y =  int(self.conf['screens'][self.screen]['pos_y'])
		self.windows = []
		self.found_mp3_files = []
		self.tags = ['album', 'album_artist', 'album_type', 'artist', 'artist_origin', 'artist_url', 'audio_file_url', 'audio_source_url', 'best_release_date', 'bpm', 'cd_id', 'chapters', 'clear', 'comments', 'commercial_url', 'composer', 'copyright_url', 'disc_num', 'encoding_date', 'extended_header', 'file_info', 'frame_set', 'frameiter', 'genre', 'getBestDate', 'getTextFrame', 'header', 'images', 'internet_radio_url', 'isV1', 'isV2', 'lyrics', 'non_std_genre', 'objects', 'original_release_date', 'parse', 'payment_url', 'play_count', 'popularities', 'privates', 'publisher', 'publisher_url', 'read_only', 'recording_date', 'release_date', 'remove', 'save', 'setTextFrame', 'table_of_contents', 'tagging_date', 'terms_of_use', 'title', 'track_num', 'unique_file_ids', 'user_text_frames', 'user_url_frames', 'version']
		self.data = {}
		self.data['album_art'] = None

	def get_info(self, search_text, artist):
		arid = self.get_arid(artist)
		#print ("Artist id:", arid)
		query_text = urllib.parse.quote(search_text)
		url = (self.api_url + "/recording?fmt=json&query=" + query_text + self.query_joiner + "arid:" + str(arid))
		r = requests.get(url)
		json_data = json.loads(r.text)
		albums = self.get_albums(artist)
		matches_names = []
		matches_ids = []
		track_numbers = []
		self.out = []
		pos = -1
		for item in json_data['recordings']:
			title = item['title']
			track_id = item['id']
			try:
				release_date = item['first-release-date']
			except:
				release_date = None
			try:
				releases = item['releases']
			except:
				releases = None
			if releases is not None and release_date is not None:
				for release in releases:
					if release['title'] in albums:
						print ("Title in albums:", release['title'])
						#string = (str(release['id']) + ", " + str(release['title']))
						try:
							status = release['status']
						except:
							status = None
						if release['title'] not in matches_names and status == 'Official':
							group = release['release-group']
							_type = group['primary-type']
							try:
								stype = group['secondary-types']
								if 'Compilation' in stype:
									stype = stype[0]
								else:
									stype = None
							except Exception as e:
								print ("secondary type error:", e)
								stype = None
							track = release['media'][0]['track'][0]['number']
							#print ("group, type, track:", group, _type, track)
							#track_ct = release['media'][0]['track'][0]['track-count']
							if _type == 'EP' or _type == 'Album' and stype is None:
								print ("Is preferred type", _type, stype)
								self.data = {}
								self.data['title'] = title
								matches_names.append(title)
								self.data['album_type'] = _type
								self.data['track_id'] = track_id
								self.data['album'] = release['title']
								self.data['album_id'] = release['id']
								alid = self.data['album_id']
								self.data['year'] = release_date
								self.data['track_number'] = track
								self.data['artist'] = artist
								self.data['artist_id'] = arid
								#self.data['album_art'] = self.get_album_art_url(alid)
								return self.data
							else:
								print ("not preferred type:", _type, stype)
								temp = {}
								temp['title'] = release['title']
								matches_names.append(release['title'])
								temp['album_type'] = _type
								temp['track_id'] = release['id']
								temp['album'] = release['title']
								temp['album_id'] = release['id']
								alid = temp['album_id']
								temp['track_number'] = track
								temp['year'] = release_date
								temp['artist'] = artist
								temp['artist_id'] = arid
								#temp['album_art'] = self.get_album_art_url(alid)
								self.data[temp['title']] = temp
		return self.data
		#if len(matches) >= 0:
		#	matches = matches[0]
		#	out = out[0]
				
			

	def get_arid(self, artist):
		search_query = urllib.parse.quote(artist)
		url = (self.api_url + "/artist/?fmt=json&query=" + search_query)
		r = requests.get(url)
		json_data = json.loads(r.text)
		for item in json_data['artists']:
			if artist in item['name']:
				if artist == item['name']:
					arid = item['id']
					return arid


	def get_albums(self, artist):
		albums = []
		arid = self.get_arid(artist)
		url = (self.api_url + "/release-group/?fmt=json&query=arid:" + str(arid))
		r = requests.get(url)
		json_data = json.loads(r.text)
		for item in json_data['release-groups']:
			if item['primary-type'] == 'Album':
				albums.append(item['title'])
		return albums


	def get_album_art_url(self, album_id):
		print ("album id:", album_id)
		url = ("https://musicbrainz.org/ws/2/release/" + str(album_id) + "?fmt=json")
		print ("URL:", url)
		r = requests.get(url)
		json_data = json.loads(r.text)
		#print ("cover art response:", json_data)
		rid = json_data['id']
		has_art = json_data['cover-art-archive']['artwork']
		print ("Has art:", json_data['cover-art-archive'])
		if has_art:
			url = ("https://coverartarchive.org/release/" + str(rid))
			r = requests.get(url)
			json_data = json.loads(r.text)
			for item in json_data['images']:
				if item['front'] is True:
					self.imgurl = item['image']
					return self.imgurl
		else:
			return None

	def get_art_gimages(self, artist, album):
		api_key = '482f3866594242e97dcc1573601a9fb13b4345479d97b4ef03e1b7a76523a58d'
		img_url = None
		string = (artist + " " + album + " Album Art")
		query_string = urllib.parse.quote(string)
		url = ("https://serpapi.com/search.json?q=" + query_string + "&tbm=isch&ijn=0&api_key=" + str(api_key))
		r = requests.get(url)
		json_data = json.loads(r.text)
		self.imgurl = json_data['images_results'][0]['original']
		return self.imgurl


	def write_tag(self, filepath, tag_data):
		import eyed3
		if tag_data is not None:
			self.data = tag_data
		
		self.a = eyed3.load(filepath)
		if self.a is None:
			#re-initialize tag
			self.a.initTag()
		self.a.tag.album = self.data['album']
		self.a.tag.artist = self.data['artist']
		self.a.tag.title = self.data['title']
		self.a.tag.track_num = (self.data['track_number'], None)
		#set MB specific iv3v2 data
		self.a.tag.user_text_frames.set("MusicBrainz Release Track Id", self.data['track_id'])
		self.a.tag.user_text_frames.set("MusicBrainz Album Type", self.data['album_type'])
		self.a.tag.user_text_frames.set("MusicBrainz Album Id", self.data['album_id'])
		self.a.tag.user_text_frames.set("MusicBrainz Artist Id", self.data['artist_id'])
		self.a.tag.user_text_frames.set("MusicBrainz Album Artist Id", self.data['artist_id'])
		self.a.tag.release_date = self.data['year']
		# create album art embed url tag
		description = (self.data['artist'] + ":" + self.data['title'] + ":" + self.data['album'])
		self.a.tag.images.set(type_=3, img_data=None, mime_type=None, description=description, img_url=self.data['album_art'])
		self.a.tag.save()
		print ("wrote image to tag: filepath =", filepath, "data = ", tag_data)
		return True
		
		#except Exception as e:
		print ("Tag write failed:", e)
		return False
			

	def init_gui(self):
		self.layout = [
			[sg.Button('Pick File', expand_x=True, key='-PICK_FILE-'), sg.Button('Pick Directory', expand_x=True, key='-PICK_DIRECTORY-'), sg.Button('Close', expand_x=True, key='-Close-')],
			[sg.Listbox(self.found_mp3_files, size=(20, 10), change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, key='-FOUND_MP3_FILES-')],
			[sg.Text('Title:'), sg.Input(key="-TITLE-", enable_events=True, expand_x=True), sg.Text(), sg.Text('Album:'), sg.Input(key="-ALBUM-", enable_events=True, expand_x=True)],
			[sg.Text('Year:'), sg.Input(key="-YEAR-", enable_events=True, expand_x=True), sg.Text(), sg.Text('Artist:'), sg.Input(key="-ARTIST-", enable_events=True, expand_x=True)],
			[sg.Text('Track:'), sg.Input(key="-TRACK-", enable_events=True, expand_x=True), sg.Text(), sg.Text('Filepath:'), sg.Input(key="-FILEPATH-", enable_events=True, expand_x=True)],
			[sg.Button('Save Tag', key='-SAVE_TAG-'), sg.Button('Read Tag', key='-READ_TAG-')],
			[sg.Image(self.data['album_art'], key='-ALBUM_ART-')],
			[sg.Text('Image URL:'), sg.Input(key="-ALBUM_ART_URL-", enable_events=True, expand_x=True)],
			[sg.Sizegrip(key='-gui_size-')]
		]
		self.win = sg.Window('Music Manager', layout=self.layout, no_titlebar=True, location=(300, 300), size=(1024, 768), grab_anywhere=True, keep_on_top=True, element_justification='center', finalize=True, resizable=True)
		self.windows.append(self.win)
		self.gui = True
		self.default_music_dir = self.conf['media_directories']['music']

	def file_browse_window(self):
		filepath = None
		file_browser_layout = [[sg.T("")], [sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-PICKED_FILE-")],[sg.Button("Submit")]]
		file_browser_window = sg.Window('Load Media file or playlist...', file_browser_layout, location=(int(self.pos_x), int(self.pos_y)))
		self.windows.append(file_browser_window)
		while True:
			file_browser_event, file_browser_values = file_browser_window.read()
			if file_browser_event == sg.WIN_CLOSED or file_browser_event=="Exit":
				filepath = None
				break
			elif file_browser_event == "Submit":
				try:
					filepath = file_browser_values["-PICKED_FILE-"]
				except:
					filepath = None
				file_browser_window.close()
				break
		return filepath

	def folder_browse_window(self):
		path = None
		folder_browser_layout = [[sg.T("")], [sg.Text("Choose directory: "), sg.Input(key='-USER_INPUT-', enable_events=True), sg.FolderBrowse(key="-PICKED_DIR-")], [sg.Button("Submit")]]
		folder_browser_window = sg.Window("Save playlist file...", folder_browser_layout, location=(int(self.pos_x), int(self.pos_y)))
		self.windows.append(folder_browser_window)
		self.target_dir = None
		while True:
			folder_browser_event, folder_browser_values = folder_browser_window.read()
			if folder_browser_event == '-USER_INPUT-':
				self.target_dir = folder_browser_values['-USER_INPUT-']
			elif folder_browser_event == 'Submit':
				if self.target_dir == None:
					if folder_browser_values["-PICKED_DIR-"] is not None:
						self.target_dir = folder_browser_values["-PICKED_DIR-"]
					elif folder_browser_values['-USER_INPUT-']:
						self.target_dir = folder_browser_values['-USER_INPUT-']
				break
			if folder_browser_event == sg.WIN_CLOSED or folder_browser_event=="Exit":
				break
		folder_browser_window.close()				
		return self.target_dir


	def get_events(self):
		if self.gui == None:
			self.init_gui()
		try:
			self.window, self.event, self.values = sg.read_all_windows(timeout=10)
			return (self.window, self.event, self.values)
		except Exception as e:
			print ("Error in get_events, line 189", e)
			return (None, None, None)


	def read_tag(self, filepath):
		self.a = eyed3.load(filepath)
		self.data = {}
		self.data['album_id'] = None
		for frame in self.a.tag.user_text_frames:
			if 'Artist Id' in frame.description:
				self.data['artist_id'] = frame.text
			elif 'Album Id' in frame.description:
				self.data['album_id'] = frame.text
			elif 'Album Type' in frame.description:
				self.data['album_type'] = frame.text
			elif 'Release Track Id' in frame.description:
				self.data['track_id'] = frame.text
#		self.data['album_type'] = self.a.tag.user_text_frames.get("MusicBrainz Album Type")
#		self.data['track_id'] = self.a.tag.user_text_frames.get("MusicBrainz Release Track Id")
		self.data['track_number'] = self.a.tag.track_num
		self.data['album'] = self.a.tag.album
		self.data['artist'] = self.a.tag.artist
		self.data['title'] = self.a.tag.title
		self.data['year'] = self.a.tag.release_date
		self.data['filepath'] = filepath
		#print (self.data)
		self.win['-TITLE-'].update(self.data['title'])
		self.win['-ALBUM-'].update(self.data['album'])
		self.win['-YEAR-'].update(self.data['year'])
		self.win['-ARTIST-'].update(self.data['artist'])
		self.win['-TRACK-'].update(self.data['track_number'])
		self.win['-FILEPATH-'].update(self.data['filepath'])
		try:
			test = self.data['album_id']
		except:
			self.data['album_id'] = None
		if self.data['album_id'] is None:
			self.data = self.get_info(self.data['title'], self.data['artist'])
		url = self.get_album_art_url(self.data['album_id'])
		if url is None:
			url = self.get_art_gimages(self.data['artist'], self.data['album'])
		print (url)
		self.dl_album_art(url)
		#self.win['-ALBUM_ART-'].update('poster.jpg')
		self.win['-ALBUM_ART_URL-'].update(url)
		return self.data


	def dl_album_art(self, url):
		com = ("wget --output-document 'poster.jpg' '" + url + "'")
		subprocess.check_output(com, shell=True)
		com = "convert 'poster.jpg' -resize 300x300 'poster.png'"
		ret = subprocess.check_output(com, shell=True)
		img = Image.open('poster.png')
		image = ImageTk.PhotoImage(image=img)
		self.win['-ALBUM_ART-'].update(data=image)
		self.win['-ALBUM_ART_URL-'].update(url)


def search_directory(target_dir):			
	global mgr
	com = ("find '" + target_dir + "' -name '*.mp3'")
	files = subprocess.check_output(com, shell=True).decode()
	mgr.found_mp3_files = files.split("\n")
	mgr.win['-FOUND_MP3_FILES-'].update(mgr.found_mp3_files)
		


if __name__ == "__main__":
	mgr = music_mgr()
	mgr.init_gui()
	search_directory('/var/storage/Music')
	while True:
		w, e, v = mgr.get_events()
		if e != '__TIMEOUT__':
			if e == '-PICK_FILE-':
				mgr.found_mp3_files = [mgr.file_browse_window()]
				mgr.win['-FOUND_MP3_FILES-'].update(mgr.found_mp3_files)
				#print ("Found files:", mgr.found_mp3_files)
			elif e == '-PICK_DIRECTORY-':
				target_dir = mgr.folder_browse_window()
				search_directory(target_dir)
			elif e == '-Close-' or e == sg.WIN_CLOSED:
				break
			elif e == '-FOUND_MP3_FILES-':
				filepath = v[e][0]
				info = mgr.read_tag(filepath)
				print (info)
			elif e == '-SAVE_TAG-':
				data = {}
				filepath = v['-FOUND_MP3_FILES-'][0]
				title = v['-TITLE-']
				artist = v['-ARTIST-']
				data = mgr.get_info(title, artist)
				data['album_art'] = v['-ALBUM_ART_URL-']
				ret = mgr.write_tag(filepath, data)
				print ("Write tag results:", ret)
			elif e == '-READ_TAG-':
				print (e, v)
				filepath = v['-FOUND_MP3_FILES-'][0]
				mgr.data = mgr.read_tag(filepath)
	for w in mgr.windows:
		w.close()
	exit()
