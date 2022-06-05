#!/bin/bash

setup_packages() {
	sudo apt-get -y install imagemagick git python3-pip
}

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
