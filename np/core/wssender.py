import asyncio
import websockets
import sys

async def sender(message: str, host: str, port: int) -> None:
	async with websockets.connect(f"ws://{host}:{port}") as ws:
		await ws.send(message)
		response = await ws.recv()
		print(response)


def send(host, port, message=None):
	loop = asyncio.get_event_loop()
	loop.run_until_complete(sender(message=message, host=host, port=port))


if __name__ == "__main__":
	try:
		message = sys.argv[1]
	except:
		message = 'Defaulted Hullaballoo!'
	try:
		host = sys.argv[2]
	except:
		host = '192.168.2.2'
	try:
		port = sys.argv[3]
	except:
		port = 4444
	send(host, port)
