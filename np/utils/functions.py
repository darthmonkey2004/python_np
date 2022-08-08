import subprocess

def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}'"
	return subprocess.check_output(com, shell=True).decode().strip()
