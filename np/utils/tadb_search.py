import requests
import json
#This api appears to be fairly convoluted in usage... the initial lookups i tried, only 3 of 169 returned data.
#gotta be doing something wrong, but i'm ready to move on here.

def lookup(artist, title):
	j = '+'
	querystring = {"s":artist,"t":title}
	url = "https://theaudiodb.p.rapidapi.com/searchtrack.php"
	headers = {
		"X-RapidAPI-Key": "TiV3k10QNXmshRyyCcCXPKyq1gYJp1oKBNKjsn3ICR7bpX3yAB",
		"X-RapidAPI-Host": "theaudiodb.p.rapidapi.com"
	}
	r = requests.request("GET", url, headers=headers, params=querystring)
	code = r.status_code
	if code == 200:
		out = {}
		data = r.text
		data = json.loads(data)
		try:
			track_data = data['track'][0]
			out['isactive'] = 1
			out['results'] = True
			if track_data['strTrack'] is not None:
				out['title'] = track_data['strTrack']
			else:
				out['title'] = title
			if track_data['strAlbum'] is not None:
				out['album'] = track_data['strAlbum']
			else:
				out['album'] = 'Unknown'
			if track_data['strMusicBrainzAlbumID'] is not None:
				out['album_id'] = track_data['strMusicBrainzAlbumID']
			else:
				out['album_id'] = 'Unknown'
			if track_data['strMusicBrainzArtistID'] is not None:
				out['artist_id'] = track_data['strMusicBrainzArtistID']
			else:
				out['artist_id'] = 'Unknown'
			if track_data['strArtist'] is not None:
				out['artist'] = track_data['strArtist']
			else:
				out['artist'] = artist
			if track_data['strGenre'] is not None:
				out['genre'] = track_data['strGenre']
			else:
				out['genre'] = 'Unknown'
			if track_data['intTrackNumber'] is not None:
				out['track'] = track_data['intTrackNumber']
			else:
				out['track'] = 0
			if track_data['strMusicBrainzID'] is not None:
				out['mbid'] = track_data['strMusicBrainzID']
			else:
				out['mbid'] = 'Unknown'
			out['filepath'] = 'null'
			return out
		except Exception as e:
			out['isactive'] = 1
			out['title'] = title
			out['album'] = 'Unknown'
			out['results'] = False
			out['album_id'] = 'Unknown'
			out['artist_id'] = 'Unknown'
			out['artist'] = artist
			out['genre'] = 'Unknown'
			out['track'] = 0
			out['mbid'] = 'Unknown'
			out['filepath'] = 'null'
			return out
	

if __name__ == "__main__":
	import sys
	artist = sys.argv[1]
	album = sys.argv[2]
	ret = lookup(artist, album)
	print (ret)
