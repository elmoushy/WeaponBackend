"""
Test WebSocket Authentication and Connection
Run this to verify WebSocket setup is working correctly
"""
import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test WebSocket connection with JWT token"""
    
    # Get token from command line or use test token
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("❌ Error: Please provide a JWT token")
        print("Usage: python test_websocket_auth.py <your_jwt_token> [thread_id]")
        print("\nTo get a token:")
        print("1. Login via POST http://localhost:8000/api/auth/login/")
        print("2. Copy the 'access' token from response")
        print("3. Run: python test_websocket_auth.py <token> [thread_id]")
        return
    
    # Get thread ID from command line or use real one
    if len(sys.argv) > 2:
        thread_id = sys.argv[2]
    else:
        thread_id = "3887e7eb-ad18-4f30-acdb-ee1df302eccc"  # Real thread from DB
    
    ws_url = f"ws://localhost:8000/ws/internal-chat/threads/{thread_id}/?token={token}"
    
    print(f"\n🔌 Testing WebSocket connection...")
    print(f"Thread ID: {thread_id}")
    print(f"URL: {ws_url[:80]}...")
    
    try:
        # Add Origin header to bypass AllowedHostsOriginValidator
        async with websockets.connect(
            ws_url,
            additional_headers={"Origin": "http://localhost:5173"}
        ) as websocket:
            print("✅ WebSocket connection established!")
            
            # Wait for connection.established message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ Received: {data}")
            
            if data.get('type') == 'connection.established':
                print("✅ Authentication successful!")
                print(f"✅ Connected to thread: {data.get('thread_id')}")
            else:
                print(f"⚠️  Unexpected response type: {data.get('type')}")
            
            # Send a test ping
            await websocket.send(json.dumps({
                'type': 'typing.start'
            }))
            print("✅ Sent typing.start event")
            
            # Close gracefully
            await websocket.close()
            print("✅ Connection closed gracefully")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection rejected with status code: {e.status_code}")
        if e.status_code == 403:
            print("   → Authentication failed or not authorized for this thread")
        elif e.status_code == 401:
            print("   → Invalid or expired JWT token")
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except ConnectionRefusedError:
        print("❌ Connection refused - Is Daphne server running on port 8000?")
        print("   Run: daphne -b 0.0.0.0 -p 8000 weaponpowercloud_backend.asgi:application")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Authentication Test")
    print("=" * 60)
    asyncio.run(test_websocket_connection())
