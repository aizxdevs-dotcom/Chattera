import asyncio
import websockets

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello backend!")
        reply = await websocket.recv()
        print("Backend replied:", reply)

asyncio.run(test_ws())
