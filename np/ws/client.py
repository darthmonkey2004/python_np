from np import readConf, log
import asyncio
import websockets
conf = readConf()

async def sender(message, host, port):
	async with websockets.connect(f'ws://{host}:{port}/') as ws:
		await ws.send(message)
		response = await ws.recv()
		return response

def send_msg(message=None, host=None, port=None):
	if host == None or port == None:
		if host is None:
			host = conf['remote']['server']['address']
		if port is None:
			port = conf['remote']['server']['port']
	if message is None:
		log(f"Exception in client.py, send_msg: No message data provided!", 'error')
	loop = asyncio.get_event_loop()
	response = loop.run_until_complete(sender(message=message, host=host, port=port))
	return response

if __name__ == "__main__":
	import sys
	message = None
	try:
		message = sys.argv[1]
	except:
		log(f"Exception in client.py, send_msg: No message data provided!", 'error')
	loop = asyncio.get_event_loop()
	response = loop.run_until_complete(sender(message=message, host='127.0.0.1', port=8000))
