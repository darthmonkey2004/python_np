import requests
import json
from urllib.parse import quote

def ck_code(code):
	encoded = quote(code)
	encoded = f"source={encoded}"
	url = "https://extendsclass.com/python-tester-source"
	r = requests.post(url, data=encoded)
	if r.status_code != 200:
		print(f"Error: Bad response code! {r.status_code}, {r.text}")
	else:
		return r.text
if __name__ == "__main__":
	import sys
	text = sys.argv[1]
	json_data = json.loads(ck_code(text))
	print(json_data)
