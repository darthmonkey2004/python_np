import os
import datetime
from np.core.log import np_logger 
import sys, traceback

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


def build_year_list():
	y = int(datetime.date.today().year) + 1
	years = []
	for i in range(1900, y):
		years.append(str(i))
	return years

def ty_isin(filepath, return_data=False):
	try:
		if return_data == True:
			data = parse_title(filepath)
			if data is not None:
				return data
			else:
				return False
		else:
			return True
	except Exception as e:
		#log(f"Filepath doesn't have apparent movie tags! {e}", 'info')
		if return_data == True:
			return os.path.splitext(os.path.basename(fname))[0], None
		else:
			return False


def parse_title(filepath):
	fname = os.path.basename(filepath)
	movie_tags = ['1080p', '720p', '480p', 'WEBRip', 'x264', 'AAC5.1', '[']
	title = None
	year = None
	if '(' in fname:
		year = fname.split('(')[1].split(')')[0].strip()
		f = fname.replace('.', ' ')
		s = f"({year})"
		title = fname.split(s)[0].strip()
		return title, year
	else:
		years = build_year_list()
		for year in years:
			if year in fname:
				fname = fname.replace('.', ' ')
				s = f"{year}"
				title = fname.split(s)[0].strip()
				return title, year
	for tag in movie_tags:
		if tag in fname:
			fname = fname.split(tag)[0]
	if title == None:
		None
			
	return title, year

if __name__ == "__main__":
	filepath = 'South.Park.The.Streaming.Wars.2022.1080p.WEBRip.x264.AAC5.1-[YTS.MX].mp4'
	title, year = parse_title(filepath)
	print (f"title:{title}, year:{year}")
