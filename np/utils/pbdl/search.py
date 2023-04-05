from np.utils.pbdl.ty_isin import *
from np.utils.pbdl.se_isin import *
from urllib.parse import unquote, quote
import requests
import np
import json
from np.core.log import np_logger
logger = np_logger().log_msg
#TODO: extract list of categories from pirate bay website, build function to return category names and codes.
#magnet links are in the following uri format:
#magnet = "magnet:?xt=urn:btih:{info_hash}&dn={name}&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://tracker.openbittorrent.com:6969/announce&tr=udp://tracker.opentrackr.org:1337&tr=udp://tracker.leechers-paradise.org:6969/announce&tr=udp://tracker.dler.org:6969/announce&tr=udp://opentracker.i2p.rocks:6969/announce&tr=udp://47.ip-51-68-199.eu:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://9.rarbg.to:2920/announce&tr=udp://tracker.pirateparty.gr:6969/announce&tr=udp://tracker.cyberia.is:6969/announce"

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)

def search(query, cat=200):
	results = {}
	query = quote(query)
	base_url = get_url()
	url = (base_url + "/search/{query}/1/7/{cat}".format(query=query,cat=cat))
	r = requests.get(url)
	lines = r.content.decode().strip().split("\n")
	magnet = None
	title = None
	for line in lines:
		m = '<a href="magnet:?'
		if m in line:
			magnet = line.split('"')[1]
			title = unquote(magnet.split("&dn=")[1].split("&tr=")[0])
			if ty_isin(title):
				t, y = ty_isin(title, True)
				title = f"{t} ({y})"
			results[title] = {}
			results[title]['magnet'] = magnet
	return results
	


def get_url():
	proxies = {}
	utest = 'class="site"'
	ctest = 'class="country"'
	stest = 'class="status"'
	sptest = 'class="speed"'
	url = "https://piratebayproxy.info"
	r = requests.get(url)
	lines = r.content.decode().split("\n")
	proxies = {}
	pos = -1
	for line in lines:
		line = line.strip()
		if line != '':
			if utest in line:
				data = {}
				pos = pos + 1
				splitter = 'href="'
				url = line.split(splitter)[1].split('"')[0]
				data['url'] = url
			elif ctest in line:
				splitter = 'title="'
				country = line.split(splitter)[1].split('"')[0]
				data['country'] = country
			elif stest in line:
				splitter = '/img/'
				status = line.split(splitter)[1].split('.png')[0]
				data['status'] = status
			elif sptest in line:
				splitter = '">'
				speed = line.split(splitter)[1].split('<')[0]
				data['speed'] = speed
				if status == 'up':
					proxies[speed] = data
		
	speeds = sorted(proxies.keys(), key = lambda x:float(x))
	speed = speeds[0]
	url = proxies[speed]['url']
	return url


