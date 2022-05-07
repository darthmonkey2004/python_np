from distutils.core import setup
import setuptools

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]
setup(name='np',
	version='1.0',
	description='NPlayer media player and media management system',
	author='Matt McClellan',
	author_email='monkey@simiantech.biz',
	url='http://nplayer.simiantech.biz/',
	packages=['np', 'np.core', 'np.utils'],
	package_dir={'np': 'np', 'np.core': 'np/core', 'np.utils': 'np/utils', 'np.np': 'np.np'},
	scripts=['scripts/mkmedialist', 'scripts/np.remote'],
	data_files=['poster.png'],
	install_requires=REQUIREMENTS,
	entry_points={'console_scripts': ['np=np.main:start']}
	)
