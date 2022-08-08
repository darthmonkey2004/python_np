import pickle
import logging
import datetime
import os
from np.core.xrandr import xrandr


global conf, LOGFILE, CONFFILE
home = os.path.expanduser("~")
DATA_DIR = (user + os.path.sep + ".np")
LOGFILE = f"{DATA_DIR}/nplayer.log"
CONFFILE = f"{DATA_DIR}/nplayer.conf"




def readConf():
	try:
		with open(CONFFILE, 'rb') as f:
			data = pickle.load(f)
		f.close()
		return data
	except Exception as e:
		print(f"Exception in readConf: {e}")
		return None
	


def writeConf(data, CONFFILE=None):
	if CONFFILE == None:
		CONFFILE == f"{DATA_DIR}/nplayer.conf"

	try:
		logger = log().log
	except:
		pass
	try:
		with open(CONFFILE, 'wb') as f:
			pickle.dump(data, f)
		f.close()
		try:
			logger('core.py, writeConf: Conf updated!', 'info')
		except:
			print('core.py, writeConf: Conf updated!, logger uninitialized')
		return True
	except Exception as e:
		print(f"Exception in log.py, writeConf, line 43:{e}")
		return False


def initConf():
	user = os.getlogin()
	#print ("Init conf running!")
	conf = {}
	conf['GUI_RESET'] = False
	conf['play_type'] = 'series'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	conf['screen'] = 1
	conf['fullscreen'] = 1
	conf['screens'] = {}
	conf['pos_x'] = None
	conf['pos_y'] = None
	conf['w'] = None
	conf['h'] = None
	conf['scale'] = 2.799999952316284
	conf['volume'] = 100
	conf['rotate'] = 0
	conf['shuffle'] = 1
	conf['mute'] = False
	conf['video_method'] = 'internal'
	conf['video_methods'] = ['external', 'internal']#select between external video player window and internal xwindow widget
	conf['video_player'] = 'vlc'
	conf['video_players'] = ['vlc', 'mplayer', 'mpv', 'cv2']# list of usuable playback engines (internal are cv2 and vlc, external are all
	screens = xrandr()
	conf['screens'] = screens
	conf['nowplaying'] = {}
	conf['nowplaying']['filepath'] = None
	conf['nowplaying']['play_pos'] = None
	conf['vlc'] = {}
	conf['vlc']['opts'] = "--no-xlib"
	conf['debug'] = True
	conf['network_modes'] = {}
	conf['network_modes']['control_modes'] = ['local', 'remote', 'server']
	conf['network_modes']['media_modes'] = ['local', 'remote']
	conf['network_mode'] = {}
	conf['network_mode']['media_mode'] = 'local'
	conf['network_mode']['media_host'] = None
	conf['network_mode']['media_user'] = user
	conf['network_mode']['control_mode'] = 'local'
	conf['network_mode']['control_host'] = None
	conf['network_mode']['control_user'] = user
	conf['network_mode']['control_port'] = 4444
	conf['remote'] = {}
	conf['debug'] = False
	conf['init'] = True
	#conf['watched_devices'] = ['/dev/input/event11', '/dev/input/event2']
	#conf['grab_devices'] = ['/dev/input/event11']
	ret = writeConf(conf)
	return conf

conf = readConf()
if conf == None:
	conf = initConf()
class np_logger():
	def __init__(self):
		global conf
		self.conf = conf
		self.log_type = 'debug'
		self.log_level = getattr(logging, self.log_type.upper(), None)
		logging.basicConfig(filename=LOGFILE, level=self.log_level)
		self.msg = None
		t = datetime.datetime.now()
		self.ts = (str(t.day) + "-" + str(t.month) + "-" + str(t.year) + " " + str(t.hour) + ":" + str(t.minute) + ":" + str(t.second) + ":" + str(t.microsecond))
		if self.conf['debug'] == None:
			self.conf = np.initConf()
			np.writeConf(self.conf)
			np.log(f"Over wrote conf file (empty debug string. Data: {self.conf}", 'warning')
		try:
			self.debug = self.conf['debug']
		except Exception as e:
			print (f"Error in log.py: debug setting not in conf: {e}")
	def log_msg(self, *args):
		#print (self.msg)
		pos = -1
		for arg in args:
			pos = pos + 1
			if pos == 0:
				self.msg = (self.ts + "--" + str(arg))
			elif pos == 1:
				self.log_type = arg
		if not isinstance(self.log_level, int):
			raise ValueError('Invalid log level: %s' % self.log_type)
			return
		#print(f"Log level: {self.log_level}")
		if self.msg == None:
			raise ValueError('No message data provided!')
		if self.debug == True:
			print ("DEBUG MESSAGE:", self.msg)
		if self.log_level == 10:#debug level
			logging.debug(self.msg)
		elif self.log_level == 20:
			logging.info(self.msg)
		elif self.log_level == 30:
			logging.warning(self.msg)
		elif self.log_level == 40:
			logging.error(self.msg)
			try:
				print("Nplayer logged an error:", self.msg)
			except Exception as e:
				ouch=("Unable to print error message, background process(?)", self.msg, e)
				logging.error(ouch)
				raise RuntimeError(ouch) from e
				print (f"Log class exiting with errors: {e}")
				return
		return
