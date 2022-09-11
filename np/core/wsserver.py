import asyncio
from np import log
import websockets
from websockets import WebSocketServerProtocol


class Server:
	clients = set()
	
	async def register(self, ws: WebSocketServerProtocol) -> None:
		self.clients.add(ws)
		np.log(f'{ws.remote_address} connects.', 'info')

	async def unregister(self, ws: WebSocketServerProtocol) -> None:
		self.clients.remove(ws)
		np.log(f'{ws.remote_address} disconnects.', 'info')

	async def send_to_clients(self, message: str) -> None:
		if self.clients:
			await asyncio.wait([client.send(message) for client in self.clients])

	async def ws_handler(self, ws: WebSocketServerProtocol) -> None:
		await self.register(ws)
		np.log('Web socket registered', 'info')
		try:
			await self.distribute(ws)
		finally:
			await self.unregister(ws)
			np.log('Web socket unregistered!', 'info')
			

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
