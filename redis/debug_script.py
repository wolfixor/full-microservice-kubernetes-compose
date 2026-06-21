"""Debug script to test Redis caching setup."""

import asyncio
import json
from redis.asyncio import Redis


async def test_redis_connection(service_name: str, host: str):
    """Test Redis connection for a specific service."""
    print(f"\n=== Testing {service_name} Redis Connection ===")
    
    try:
        # Test connection
        redis = Redis(host=host, port=6379, db=0, decode_responses=True)
        
        # Test ping
        ping_result = await redis.ping()
        print(f"✓ Ping successful: {ping_result}")
        
        # Test set/get
        test_key = f"test:{service_name}"
        test_value = {"service": service_name, "test": "works"}
        
        await redis.setex(test_key, 60, json.dumps(test_value))
        print(f"✓ Set test key: {test_key}")
        
        retrieved = await redis.get(test_key)
        if retrieved:
            print(f"✓ Get test key: {json.loads(retrieved)}")
        else:
            print("✗ Failed to get test key")
        
        # List all keys
        all_keys = await redis.keys("*")
        print(f"✓ All keys in Redis: {all_keys}")
        
        await redis.close()
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


async def main():
    """Test all three service Redis connections."""
    services = [
        ("comment-service", "comment-service-redis"),
        ("task-service", "task-service-redis"),
        ("user-service", "user-service-redis")
    ]
    
    print("Testing Redis connections for all microservices...")
    print("=" * 50)
    
    results = {}
    for service_name, host in services:
        success = await test_redis_connection(service_name, host)
        results[service_name] = success
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    for service_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{service_name}: {status}")
    
    # Test recommendations
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("1. Rebuild services: docker-compose build --no-cache")
    print("2. Test individual endpoints, not collections:")
    print("   curl http://localhost:8001/api/comments/{id}")
    print("   curl http://localhost:8002/api/tasks/{id}")
    print("   curl http://localhost:8003/api/users/{id}")
    print("3. Collections (GET /api/comments/) are NOT cached!")


if __name__ == "__main__":
    asyncio.run(main())