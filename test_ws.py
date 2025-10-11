import asyncio, websockets, json

async def test_ws():
    # Replace with real IDs when testing manually
    conversation_id = input("Conversation ID: ")
    sender_id = input("Sender ID: ")

    uri = f"ws://127.0.0.1:8000/ws/conversations/{conversation_id}"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "sender_id": sender_id,
            "content": "Hello backend!"
        }))
        reply = await websocket.recv()
        print("Backend replied:", reply)

asyncio.run(test_ws())