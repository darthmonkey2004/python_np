#!/usr/bin/env python3

import pathlib
import np
import os

def run_setup():
	keys = ['media_directories', 'play_type', 'play_types', 'screen', 'fullscreen', 'screens', 'pos_x', 'pos_y', 'w', 'h', 'scale', 'volume', 'opts', 'rotate', 'shuffle', 'mute', 'video_method', 'video_methods', 'video_player', 'video_players', 'nowplaying', 'vlc', 'gui_data', 'windows', 'grab_devices']
	conf = {}
	for key in keys:
		conf[key] = {}
	media_dir = input("Enter primary media storage path: ")
	conf['media_directories']['main'] = media_dir
	conf['media_directories']['movies'] = (media_dir + os.path.sep + "Movies")
	conf['media_directories']['series'] = (media_dir + os.path.sep + "Series")
	conf['media_directories']['music'] = (media_dir + os.path.sep + "Music")
	conf['play_type'] = 'series'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	screen = 0
	conf['screen'] = screen
	conf['screens'] = np.xrandr()
	conf['pos_x'] = conf['screens'][screen]['x']
	conf['pos_y'] = conf['screens'][screen]['y']
	conf['w'] = conf['screens'][screen]['w']
	conf['h'] = conf['screens'][screen]['h']
	conf['scale'] = 0.0
	conf['volume'] = 100
	conf['vlc']['opts'] = '--no-xlib'
	conf['rotate'] = 0
	conf['shuffle'] = True
	conf['mute'] = False
	conf['video_method'] = 'internal'
	conf['video_methods'] = ['external', 'internal']
	conf['video_player'] = 'vlc'
	conf['video_players'] = ['vlc', 'mplayer', 'mpv', 'cv2']
	conf['nowplaying'] = ['filepath', 'play_pos']
	conf['windows'] = np.init_window_position()

if __name__ == "__main__":
	run_setup()
