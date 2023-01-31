from np.core.playlist import get_series_names
import subprocess
import os
from np.core.log import np_logger
log = np_logger().log_msg

class dbfixer():
	def __init__(self):
		self.unique_id = 0
		self.tables = ['movies', 'series', 'music']
		self.dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
		self.table = self.tables[0]
		self.backup_dir = os.path.join(os.path.expanduser("~"), '.np', 'db_backups')
		self.current_backup = None
		if not os.path.exists(self.backup_dir):
			print("Backup directory doesn't exist! Creating...")
			ret, msg = self.shell(f"mkdir -p \"{self.backup_dir}\"")
	def set_table(self, table, modified=False):
		self.table = table
		if not modified:
			temp_sql = os.path.join(os.path.expanduser("~"), '.np', f"{self.table}.backup.sql")
		else:
			temp_sql = os.path.join(os.path.expanduser("~"), '.np', f"{self.table}.backup.modified.sql")
		return temp_sql
	def backup_db(self, backup_dir=None):
		if backup_dir is not None:
			self.backup_dir = backup_dir
		self.current_backup = self.get_backup_filename()
		ret, msg = self.shell(f"cp \"{self.dbfile}\" \"{self.current_backup}\"")
		if not ret:
			print("Couldn't create database backup:{msg}!")
			input("Press enter to continue, or ctrl+c to abort..")
	def list_backups(self, backup_dir=None):
		if backup_dir is not None:
			self.backup_dir = backup_dir
		ret, files = self.shell(f"find \"{self.backup_dir}\" -name \"*.db\"")
		if not ret or files is None:
			print("No backups found!")
			return []
		return files.split("\n")
	def get_backup_filename(self, backup_dir=None):
		if backup_dir is not None:
			self.backup_dir = backup_dir
		ct = len(self.list_backups()) + 1
		return os.path.join(self.backup_dir, f"nplayer.backup.{ct}.db")
	def dump(self, table=None):
		if table is not None:
			self.table = table
		temp_sql = self.set_table(self.table)
		ret, msg = self.shell(f"sqlite3 \"{self.dbfile}\" \".dump {table}\" > \"{temp_sql}\"")
		if not ret:
			print(f"Error backing up table({self.table}):{msg}")
			input("Press enter to continue, or ctrl+c to abort..")

	def restore(self, table=None):
		if table is not None:
			self.table = table
		temp_sql = self.set_table(self.table, modified=True)
		ret, msg = self.shell(f"sqlite3 \"{self.dbfile}\" \"drop table {self.table};\"")
		if not ret:
			print(f"Error dropping table({self.table}):{msg}")
			input("Press enter to continue, or ctrl+c to abort..")
		ret, msg = self.shell(f"cat \"{temp_sql}\" | sqlite3 \"{self.dbfile}\"")
		if not ret:
			print(f"Error restoring {table} data:{msg}")
			input("Press enter to continue, or ctrl+c to abort..")

	def shell(self, com):
		ret = False
		data = None
		try:
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret != '':
				if 'Error' in ret:
					data = ret
					ret = False
				else:
					data = ret
					ret = True
			else:
				ret = True
				data = None
		except Exception as e:
			print("transform_unique_id.shell():Error! {e}")
			data = e
			ret = False
		return ret, data
	def write(self, table=None, data=[]):
		if table is not None:
			self.table = table
		j = "\n"
		data = j.join(data)
		temp_sql = self.set_table(self.table, modified=True)
		with open (temp_sql, 'w') as f:
			f.write(data)
			f.close()
		print(f"Updated sql file for :{self.table} ({temp_sql})!")
		return

	def read_backup(self, table=None):
		if table is not None:
			self.table = table
		temp_sql = self.set_table(self.table)
		with open(temp_sql, 'r') as f:
			data = f.read().split("\n")
			f.close()
		return data



	def replace_id(self, table=None):
		if table is not None:
			self.table = table
		out = []
		print(f"reading sql file(table:{table}...")
		data = self.read_backup(self.table)
		ct = len(data)
		totalpos = 0
		for line in data:
			totalpos += 1
			if 'PRAGMA' in line or 'BEGIN TRANSACTION;' in line or 'CREATE TABLE' in line or 'COMMIT;' in line:
				out.append(line)
				pass
			else:
				if totalpos < ct:
					self.unique_id += 1
					print(f"unique_id:{self.unique_id}")
					s = f"INSERT INTO {self.table} VALUES("
					_id = line.split(f"INSERT INTO {self.table} VALUES(")[1].split(',')[0]
					s = f"{s}{_id},"
					remainder = line.split(s)[1]
					j = f"INSERT INTO {self.table} VALUES({self.unique_id},"
					line = f"{j}{remainder}"
					out.append(line)
				else:
					out.append(line)
					print(f"table {self.table} done!")
					break
		if data == out:
			print("No changes made to data!")
			return False
		else:
			self.write(self.table, out)
			return True

	def fix_unique_id(self, table=None):
		self.backup_db()
		if table is not None:
			tables = [table]
		else:
			tables = self.tables
		for table in tables:
			self.table = table
			print(f"Backing up table:{self.table}..")
			self.dump(self.table)
			print(f"Processing table:{self.table}....")
			ret = self.replace_id(self.table)
			if ret:
				print(f"Restoring modified table:{self.table}...")
				self.restore(self.table)
		print("Done!")

	def correct_titles(self, table=None):
		series_names = get_series_names()
		for series_name in series_names:
			sn = series_name.title()
			if sn != series_name:
				ret = sqlite3(f"update series set series_name = \'{sn}\' where series_name like \'{series_name}\';")
				if ret is not None:
					log(f"Whoops! Couldn't update {series_name} with {sn}! Reason:{ret}", 'error')
					return False
				else:
					log(f"Updated {series_name} to {sn}!", 'info')
		return True
					


	def fix(self, function='all', table=None):
		if function == 'unique_id' or function == 'all':
			log(f"dbfixer.fix():Running unique_id fix...", 'info')
			self.fix_unique_id(table=table)
		if function == 'correct_titles' or function == 'all':
			log(f"dbfixer.fix():Running series_name capitalization fix...", 'info')
			self.correct_titles(table=table)


if __name__ == "__main__":
	import sys
	try:
		table = sys.argv[1]
	except:
		table = None
	try:
		function = sys.argv[2]
	except:
		function = 'all'
	if table is None:
		fixer = dbfixer()
		fixer.fix(function=function)
	else:
		fixer = dbfixer(table=table)
		fixer.fix(function=function, table=table)
