import json
import requests

def get(control, user=None, pw=None, ret='data'):
	headers = get_auth()
	url = f"http://{get_router_ip()}/{control}.asp"
	r = requests.get(url, headers=headers)
	lines = []
	if r.status_code == 200:
		if ret == 'data':
			lines = r.text.split("\n")
		elif ret == 'req':
			return r
	elif r.status_code == 401:
		print("refreshing authentication, and trying again...")
		headers = get_auth(user=user, pw=pw)
		url = f"http://{get_router_ip()}/{control}.asp"
		r = requests.get(url, headers=headers)
		if r.status_code != 200:
			print("Failed to authenticate! Aborting...")
			return []
	else:
		print(f"Failed to get url ({url}, code={r.status_code}): Data:{r.text}")
		lines = []
	return lines


def get_wan_gateway():
	tagline1 = 'var table = new Array('
	tagline2 = "','UG','0','WAN'"
	lines = get('RouteTable')
	for line in lines:
		if tagline1 in line and tagline2 in line:
			return line.split(',')[2].split("'")[1]



url = 'https://ipinfo.io/json/?token=7e1b9011ee9f9b'
r = requests.get(url)
data = json.loads(r.text)
ip = data['ip']
#url = f"http://ipinfo.io/{ip}?token=4d3f83adf329f8"
#r = requests.get(url)
url = f"https://whatismyipaddress.com/ip/{ip}"
r = requests.get(url)
data = r.text.splitlines()
#location_info_url = 'https://apis.cmp.quantcast.com/geoip'
tag = 'ip-information'
data = r.text.splitlines()
for line in data:
	if tag in line:
		print("line:", line)
		input()



#curl 'https://ipinfo.io/widget/demo/45.128.36.194'
#curl "ipinfo.io/45.128.36.194?token=4d3f83adf329f8"




