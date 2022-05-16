import np
import logging
import datetime

class np_logger(conf, logfile):
	def __init__(self):
		global conf
		self.conf = conf
		self.log_type = 'debug'
		self.log_level = getattr(logging, self.log_type.upper(), None)
		logging.basicConfig(filename=np.LOGFILE, level=self.log_level)
		self.msg = None
		t = datetime.datetime.now()
		self.ts = (str(t.day) + "-" + str(t.month) + "-" + str(t.year) + " " + str(t.hour) + ":" + str(t.minute) + ":" + str(t.second) + ":" + str(t.microsecond))
		try:
			self.debug = self.conf['debug']
		except Exception as e:
			print (f"Error: debug setting not in conf: {e}")
	def log_msg(self, *args):
		print (self.msg)
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
