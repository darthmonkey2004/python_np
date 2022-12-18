from datetime import datetime
import os

def readLog(logfile=None):
	if logfile is None:
		logfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.log')
	try:
		with open(logfile, 'r') as f:
			data = f.read().split("\n")
			f.close()
		return data
	except:
		txt = f"Log file not found! ({logfile})"
		return txt

def searchLog(query, logfile=None):
	if logfile is None:
		logfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.log')
	data = readLog(logfile)
	out = []
	for line in data:
		if query in line:
			out.append(line)
	return out

def get_type_change_times(target=None):
	lines = searchLog('Play type changed:')
	out = {}
	for line in lines:
		flag = None
		if '>>' in line:
			ts = line.replace('DEBUG:root:', '').split('--')[0]
			fromtype, totype = line.split('changed:')[1].split(' >> ')
			if totype == 'music':
				flag = 'start'
			elif fromtype == 'music':
				flag = 'end'
			if flag is not None:
				obj = datetime.strptime(ts, '%d-%m-%Y %H:%M:%S:%f')
				seconds = datetime.timestamp(obj)
				date = str(obj.date())
				time = str(obj.time())
				if flag == 'start':
					out[date] = {}
					out[date]['start'] = seconds
					out[date]['date'] = date
					out[date]['time'] = time
				elif flag == 'end':
					out[date]['end'] = seconds
					duration = out[date]['end'] - out[date]['start']
					out[date]['duration'] = duration
	return out


if __name__ == "__main__":
	import sys
	q = sys.argv[1]
	try:
		logfile = sys.argv[2]
	except:
		logfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.log')
	print(searchLog (query=q, logfile=logfile))
