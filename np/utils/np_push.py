from tqdm import tqdm
import os
import subprocess
import time
from np.utils.git import *

def set_gitdir():
	base_dir = os.getcwd()
	path = None
	com = f"ls -d python_np"
	try:
		path = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print(f"Error: {e}")
	return os.path.join(base_dir, path)

BACKUPDIR = os.path.join(os.getcwd(), 'python_np_backups')
TARFILE = os.path.join(BACKUPDIR, f"np_backup.{time.time()}.tar.gz")
GITDIR = set_gitdir()
if GITDIR is None:
	GITDIR = input("Repo directory not found in relative path! Enter local repository path now:")
VERSIONFILE = os.path.join(os.path.expanduser("~"), '.np', 'VERSION.txt')
git = git(path=GITDIR)

def test_backup_dir():
	if not os.path.exists(BACKUPDIR):
		ret = subprocess.check_output(f"mkdir -p \"{BACKUPDIR}\"", shell=True).decode().strip()
		if ret != '':
			print("couldn't create backup directory! ({ret})!")
			return False
	return True


def write_version(version, subversion):
	with open(VERSIONFILE, 'w') as f:	
		txt = f"{version}.{subversion}"
		f.write(txt)
		f.close()
		
def get_version():
	if os.path.exists(VERSIONFILE):
		with open(VERSIONFILE, 'r') as f:
			version, subversion = f.read().split('.')
			version, subversion = int(version), int(subversion)
			f.close()
	else:
		version, subversion = 1, 0
		write_version(version, subversion)
	return version, subversion


def increment_version(t='sv'):
	v, sv = get_version()
	if t != 'sv' and t != 'v':
		print("Invalid versinon increment type ({t}). Valid types are 'v' (full version) or 'sv' (sub-version)")
	elif t == 'sv':
		sv += 1
	elif t == 'v':
		v += 1
	write_version(v, sv)
	return v, sv
	
	

def rm(path):
	ret = None
	if os.path.isdir(path):
		com = f"rm -rf \"{path}\""
	else:
		com = f"rm \"{path}\""
	if os.path.exists(path):
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret == '':
			ret = None
	else:
		ret = f"Error: target doesn't exist! ({path})"
	if ret is not None:
		print(ret)
		return False
	else:
		return True


def clean_local_install():
	path = os.path.join(os.path.expanduser("~"), '.local', 'lib', 'python3.8', 'site-packages', 'np')
	todel = [os.path.join(path, 'utils', 'pbdl', 'downloads.dat'), os.path.join(path, 'utils', 'pbdl', 'poster.jpg'), os.path.join(path, 'utils', 'pbdl', 'poster.png'), os.path.join(path, 'utils', 'pbdl', 'temp.settings.json'), os.path.join(path, '__pycache__'), os.path.join(path, 'core', '__pycache__'), os.path.join(path, 'utils', '__pycache__'), os.path.join(path, 'utils', 'pbdl', '__pycache__'), os.path.join(path, 'ws', '__pycache__')]
	for path in todel:
		if not rm(path):
			break


def backup(gitdir=None):
	if not test_backup_dir():
		return False
	if gitdir is None:
		gitdir = GITDIR
	com = f"tar -zcvf \"{TARFILE}\" \"{gitdir}\" > /dev/null"
	ret = True
	msg = None
	try:
		print(f"Backing up dir \"{gitdir}\" to \"{TARFILE}\"...")
		msg = subprocess.check_output(com, shell=True).decode().strip()
		if msg == '':
			msg = None
			ret = True
		else:
			ret = False
	except Exception as e:
		msg = e
		ret = False
	return ret, msg


def commit(gitdir=None, comment="Generic commit, executed from nppush.py"):
	if gitdir is not None:
		GITDIR = gitdir
	clean_local_install()
	ret, msg = backup(GITDIR)
	if not ret:
		print(msg)
		input()
		return False
	v, sv = increment_version()
	git.add()
	git.commit(commit_message=comment)
