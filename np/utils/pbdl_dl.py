from urllib.parse import unquote
import requests
import np
import json

def get_results_html(query, cat=200):
	base_url = np.get_url()
	url = (base_url + "/search/{query}/1/7/{cat}".format(query=query,cat=cat))
	print (url)
	r = requests.get(url)
	print (r.content.decode().strip())

def get_results_api(query, cat=200):
	query = query.split(' ')
	j = '+'
	query = j.join(query)
	base_url = np.get_url()
	s = 'https'	
	if s in base_url:
		base_url = base_url.split(s)[1]
		base_url = ("http" + base_url)
	url = (base_url + "/api?url=/q.php?q={query}&cat={cat}&sort=7".format(query=query,cat=cat))
	r = requests.get(url)
	out = r.content.decode().strip()
	json_data = json.loads(out)
	results = {}

	for data in json_data:
		keys = list(data.keys())
		vals = list(data.values())
		pos = -1
		for key in keys:
			pos = pos + 1
			val = vals[pos]
			if key == 'name':
				name = val
			elif key == 'info_hash':
				info_hash = val
			elif key == 'seeders':
				seeders = int(val)
				if seeders >= 0:
					dkey = (name + " (Seeds: " + str(seeders) + ")")				
					results[dkey] = {}
					results[dkey]['info_hash'] = info_hash
					results[dkey]['seeders'] = seeders
	return results
				
magnet = "magnet:?xt=urn:btih:{info_hash}&dn={name}&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://tracker.openbittorrent.com:6969/announce&tr=udp://tracker.opentrackr.org:1337&tr=udp://tracker.leechers-paradise.org:6969/announce&tr=udp://tracker.dler.org:6969/announce&tr=udp://opentracker.i2p.rocks:6969/announce&tr=udp://47.ip-51-68-199.eu:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://9.rarbg.to:2920/announce&tr=udp://tracker.pirateparty.gr:6969/announce&tr=udp://tracker.cyberia.is:6969/announce"

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
