from distutils.core import setup
setup(name='np',
	version='1.0',
	description='NPlayer media player and media management system',
	author='Matt McClellan',
	author_email='monkey@simiantech.biz',
	url='http://nplayer.simiantech.biz/',
	packages=['np', 'np.core', 'np.utils'],
	package_dir={'np': 'np', 'np.core': 'np/core', 'np.utils': 'np/utils', 'np.np': 'np.np'},
	scripts=['np/np'],
	install_requires=['pygame-gui', 'eyed3', 'PySimpleGUI', 'evdev', 'python-vlc', 'get-video-properties']
	)
