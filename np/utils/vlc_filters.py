import vlc
from np.core.log import np_logger
log = np_logger().log_msg

def create_vlc_filters(t=None):
	if t is None:
		t = 'all'
	def create_audio_filters():
		VLC_AUDIO_FILTERS = []
		for f in vlc.Instance().audio_filter_list_get():
			n, x, y, x = f
			name = n.decode()
			name = ("audio:" + name)
			VLC_AUDIO_FILTERS.append(name)
		return VLC_AUDIO_FILTERS
	def create_video_filters():
		VLC_VIDEO_FILTERS = []
		for f in vlc.Instance().video_filter_list_get():
			n, x, y, x = f
			name = n.decode()
			name = ("video:" + name)
			VLC_VIDEO_FILTERS.append(name)
		return VLC_VIDEO_FILTERS
	if t == 'audio':
		return sorted(create_audio_filters())
	elif t == 'video':
		return sorted(create_video_filters())
	elif t == 'all':
		return [sorted(create_video_filters()), sorted(create_audio_filters())]
	else:
		log(f"Unknown argument provided for gui.create_vlc_filters(): Returning None...", 'warning')
		return None

