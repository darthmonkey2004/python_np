from PySimpleGUI import *
import inspect
elements_list = ['Radio', 'Checkbox', 'Listbox', 'Input', 'Text', 'Image', 'Button', 'TabGroup', 'Slider', 'ButtonMenu', 'Window', 'Titlebar', 'one_line_progress_meter', 'Tab', 'Canvas', 'Column', 'Frame', 'Graph', 'HorizontalSeparator', 'Menu', 'MenubarCustom', 'Multiline', 'OptionMenu', 'Pane', 'ProgressBar', 'Sizer', 'Sizegrip', 'bind', 'Spin', 'StatusBar', 'Table', 'Titlebar', 'Tree', 'Node', 'insert', 'VerticalSeparator']

class add_elem():
	def __init__(self):

		self.layout = []#main element container, use for insertion into organizers (table, pane, window, tab/tabgroup)
		self.window = None
		self.args = {}
		self.elem_keys = []
		self.elem_defaults = []


	def get_defaults(self, elem):
		self.elem_defaults = inspect.getargspec(globals()[elem]).defaults
		return self.elem_defaults


	def get_element_args(self, elem):
		try:
			self.elem_keys = inspect.getargspec(globals()[elem]).args
			return self.elem_keys
		except Exception as e:
			raise Exception('get_element_args failed to return data, is specified element name misspelled (camel cased?)', 'error=' + e, 'element=' + elem, 'ret=' + self.elem_keys)


	def create_element(self, elem, args={}):
		pos = -1
		argdict = {}
		sig = inspect.signature(globals()[elem])
		sig_keys = list(sig.parameters.keys())
		for param in sig.parameters.values():
			pos = pos + 1
			key = sig_keys[pos]
			if param.default is param.empty and key not in list(args.keys()):
				raise Exception ('Required value not provided!', param, args, sig)
			elif param.default is not param.empty and key not in list(args.keys()):
				argdict[key] = param.default
			elif key in list(args.keys()):
				argdict[key] = args[key]
		vals_list = list(argdict.keys())
		vals = tuple(vals_list)
		element = globals()[elem](vals)
		return element

	def create(self, elem, args=[]):
		pos = -1
		args_dict = {}
		for arg in args:
			pos = pos + 1
			if pos == 0:
				key = 'primary'
				val = arg
			else:
				try:
					key = arg.split('=')[0]
					val = arg.split('=')[1]
				except Exception as e:
					print (e, arg, key, val)
					break
			args_dict[key] = val
		return self.create_element(elem, args_dict)
	
	
	def read_gui_config(self, config_path):
		with open(config_path, 'r') as f:
			self.gui_data = pickle.load(f)
		f.close()
		return self.gui_data


	#def render(self, gui_data):
		
		


if __name__ == "__main__":
	gui = gui()
	args = {}
	args['button_text'] = 'hello'
	args['key'] = '-howdykey-'
	ret = gui.create_element('Button', args)
	data = dir(ret)
	for item in data:
		data2 = dir(data[item])
		print (data2)
