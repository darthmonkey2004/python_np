#!/bin/bash
if [ -f torrents.json ]; then mv torrents.json torrents.json.bak; fi
data='{"method":"torrent-get","arguments":{"fields":["files","id"]}}'
curl --out torrents.json http://192.168.2.2:9091/transmission/rpc -H 'X-Transmission-Session-Id: i0vmh6RL9WiQ59Hm9ZWU4eROQanovfkCUu7IQLE2iO1f4N1A' --data-raw "$data"