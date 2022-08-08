import np
from np.utils.query_series import tmdb_query_series as query_series

pbdl = np.pbdl()

def add_series(filepath, series_name=None, season=None, episode_number=None):
	if series_name is None:
		series_name = input("Enter series name: ")
	if season is None:
		season = input("Enter season number ")
	if episode_number is None:
		episode_number = input("Enter episode number ")
	data = query_series(series_name, season, episode_number)
	episode_number = str(episode_number)
	season = str(season)
	try:
		tmdbid = data['tmdbid']
	except:
		tmdbid = 'None'

	try:
		episode_name = data['episode_name']
	except:
		episode_name = 'None'
	try:
		description = data['description']
	except:
		description = "No description available"
	try:
		air_date = data['air_date']
	except:
		air_date = 'None'
	try:
		still_path = data['still_path']
	except:
		still_path = "https://www.eglsf.info/wp-content/uploads/image-missing.png"
	if "'" in description:
		chunks = description.split("'")
		out = ''
		for chunk in chunks:
			out = (f"{out}{chunk}")
		description = out
	if "'" in episode_name:
		chunks = episode_name.split("'")
		out = ''
		for chunk in chunks:
			out = (f"{out}{chunk}")
		episode_name = out
	sql_string = f"INSERT into series (isactive, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, filepath) VALUES (1, '{series_name}', '{tmdbid}', {season}, {episode_number}, '{episode_name}', '{description}', '{air_date}', '{still_path}', '{filepath}');"
	ret = np.addtodb('series', sql_string)
	return ret

