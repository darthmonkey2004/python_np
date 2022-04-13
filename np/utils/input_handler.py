#!/usr/bin/env python3
import evdev


class input_handler():
	def __init__(self):
		self.devices = {}
		self.events = {}
		self.event = {}
		self.code = None
		self.type = None
		self.value = None
		self.targets = None
		

	def get_devices(self, devlist=None):
		if devlist == None:
			devlist = evdev.list_devices()
		self.devices = [evdev.InputDevice(path) for path in devlist]
		return self.devices

	
	def get_capabilities(self, device=None):
		if type(device) == str:
			device = evdev.InputDevice(device)
		capslist = []
		if device == None:
			for device in devices:
				self.devinfo[device.name]['caps'] = device.capabilities(verbose=True)
		else:
			self.devinfo[device.name]['caps'] = device.capabilities(verbose=True)
		return self.devinfo


	def get_leds(self, device=None):
		if type(device) == str:
			device = evdev.InputDevice(device)
		if device is not None:
			self.devinfo[device.name]['leds'] = device.leds(verbose=True)
		else:
			for device in devices:
				self.devinfo[device.name]['leds'] = device.leds(verbose=True)
		return self.devinfo


	def set_led(self, device, led, val):
		if type(device) == str:
			device = evdev.InputDevice(device)
		try:
			device.set_led(evdev.ecodes.led, val)
			return True
		except Exception as e:
			print ("Exception, line 43:", device.name, led, val, e)
			return False

	
	def get_active_keys(self, device=None):
		if type(device) == str:
			device = evdev.InputDevice(device)
		if device == None:
			for device in devices:
				self.devinfo[device.name]['active_keys'] = device.active_keys(verbose=True)
		else:
			self.devinfo[device.name]['active_keys'] = device.active_keys(verbose=True)
		return self.devinfo
				

	def get_events(self, targets):
		self.targets = targets
		valstr = None
		for device in self.targets:
			self.events[device.path] = {}
			devdict = self.events[device.path]
			while True:
				event = device.read_one()
				if event:
					code = event.code
					_type = event.type
					value = event.value
					if _type == evdev.ecodes.EV_KEY or event == 4 or code == 4:
						devdict['code'] = code
						devdict['type'] = _type
						devdict['value'] = value
					else:
						pass
						#print(device.name, code, _type, value)
				else:
					devdict = {}
					break
		return self.events

