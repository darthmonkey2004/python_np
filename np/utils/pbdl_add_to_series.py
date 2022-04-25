import np

pbdl = np.pbdl()

def add_series(data={}):
	try:
		series_name = data['series_name']
		tmdbid = data['tmdbid']
		season = data['season']
		episode_number = data['episode_number']
		episode_name = data['episode_name']
		description = data['description']
		air_date = data['air_date']
		still_path = data['still_path']
		duration = data['duration']
		filepath = data['filepath']
		md5 = data['md5']
		url = data['url']
	except Exception as e:
		print ("Data format error:", e)
		return False
	sql_string = ("INSERT into series (isactive, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, duration, filepath, md5, url) VALUES (1, " + series_name + ", " + str(tmdbid) + ", " + str(season) + ", " + str(episode_number) + ", " + episode_name + ", " + description + ", " + air_date + ", " + still_path + ", " + duration + ", " + filepath + ", " + md5 + ", " + url + ");")
	ret = pbdl.add_to_db(sql_string)
	return ret

