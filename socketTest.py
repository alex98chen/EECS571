import asyncio
import websockets
import socket

async def hello(websocket, path):
    name = await websocket.recv()
    print("-" + name)
    
    greeting = "Hello " + name

    await websocket.send(greeting)
    print("- " + greeting)

print("localhost")
start_server = websockets.serve(hello, "164.227.31.53", 4321)

hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)
print("Computer: " + hostname)
print("IP: " + IP)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
