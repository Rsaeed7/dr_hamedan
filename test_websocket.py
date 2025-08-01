#!/usr/bin/env python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/1/"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful")
            
            # Send a test message
            test_message = {
                "message": "Test message from script",
                "sender": "test_user"
            }
            await websocket.send(json.dumps(test_message))
            print("✅ Test message sent")
            
            # Wait for response
            response = await websocket.recv()
            print(f"✅ Received response: {response}")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 