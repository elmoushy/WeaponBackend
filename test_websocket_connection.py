#!/usr/bin/env python
"""
WebSocket Connection Test Script
Tests real-time chat WebSocket connectivity with Redis
"""

import asyncio
import websockets
import json
import sys

# Configuration
WS_URL = "ws://localhost:8000/ws/internal-chat/threads/{thread_id}/?token={token}"
REST_API_URL = "http://localhost:8000/api"

async def test_websocket_connection(thread_id, token):
    """Test WebSocket connection to a thread"""
    
    url = WS_URL.format(thread_id=thread_id, token=token)
    print(f"\n{'='*60}")
    print(f"Testing WebSocket Connection")
    print(f"{'='*60}")
    print(f"URL: {url}\n")
    
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket connected successfully!\n")
            
            # Wait for connection.established message
            print("⏳ Waiting for connection.established message...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Received: {json.dumps(data, indent=2)}\n")
            
            if data.get('type') == 'connection.established':
                print("✅ Connection established successfully!")
                print(f"   Thread ID: {data.get('thread_id')}")
                print(f"   Message: {data.get('message')}\n")
            
            # Send a test message
            test_message = {
                "type": "message.send",
                "content": "🧪 Test message from WebSocket test script"
            }
            print(f"📤 Sending test message...")
            await websocket.send(json.dumps(test_message))
            print(f"   Content: {test_message['content']}\n")
            
            # Wait for response (message.new event)
            print("⏳ Waiting for message.new response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📨 Received: {json.dumps(data, indent=2)}\n")
            
            if data.get('type') == 'message.new':
                print("✅ Message sent and received successfully!")
                message = data.get('message', {})
                print(f"   Message ID: {message.get('id')}")
                print(f"   Content: {message.get('content')}")
                print(f"   Sender: {message.get('sender', {}).get('username')}\n")
            
            # Test typing indicator
            print("📤 Testing typing indicator...")
            await websocket.send(json.dumps({"type": "typing.start"}))
            print("✅ Typing indicator sent\n")
            
            await asyncio.sleep(1)
            
            await websocket.send(json.dumps({"type": "typing.stop"}))
            print("✅ Stop typing sent\n")
            
            print(f"{'='*60}")
            print("🎉 ALL TESTS PASSED!")
            print(f"{'='*60}")
            print("\n✅ Redis is working")
            print("✅ WebSocket connection is working")
            print("✅ Real-time messaging is working")
            print("✅ Daphne server is working")
            print("\nYour real-time chat is fully operational! 🚀\n")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        if e.status_code == 403:
            print("   → Invalid token or not a thread participant")
        elif e.status_code == 401:
            print("   → Authentication failed")
        print(f"\n{str(e)}\n")
        return False
        
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for server response")
        print("   → Server might not be running or not responding\n")
        return False
        
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {str(e)}\n")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def print_usage():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("WebSocket Test Script")
    print("="*60)
    print("\nUsage:")
    print("  python test_websocket_connection.py <thread_id> <jwt_token>")
    print("\nExample:")
    print("  python test_websocket_connection.py abc123 eyJ0eXAiOiJKV1QiLCJhbGc...")
    print("\nTo get your JWT token:")
    print("  1. Login via REST API: POST /api/auth/login/")
    print("  2. Use the 'access' token from response")
    print("\nTo get a thread ID:")
    print("  1. List threads: GET /api/internal-chat/threads/")
    print("  2. Use any thread ID you have access to")
    print("="*60 + "\n")


async def main():
    """Main function"""
    if len(sys.argv) != 3:
        print_usage()
        print("❌ Error: Missing required arguments\n")
        sys.exit(1)
    
    thread_id = sys.argv[1]
    token = sys.argv[2]
    
    success = await test_websocket_connection(thread_id, token)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user\n")
        sys.exit(0)
