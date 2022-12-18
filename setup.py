from distutils.core import setup

setup(name='np',
	version='1.0',
	description='NPlayer media player and media management system',
	author='Matt McClellan',
	author_email='darthmonkey2004@gmail.com',
	url='http://nplayer.simiantech.biz/',
	packages=['np', 'np.core', 'np.utils', 'np.ws'],
	package_dir={'np': 'np', 'np.core': 'np/core', 'np.utils': 'np/utils', 'np.np': 'dist/np.bin'},
	scripts=['scripts/install_np.sh', 'scripts/mkmedialist', 'scripts/np.remote', 'scripts/write_client_html'],
	data_files=['poster.png', 'README', 'requirements.txt', 'version.txt'],
	)
