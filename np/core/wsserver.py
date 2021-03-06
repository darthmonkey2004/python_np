import asyncio
import logging
import websockets
from websockets import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)

class Server:
	clients = set()
	
	async def register(self, ws: WebSocketServerProtocol) -> None:
		self.clients.add(ws)
		logging.info(f'{ws.remote_address} connects.')

	async def unregister(self, ws: WebSocketServerProtocol) -> None:
		self.clients.remove(ws)
		logging.info(f'{ws.remote_address} disconnects.')

	async def send_to_clients(self, message: str) -> None:
		if self.clients:
			await asyncio.wait([client.send(message) for client in self.clients])

	async def ws_handler(self, ws: WebSocketServerProtocol) -> None:
		await self.register(ws)
		logging.info('Web socket registered')
		try:
			await self.distribute(ws)
		finally:
			await self.unregister(ws)
			logging.info('Web socket unregistered!')
			

	async def distribute(self, ws: WebSocketServerProtocol) -> None:
		async for message in ws:
			await self.send_to_clients(message)

def bark(port=4444):
	server = Server()
	start_server = websockets.serve(server.ws_handler, port=4444)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(start_server)
	loop.run_forever()

if __name__ == "__main__":
	server = Server()
	start_server = websockets.serve(server.ws_handler, port=4444)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(start_server)
	loop.run_forever()
