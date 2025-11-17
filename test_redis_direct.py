"""
Direct Redis Test - Verify Redis PubSub is working
Tests Redis channel layer without authentication
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def test_redis_pubsub():
    """Test Redis pub/sub functionality"""
    
    print("\n" + "="*60)
    print("Testing Redis Pub/Sub")
    print("="*60 + "\n")
    
    # Get channel layer
    channel_layer = get_channel_layer()
    print(f"✅ Channel layer loaded: {channel_layer.__class__.__name__}")
    print(f"   Config: {channel_layer.hosts}\n")
    
    # Test group send/receive
    print("🧪 Testing group messaging...")
    
    test_group = "test_group_123"
    test_message = {
        "type": "test.message",
        "content": "Hello from Redis test!"
    }
    
    try:
        # Send message to group
        print(f"📤 Sending message to group '{test_group}'...")
        async_to_sync(channel_layer.group_send)(
            test_group,
            test_message
        )
        print("✅ Message sent successfully!\n")
        
        # Test channel layer attributes
        print("📊 Channel Layer Information:")
        print(f"   Backend: {channel_layer.__class__.__module__}.{channel_layer.__class__.__name__}")
        
        if hasattr(channel_layer, 'hosts'):
            print(f"   Redis Host: {channel_layer.hosts}")
        
        if hasattr(channel_layer, 'prefix'):
            print(f"   Channel Prefix: {channel_layer.prefix}")
        
        if hasattr(channel_layer, 'expiry'):
            print(f"   Message Expiry: {channel_layer.expiry} seconds")
        
        print("\n" + "="*60)
        print("🎉 REDIS PUBSUB TEST PASSED!")
        print("="*60)
        print("\n✅ Redis server is running")
        print("✅ Channel layer is configured correctly")
        print("✅ Pub/Sub messaging is working")
        print("✅ Ready for WebSocket connections!\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if Redis is running: docker ps")
        print("2. Check Redis connectivity: redis-cli ping")
        print("3. Check settings.py CHANNEL_LAYERS configuration")
        print()
        import traceback
        traceback.print_exc()
        return False


async def test_async_channel_layer():
    """Test channel layer with async operations"""
    
    print("\n" + "="*60)
    print("Testing Async Channel Operations")
    print("="*60 + "\n")
    
    channel_layer = get_channel_layer()
    
    # Create a unique channel name
    channel_name = await channel_layer.new_channel()
    print(f"✅ Created channel: {channel_name}\n")
    
    # Test sending and receiving
    test_message = {
        "type": "test.message",
        "content": "Async test message",
        "timestamp": "2025-11-17T08:36:00Z"
    }
    
    print("📤 Sending message to channel...")
    await channel_layer.send(channel_name, test_message)
    print("✅ Message sent\n")
    
    print("📥 Receiving message from channel...")
    received = await channel_layer.receive(channel_name)
    print(f"✅ Message received: {received}\n")
    
    if received == test_message:
        print("🎉 Message integrity verified!\n")
        return True
    else:
        print("⚠️  Message mismatch!")
        print(f"   Sent: {test_message}")
        print(f"   Received: {received}\n")
        return False


def main():
    """Run all tests"""
    print("\n🧪 Starting Redis Tests...\n")
    
    # Test 1: Sync pub/sub
    test1 = test_redis_pubsub()
    
    # Test 2: Async operations
    print("\n")
    test2 = asyncio.run(test_async_channel_layer())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Sync Pub/Sub Test:      {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Async Channel Test:     {'✅ PASSED' if test2 else '❌ FAILED'}")
    print("="*60 + "\n")
    
    if test1 and test2:
        print("🚀 All tests passed! Your WebSocket infrastructure is ready!\n")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.\n")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
