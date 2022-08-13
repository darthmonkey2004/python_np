#!/bin/bash


gdrive_setup() {
	sudo add-apt-repository ppa:alessandro-strada/ppa
	sudo apt update && sudo apt install google-drive-ocamlfuse
	google-drive-ocamlfuse
	
}
mount_gdrive() {
	if [ ! -d "$HOME/gdrive" ]; then
		mkdir "$HOME/gdrive"
	fi
	google-drive-ocamlfuse "$HOME/gdrive"
	cd "$HOME/gdrive"
	if [ ! -d ".np" ]; then
		mkdir .np
	fi
}
unmount_gdrive() {
	fusermount -u ~/google-drive
}

np_setup() {
	cd "$HOME/python_np"
	pip3 install --user 'dist/np-1.0.tar.gz' -r requirements.txt
	dbfile="$HOME/.np/nplayer.db"
	cd $HOME/.np
	if [ ! -f "$dbfile" ]; then
		echo "Starting setup.."
		python3 -c "import np; np.set_media_paths()"
		echo "Creating sql database..."
		python3 -c "import np; np.sqldb.create_db()"
		music_dir=$(python3 -c "import np; print(np.MUSIC_DIR)")
		movies_dir=$(python3 -c "import np; print(np.MOVIES_DIR)")
		series_dir=$(python3 -c "import np; print(np.SERIES_DIR)")
		python3 -c "import np; print ('Scanning music..'); np.scan_music($music_dir)"
		python3 -c "import np; print ('Scanning movies..'); np.scan_music($movies_dir)"
		python3 -c "import np; print ('Scanning series..'); np.scan_music($series_dir)"
	fi
	logfile="$HOME/.np/nplayer.log"
	if [ ! -f "$logfile" ]; then
		touch "$logfile"
	fi
}


need_vlc=$(sudo dpkg -l | grep "python3-vlc")
if [ -z "$need_vlc" ]; then
	 sudo apt-get install -y python3-vlc libsecret-tools curl transmission-daemon imagemagick
fi
hassqllite3=$(which sqlite3)
if [ -z "$hassqllite3" ]; then
	sudo apt-get install -y sqlite3
fi
hasgit=$(which git)
haspip=$(which pip3)
if [ -z "$haspip" ]; then
	sudo apt-get install -y python3-pip
fi
hastk=$(pip3 list | grep "tk")
if [ -z "$hastk" ]; then
	pip3 install tk
fi
python3 -c "from PIL import Image, ImageTk" > out 2>errors.txt
rm out
needpil=$(cat errors.txt)
rm errors.txt
if [ -n "$needpil" ]; then
	sudo apt-get install -y python3-pil python3-pil.imagetk python3-vlc
fi
dir="$HOME/.local/bin"
inpath=$(echo "$PATH" | grep "$dir")
inrc=$(cat ~/.bashrc | grep "export PATH")
if [ -z "$hasgit" ]; then
	sudo apt-get install -y git
fi
if [ -z "$inpath" ]; then
	export PATH="$PATH:$HOME/.local/bin"
fi
if [ -z "$inrc" ]; then
	echo "export PATH='$PATH'" >> ~/.bashrc
fi
. ~/.bashrc

np_setup;
