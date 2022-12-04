import os

def cli_opts(user=None, pw=None):
	user = os.path.expanduser("~").split('/home/')[1]	
	cli_opts = {}
	cli_opts['user'] = f"--sout-http-user={user}"
	cli_opts['pw'] = "--sout-http-pwd={pw}"
	#cli_opts['mime'] = f"--sout-http-mime={mime}"
	cli_opts['Metacube'] = ["--sout-http-metacube", "--no-sout-http-metacube"]
	cli_opts['file_out_overwrite'] = ["--sout-file-overwrite", "--no-sout-file-overwrite"]
	cli_opts['file_out_append'] = ["--sout-file-append", "--no-sout-file-append"]
	cli_opts['file_out_time_formatted'] = ["--sout-file-format", "--no-sout-file-format"]
	return cli_opts
