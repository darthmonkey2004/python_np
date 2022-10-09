import vlc
import os
from bs4 import BeautifulSoup
import requests
import PySimpleGUI as sg
from np.core.conf import readConf
from np.core.core import shell
from np.utils.id3 import tag
from np.core.gui import file_browse_window
from np.core.log import np_logger
id3 = tag()
log = np_logger().log_msg

def delete_file(win, filepath):
	choice, _ = sg.Window("Delete?", [[sg.T(f"Really delete file \"{filepath}\"?", auto_size_text=True)], [sg.Yes(s=10), sg.No(s=10)]], disable_close=True).read(close=True)
	if choice == 'Yes':
		com = f"rm \"{filepath}\""
		ret = shell(com)
		if ret != '':
			log("Delete action returned data: {ret}", 'warning')
		else:
			log("Deleted!", 'info')
	music_files = list_files(win)
	return True

def list_files(win, path=None):
	if path == None:
		conf = readConf()
		path = conf['media_directories']['music']
	com = f"find \"{path}\" -name \"*.mp3\""
	files = shell(com).split("\n")
	files = sorted(files)
	win['-music_list_select-'].update(files)
	return files

def read_tag(win, filepath):
	log(f"Reading file: {filepath}", 'info')
	tag = id3.read(filepath)
	d = {}
	d['album'] = tag.album
	d['filepath'] = tag.filepath
	d['title'] = tag.title
	d['artist'] = tag.artist
	d['album'] = tag.album
	if tag.year == 'Unkn':
		tag.year = '0000'
	d['year'] = tag.year
	if tag.genre == 'Unknown (255)':
		tag.genre = 'Unknown'
	d['genre'] = tag.genre
	d['track'] = tag.track
	if tag.comment == '':
		tag.comment = f"Tag created by python_np for linux!"
	d['comment'] = tag.comment
	sg.fill_form_with_values(win, d)
	return tag

def find_album(artist, title):
	query = f"{artist} {title} album"
	url = f"https://www.google.com/search?q={query}"
	r = requests.get(url)
	if r.status_code == 200:
		sr = BeautifulSoup(r.text, "html.parser")
		album = sr.find("div", class_='BNeawe').text
		return album
	else:
		log(f"Error: Bad status code! {r.status_code}", 'error')
		return None


def run():		
	menu_def = [['File', ['Pick File', 'Save', 'Pick Folder']], ['lookup', ['Lookup Album']]]
	props = ['title', 'artist', 'album', 'year', 'genre', 'track', 'comment']
	layout = [[sg.MenubarCustom(menu_def, tearoff=True, key='-menubar_key-'), sg.Checkbox(text='Auto Rename Files', auto_size_text=True, default=True, change_submits=True, enable_events=True, key='auto_rename')]]
	layout.append([sg.Text('Filepath:'), sg.Input(key='filepath', expand_x=True, enable_events=True, do_not_clear=True), sg.Button('Load Tag Data', key='-LOAD-')])
	music_files = []
	for prop in props:
		line = [sg.Text(prop), sg.Input(key=prop, expand_x=True, enable_events=True, do_not_clear=True)]
		layout.append(line)

	line = [sg.Button('delete'), sg.Button('play'), sg.Button('stop'), sg.Button('Save Tag'), sg.Button('Lookup Data'), sg.Button('Close')]
	layout.append(line)
	line = [sg.Listbox(values=music_files, change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-music_list_select-')]
	layout.append(line)
	win = sg.Window('GUI', layout, no_titlebar=False, location=(0,0), size=(640,480), keep_on_top=False, grab_anywhere=True, element_justification='center', resizable=True)
	tag = None
	p = vlc.MediaPlayer()
	while True:
		event, values = win.read(timeout=1)
		if music_files == []:
			music_files = list_files(win)
		auto_rename = values['auto_rename']
		if event == '__TIMEOUT__':
			pass
		else:
			log(f"EVENT: {event}", 'info')
			if event == 'Pick File':
				conf = readConf()
				music_dir = conf['media_directories']['music']
				path = file_browse_window(music_dir)
				if path:
					win['filepath'].update(path)
					tag = read_tag(win, path)
					tag.filepath = path
					string = f"file://{tag.filepath}"
					p = vlc.MediaPlayer(string)
			elif event == 'Pick Folder':
				conf = readConf()
				music_dir = conf['media_directories']['music']
				path = file_browse_window(music_dir)
			elif event == '-LOAD-':
				p = values['filepath']
				if p != '':
					path = p
					log(f"Path:'{path}'", 'info')
				else:
					conf = readConf()
					music_dir = conf['media_directories']['music']
					path = file_browse_window(music_dir)
				if path:
					win['filepath'].update(path)
					tag = read_tag(win, path)
					tag.filepath = path
					string = f"file://{tag.filepath}"
					p = vlc.MediaPlayer(string)
			elif event == 'title':
				if tag is not None:
					tag.title = values[event]
			elif event == 'filepath':
				if tag is not None:
					tag.filepath = values[event]
			elif event == 'artist':
				if tag is not None:
					tag.artist = values[event]
			elif event == 'album':
				if tag is not None:
					tag.album = values[event]
			elif event == 'year':
				if tag is not None:
					tag.year = values[event]
			elif event == 'genre':
				if tag is not None:
					tag.genre = values[event]
			elif event == 'track':
				if tag is not None:
					tag.track = values[event]
			elif event == 'comment':
				if tag is not None:
					tag.comment = values[event]
			elif event == 'Save Tag':
				if tag is not None and tag.filepath is not None and tag.filepath != '':
					if auto_rename == True:
						fname = os.path.basename(tag.filepath)
						dirname = os.path.dirname(tag.filepath)
						l = len(fname) - 4
						ext = fname[l:]
						if tag.album is not None and tag.album != '' and tag.album != 'Unknown' and tag.album != tag.title and tag.album != tag.artist:
							newpath = f"{dirname}{os.path.sep}{tag.artist} - {tag.title} - {tag.album}{ext}"
						else:
							newpath = f"{dirname}{os.path.sep}{tag.artist} - {tag.title}{ext}"
						log(f"Auto renaming file: {tag.filepath} > {newpath}", 'info')
						if tag.filepath != newpath:
							com = f"mv \"{tag.filepath}\" \"{newpath}\""
							ret = shell(com)
							if ret:
								log(f"Error moving file: {ret}", 'error')
							else:
								log("Ok!", 'info')
								tag.filepath = newpath
								win['filepath'].update(tag.filepath)
								music_files = list_files(win)
								win.refresh()
						else:
							log(f"Autorename: Skipping (filepath and newpath match!)", 'info')
					ret = tag.save(tag.filepath)
					log(f"Tag Save Results: {ret}", 'info')
			elif event == 'Lookup Album':
				if tag is not None:
					album = find_album(tag.artist, tag.title)
					if album is not None:
						tag.album = album
						log(f"Album found: '{album}'", 'info')
					else:
						log("Unable to find album!", 'warning')
						tag.album = "Unknown"
					win['album'].update(tag.album)
			elif event == '-music_list_select-':
				path = values[event][0]
				win['filepath'].update(path)
				tag = read_tag(win, path)
				tag.filepath = path
				string = f"file://{tag.filepath}"
				p = vlc.MediaPlayer(string)
			elif event == 'play':
				try:
					p.play()
				except:
					log("Please select a file first!", 'error')
			elif event == 'stop':
				try:
					p.stop()
				except:
					log("Please select a file first!", 'error')
			elif event == 'delete':
				delete_file(win, tag.filepath)
			elif event == 'sg.WIN_CLOSED' or event == 'Close':
				if event == 'Close':
					win.close()
				break

if __name__ == "__main__":
	run()
