#!/bin/bash

setup_packages() {
	sudo apt-get -y install imagemagick git python3-pip
}

check_path() {
	inpath=$(echo "$PATH" | grep ".local/bin")
	if [ -n "$inpath" ]; then
		echo "Already in path!"
	else
		echo "Note: this will ammend your current .bashrc to include the local bin directory in your path. You may restore using 'restore_path' function in this script. No changes will be made if bashrc is already patched or .local/bin is already in PATH variable."
		read -p "Continue?: " cont
		if [ "$cont" = "y" ]; then
			echo "$PATH" > ~/oldpath.temp
			echo "Backed up old path variable to '$HOME/oldpath.temp'"
			cd ~/
			path="$PATH"
			newpath="$path:/home/$USER/.local/bin"
			hasline=$(cat ~/.bashrc | grep "export PATH=")
			if [ -n "$hasline" ]; then
				echo "Already patched! Skipping..."
			else		
				echo "export PATH=$newpath" >> ~/.bashrc
				. ~/.bashrc
				echo ".bashrc file patched and reloaded! Executable dirctory should be reachable from cli"
			fi
		else
			echo "User aborted!"
		fi
	fi
}

restore_path() {
	if [ -f "$HOME/oldpath.temp" ]; then
		path=$(cat ~/oldpath.temp)
	else
		echo "Backup path not found! Please enter new path value: " path
	fi
	echo "Restoring path variable from backup:"
	echo "Current: '$PATH'"
	echo "Replacing with: '$path'"
	read -p "Press 'y' to continue: " yn
	if [ "$yn" != "y" ]; then
		echo "Aborting..."
		exit 1
	else
		export PATH="$path"
	fi
	read -p "Preparing to open .bashrc for editing. Locate the bottom line that contains 'export PATH=' and remove it, or comment it out with '#'. Press a key when ready: " ak
	hasnano=$(which nano)
	hasgedit=$(which gedit)
	hasvim=$(which vim)
	if [ -n "$hasnano" ]; then
		prog="nano"
	elif [ -n "$hasgedit" ]; then
		prog="gedit"
	elif [ -n "$hasvim" ]; then
		prog="vim"
	fi
	$prog ~/.bashrc
	echo "Reloading .bashrc..."
	. ~/.bashrc
	echo "Done!"
	exit 0		
}

check_path
set_ssh() {
	read -p "Enter remote ip:" remote_ip
	read -p "Use user '$USER'?" yn
	if [ "$yn" = "y" ]; then
		user="$USER"
	else
		read -p "Enter remote user name: " user
	fi
	echo "Generating key pair..."
	ssh-keygen
	ssh-copy-id "$USER@$remote_ip"
	echo "Ssh authentication complete."
}

read -p "Set up ssh authentication?" yn
if [ "$yn" = "y" ]; then
	set_ssh
fi
haspip=$(which pip3)
if [ -z "$haspip" ]; then
	echo "Pypi for python3 not found. Installing packages..."
	setup_packages
fi
if [ -n "$1" ]; then
	np_dir="$1"
else
	read -p "python_np install directory not provided. Download?" yn
	if [ "$yn" = "y" ]; then
		cd ~/
		hasgit=$(which git)
		if [ -z "$hasgit" ]; then
			echo "Git not installed. Installing packages..."
			setup_packages
		fi
		np_dir="$HOME/python_np"
	else
		read -p "Please enter path python_np folder:" np_dir
	fi
fi
if [ -z "$np_dir" ]; then
	np_dir="$HOME/python_np"
fi
file=$(ls $np_dir/dist/*.tar.gz)
pip3 install "$file" -r "$np_dir/requirements.txt"
