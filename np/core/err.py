import np.core.log as log
log = log.np_logger().log_msg

class err():
	def __init__(self):
		self.err_type = None
		self.msg = None
	def err(self, *args):
		pos = -1
		for arg in args:
			pos = pos + 1
			if pos == 0:
				self.msg = arg
			elif pos == 1:
				self.err_type = arg
		if self.err_type is None:
			self.err_type = RuntimeError
		if self.msg == None:
			log("No error message data provided!", 'error')
			raise RuntimeError('No message data provided!')
			return
		else:
			log(self.msg, 'error')
			raise self.err_type(self.msg)
			return

