from urllib.parse import quote, unquote
import subprocess
import requests
from bs4 import BeautifulSoup
from lxml import etree
import os
from np.utils.pbdl.utils import query_series, query_movies, test_media
from np.core.conf import readConf

def get_poster(query):
	try:
		play_type = test_media(query)
	except:
		play_type = readConf()['play_type']
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	if os.path.exists(query):
		qtype = 'filepath'
		query_string = f"where {qtype} like \'%{query}%\'"
	else:
		qtype = 'id'
		query_string = f"where {qtype} = {query}"
	if play_type == 'series':
		column = 'still_path'
	else:
		column = 'poster'
	poster_url = subprocess.check_output(f"sqlite3 \"{dbfile}\" \"select {column} from {play_type} {query_string};\"", shell=True).decode().strip()
	log(f"get_poster.get_poster():Creating url:{poster_url}", 'info')
	if 'https://image.tmdb.org' not in poster_url:
		poster = f"https://image.tmdb.org/t/p/original/{poster_url}"
	else:
		poster = poster_url
	return poster

def dl_poster(poster_url):
	poster_path = os.path.join(os.path.expanduser("~"), '.np', 'poster.jpg')
	com = f"curl -o \"{poster_path}\" {poster_url}"
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		print(f"Error downloading poster ({poster_url}): {ret}", 'error')
		return poster_path
	else:
		print("Ok!")
		return poster_path

def convert_png(filepath, w=None, h=None):
	if w is None:
		w = 320
	if h is None:
		h = 240
	size = f"{w}x{h}"
	ext = os.path.splitext(filepath)[1]
	dname = os.path.dirname(filepath)
	fname = os.path.basename(os.path.splitext(filepath)[0])
	newpath = os.path.join(dname, f"{fname}.png")
	#com = (f"convert --resize \"{filepath}\" \"{newpath}\"")
	com = f"convert \"{filepath}\" -resize {size} \"{newpath}\""
	#com = ("convert 'poster.jpg' -resize " + str(self.art_w) + "x" + str(self.art_h) + " 'poster.png'")
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		print(f"Error converting jpg to png: {ret}", 'error')
		return False
	else:
		print("Ok!")
		return newpath

def get_poster2(q):
	query = "Shang-Chi And The Legend Of The Ten Rings"
	#url = f"https://www.movieposters.com/collections/shop?q={query.replace(' ', '+')}"
	if '%20' in query:
		query = urllib.parse.quote(q)
	url = ("https://www.google.com/search?q=" + q)
	r = requests.get(url)
	soup = BeautifulSoup(r.content, "html.parser")
	dom = etree.HTML(str(soup))
	l = dom.xpath('//img')
	poster = f"https:{l[0].values()[1]}"
	if 'png' in poster:
		filepath = '/home/monkey/.np/poster.png'
	elif 'jpg' in poster:
		filepath = '/home/monkey/.np/poster.jpg'
	try:
		subprocess.check_output(f"wget -o {filepath} \"{poster}\"", shell=True)
		return poster
	except:
		return None

def get_poster3(query):
	img_url = None
	q = quote(query)
	test='https://www.google.com/imgres?imgurl='
	s = '&amp;imgrefurl'
	url = ("https://www.google.com/search?q=" + q)
	r = requests.get(url)
	data = r.text.split("\n")
	for item in data:
		if test in item:
			img_url = item.split(test)[1].split(s)[0]
			if '%' in img_url:
				img_url = unquote(img_url)
				print(img_url)
			break
	if img_url is not None:
		try:
			com = (f"curl -o '/home/monkey/.np/poster.jpg' '{img_url}'")
			subprocess.check_output(com, shell=True)
		except Exception as e:
			log(f"Unable to get poster: {e}", 'error')
			return None
	else:
		return None
	screen = MP.conf['screen']
	art_w = MP.conf['windows'][screen]['viewer']['w']
	art_h = MP.conf['windows'][screen]['viewer']['h']
	com = ("convert 'poster.jpg' -resize " + str(art_w) + "x" + str(art_h) + " 'poster.png'")
	try:
		ret = subprocess.check_output(com, shell=True)
		album_art = 'poster.png'
		return album_art
	except:
		return None
