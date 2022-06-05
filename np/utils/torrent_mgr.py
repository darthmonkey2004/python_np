#!/usr/bin/env python3

import subprocess

def get_all():
	data = subprocess.check_output("transmission-remote -l", stderr=subprocess.STDOUT, shell=True).decode().split("\n")
	ct = len(data)
	outlist = []
	for line in data:
		outstr = None
		line = line.strip()
		chunks = line.split(' ')
		for chunk in chunks:
			if chunk != '':
				if outstr == None:
					outstr = str(chunk)
				else:
					outstr = (outstr + "|" + str(chunk))
		outlist.append(outstr)
	torrent_data = {}
	for line in outlist:
		data = {}
		if line is not None:
			if line.split('|')[0] == 'ID' or line.split('|')[0] == 'Sum:':
				pass
			else:
				chunks = line.split('|')
				tid = chunks[0]
				data['percent'] = chunks[1]
				data['have'] = chunks[2]
				data['eta'] = chunks[3]
				data['up'] = chunks[4]
				data['down'] = chunks[5]
				data['ratio'] = chunks[6]
				data['status'] = chunks[7]
				data['name'] = chunks[8]
				torrent_data[tid] = data
	#print (torrent_data)
	return torrent_data


def get_info(tid, torrent_data=None):
	com = ("transmission-remote -t" + str(tid) + " --files")
	lines = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode().split("\n")
	outlist = []
	for line in lines:
		if line is not None:
			newline = []
			outstr = None
			line = line.strip()
			chunks = line.split(' ')
			_list = []
			for chunk in chunks:
				if chunk is not None:
					chunk = str(chunk.strip())
					print (type(chunk), chunk)
					if ':' in chunk:
						chunk = chunk.split(':')[0]
						if chunk.isnumeric():
							_list.append(chunk)
			n = "|"
			newline = n.join(_list)
			print ("Newline:", newline)
			outlist.append(newline)
	#n = "\n"
	#trimmed = n.join(outlist)
	#com = ("echo '" + trimmed + "' | grep -v '#' | grep -v 'None'")
	#trimmed = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode().split("\n")
	#output = n.join(trimmed)
	
	print (outlist)
#	return files
				
