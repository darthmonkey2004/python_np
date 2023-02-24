from dl_manager import *
d = downloader()
data = {}
data['series_name'] = 'Archer'
data['tmdbid'] = d.series_name_to_tmdbid(data['series_name'])
#data['season'] = 0
#data['episode_number'] = 1
d.update(data)



#out = filter(data)
#print(out)
print(d.win['-SERIES_NAME-'].get())
print(d.win['-EPISODE_NUMBER-'].get())
input()
