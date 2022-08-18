from distutils.core import setup

setup(name='np',
	version='1.0',
	description='NPlayer media player and media management system',
	author='Matt McClellan',
	author_email='darthmonkey2004@gmail.com',
	url='http://nplayer.simiantech.biz/',
	packages=['np', 'np.core', 'np.utils'],
	package_dir={'np': 'np', 'np.core': 'np/core', 'np.utils': 'np/utils', 'np.np': 'np.np'},
	scripts=['install_np.sh', 'np/scripts/mkmedialist', 'np/scripts/np.remote', 'np/scripts/write_client_html', 'np/np'],
	data_files=['poster.png'],
	)
