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

add_to_favorites() {
	data=$(gsettings get org.gnome.shell favorite-apps)
	echo "_list = $data" > temp.py
	echo "if 'np.desktop' not in _list:" >> temp.py
	echo "	_list.append('np.desktop')" >> temp.py
	echo "print(_list)" >> temp.py
	newlist=$(python3 temp.py)
	gsettings set org.gnome.shell favorite-apps "$newlist"
	rm temp.py
}


write_desktop() {
	echo "[Desktop Entry]" > np.desktop
	echo "Version=1.0" >> np.desktop
	echo "Name=NPlayer" >> np.desktop
	echo "Comment=Media player and databasing package." >> np.desktop
	echo "Exec=np" >> np.desktop
	echo "Path=/home/monkey/.local" >> np.desktop
	echo "Icon=/home/monkey/.local/share/applications/poster.png" >> np.desktop
	echo "Terminal=false" >> np.desktop
	echo "Type=Application" >> np.desktop
	echo "Categories=Utility;AudioVideo;Audio;Video" >> np.desktop
	echo "StartupWMClass=GUI" >> np.desktop
	mv np.desktop "$HOME/.local/share/applications/np.desktop"
	cp poster.png "$HOME/.local/share/applications/poster.png"
	data=$(gsettings get org.gnome.shell favorite-apps)
	echo "_list = $data" > temp.py
	echo "if 'np.desktop' not in _list:" >> temp.py
	echo "	_list.append('np.desktop')" >> temp.py
	echo "print(_list)" >> temp.py
	newlist=$(python3 temp.py)
	gsettings set org.gnome.shell favorite-apps "$newlist"
	add_to_favorites;
}

version() {
	vfile=$(find $(pwd) -name "version.txt")
	cp "$vfile" "$HOME/.np/version.txt"
}

np_setup() {
	dir=$(pwd)
	dname=$(basename "$dir")
	if [ "$dname" = "python_np" ]; then
		pydir="$dir"
	else
		pydir="$dir/python_np"
	fi
	echo "Git repo dir: '$pydir'"
	if [ ! -d "$pydir" ]; then
		read -p "Enter path to git clone (python_np): " pydir
	fi
	cd "$pydir"
	pip3 install --user 'dist/np-1.0.tar.gz' -r requirements.txt
	dbfile="$HOME/.np/nplayer.db"
	if [ ! -d "$HOME/.np" ]; then
		mkdir "$HOME/.np"
	fi
	version;
	cd $HOME/.np
	if [ ! -f "$dbfile" ]; then
		cd "$HOME/.local/lib/python3.8/site-packages/np"
		echo "Starting setup.."
		python3 -c "import np; np.run_setup()"
		echo "Creating sql database..."
		python3 -c "import np; np.sqldb.create_db()"
		music_dir=$(python3 -c "import np; print(np.MUSIC_DIR)")
		movies_dir=$(python3 -c "import np; print(np.MOVIES_DIR)")
		series_dir=$(python3 -c "import np; print(np.SERIES_DIR)")
		if [ ! -d "$music_dir" ]; then
			mkdir -p "$music_dir"
		fi
		if [ ! -d "$movies_dir" ]; then
			mkdir -p "$movies_dir"
		fi
		if [ ! -d "$series_dir" ]; then
			mkdir -p "$series_dir"
		fi
		python3 -c "import np; print ('Scanning music..'); np.scan_music('$music_dir')"
		python3 -c "import np; print ('Scanning movies..'); np.scan_movies('$movies_dir')"
		python3 -c "import np; print ('Scanning series..'); np.scan_series('$series_dir')"
	fi
	logfile="$HOME/.np/nplayer.log"
	if [ ! -f "$logfile" ]; then
		touch "$logfile"
	fi
	host=$(python3 -c "import np; conf = np.readConf(); print(conf['remote']['server']['host'])")
	port=$(python3 -c "import np; conf = np.readConf(); print(conf['remote']['server']['port'])")
	write_client_html;
	write_desktop;
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
