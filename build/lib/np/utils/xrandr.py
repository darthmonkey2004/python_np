#!/usr/bin/env python3
import subprocess

def xrandr():
	ret = []
	out = {}
	s = subprocess.check_output('xrandr', shell=True)
	ret = s.decode().split('\n')
	id = -1
	for item in ret:
		screen = {}
		if 'connected' in item:
			chunks = item.split(' ')
			state = str(chunks[1])
			if state != 'disconnected':
				id = id + 1
				screen['name'] = chunks[0]
				info = chunks[2]
				if info == 'primary':
					screen['primary'] = True
					info = chunks[3]
				else:
					screen['primary'] = False
				data = info.split('+')
				screen['pos_x'] = data[1]
				screen['pos_y'] = data[2]
				screen['w'], screen['h'] = str(data[0]).split('x')
				out[id] = screen
			
	return out
if __name__ == "__main__":
	ret = xrandr()
	print (ret)
