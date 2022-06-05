import np

def init_viewer():
	conf = np.readConf()
	screen = conf['screen']
	displays = np.xrandr()
	viewer_w = displays[screen]['w']
	viewer_h = displays[screen]['h']
	viewer_x = displays[screen]['pos_x']
	viewer_y = displays[screen]['pos_y']
	conf['windows']['viewer'][screen]['x'] = viewer_x
	conf['windows']['viewer'][screen]['y'] = viewer_y
	conf['windows']['viewer'][screen]['w'] = viewer_w
	conf['windows']['viewer'][screen]['h'] = viewer_h
	np.writeConf(conf)
	np.log(f"Viewer screen updated!")
	return conf['windows']

def init_gui():
	conf = np.readConf()
	screen = conf['screen']
	displays = np.xrandr()
	if screen == 0:
		gui_visible_x = displays[1]['pos_x']
		gui_visible_y = displays[1]['pos_y']
	elif screen == 1:
		gui_visible_x = displays[0]['pos_x']
		gui_visible_y = displays[0]['pos_y']
	gui_w = 1024
	gui_h = 600
	conf['windows']['gui']['visible'][screen]['x'] = gui_visible_x
	conf['windows']['gui']['visible'][screen]['y'] = gui_visible_y
	conf['windows']['gui']['visible'][screen]['w'] = gui_w
	conf['windows']['gui']['visible'][screen]['h'] = gui_h
	conf['windows']['gui']['hidden'][screen]['x'] = gui_visible_x
	conf['windows']['gui']['hidden'][screen]['y'] = gui_visible_y
	conf['windows']['gui']['hidden'][screen]['w'] = gui_w
	conf['windows']['gui']['hidden'][screen]['h'] = gui_h
	np.writeConf(conf)
	np.log(f"GUI screen updated!")
	return conf['windows']

def init_screens(screen=None, reset=False):
	conf = np.readConf()
	if reset == True:
		if screen == None:
			conf['windows'] = init_gui()
			conf['windows'] = init_viewer()
		elif screen == 'viewer':
			conf['windows'] = init_viewer()
		elif screen == 'gui':
			conf['windows'] = init_gui()
		return conf['windows']
	elif reset == False:
		return conf['windows']
	
	

if __name__ == "__main__":
	init_screens()
