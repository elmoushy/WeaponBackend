"""
Quick test to verify newsletters system is working.
Tests basic CRUD without authentication (checks endpoints exist).
"""

import requests

BASE_URL = "http://127.0.0.1:8000/api"

print("=" * 60)
print("Newsletter System Quick Test")
print("=" * 60)

# Test 1: Check if endpoints are accessible
print("\n1. Testing endpoint availability...")

endpoints = [
    "/newsletters/normal/",
    "/newsletters/slider/",
    "/newsletters/achievement/",
]

for endpoint in endpoints:
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url)
    
    # Should return 401 (unauthorized) or 403 (forbidden) - meaning endpoint exists
    if response.status_code in [401, 403]:
        print(f"✓ {endpoint} - Endpoint exists (requires auth)")
    elif response.status_code == 404:
        print(f"✗ {endpoint} - Endpoint not found (404)")
    else:
        print(f"? {endpoint} - Unexpected status: {response.status_code}")

# Test 2: Check API root
print("\n2. Testing API root...")
response = requests.get(f"{BASE_URL}/")

if response.status_code == 200:
    data = response.json()
    if 'newsletters' in data.get('endpoints', {}):
        print(f"✓ Newsletters endpoint listed in API root")
        print(f"  URL: {data['endpoints']['newsletters']}")
    else:
        print(f"✗ Newsletters endpoint not in API root")
else:
    print(f"✗ API root failed: {response.status_code}")

# Test 3: Check URL patterns
print("\n3. URL Pattern Summary:")
print("  Normal News:      GET/POST /api/newsletters/normal/")
print("  Slider News:      GET/POST /api/newsletters/slider/")
print("  Achievements:     GET/POST /api/newsletters/achievement/")
print("  Image Upload:     POST /api/newsletters/{type}/{id}/images/upload/")
print("  Image Download:   GET /api/newsletters/images/{id}/download/")
print("  Image Thumbnail:  GET /api/newsletters/images/{id}/thumbnail/")

print("\n" + "=" * 60)
print("Quick Test Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Use authenticated user credentials to test full CRUD")
print("2. Test image upload with multipart/form-data")
print("3. Test pagination with ?page_size=N parameter")
