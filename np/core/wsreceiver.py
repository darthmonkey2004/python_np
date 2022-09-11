import subprocess
import threading
import asyncio
import logging
import websockets
import np

class receiver(threading.Thread):
	def __init__(self, hostname=None, port=None):
		if hostname == None:
			self.hostname == get_localip()
		else:
			self.hostname = hostname
		if port == None:
			self.port = 4000
		else:
			self.port = port
		threading.Thread.__init__(self)
		self.message = None

	async def consumer_handler(self, websocket: websockets.WebSocketClientProtocol) -> None:
		async for message in websocket:
			self.message = message
			self.log_message(self.message)

	async def consume(self, hostname: str, port: int) -> None:
		websocket_resource_url = f"ws://{hostname}:{port}"
		async with websockets.connect(websocket_resource_url) as websocket:
			await self.consumer_handler(websocket)

	def log_message(self, message: str) -> None:
		self.message = message
		np.log(f"Message: {self.message}", 'info')
		with open(np.WSLOGFILE, 'w') as f:
			f.write(self.message)
			f.close()
		return self.message

	def get_localip(self):
		com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}'"
		return subprocess.check_output(com, shell=True).decode().strip()

	def run(self):
		loop = asyncio.new_event_loop()
		loop.run_until_complete(self.consume(hostname=self.hostname, port=self.port))
		loop.run_forever()

if __name__ == "__main__":
	import sys
	try:
		host = sys.argv[1]
	except:
		host = '192.168.2.2'
	try:
		port = sys.argv[2]
	except:
		port = 4000

	receiver = receiver(host, port)
	receiver.start()
