"""
Test script for newsletters system.

This script tests:
1. Authentication
2. Newsletter CRUD operations for all three types
3. Image upload and retrieval
4. Pagination
"""

import requests
import json
import os
from io import BytesIO
from PIL import Image

# Base URL
BASE_URL = "http://127.0.0.1:8000/api"

# Test credentials (update with your test user)
TEST_EMAIL = "seif778811@gmail.com"
TEST_PASSWORD = "seif778811"  # Update this with actual password

def create_test_image(width=800, height=600, color='red'):
    """Create a test image in memory"""
    img = Image.new('RGB', (width, height), color=color)
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer

def test_authentication():
    """Test login and get access token"""
    print("\n=== Testing Authentication ===")
    
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('data', {}).get('access')
        print(f"✓ Login successful")
        print(f"  Access token: {token[:50]}...")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_create_newsletter(token, news_type, title, details):
    """Create a newsletter"""
    print(f"\n=== Creating {news_type} Newsletter ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/newsletters/{news_type.lower()}/",
        headers=headers,
        json={
            "news_type": news_type,
            "title": title,
            "details": details
        }
    )
    
    if response.status_code == 201:
        data = response.json()
        newsletter_id = data.get('id')
        print(f"✓ Newsletter created successfully")
        print(f"  ID: {newsletter_id}")
        print(f"  Title: {data.get('title')}")
        return newsletter_id
    else:
        print(f"✗ Failed to create newsletter: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_list_newsletters(token, news_type, page_size=5):
    """List newsletters with pagination"""
    print(f"\n=== Listing {news_type} Newsletters (page_size={page_size}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/newsletters/{news_type.lower()}/?page_size={page_size}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        newsletters_data = data.get('data', {})
        count = newsletters_data.get('count', 0)
        results = newsletters_data.get('results', [])
        
        print(f"✓ Retrieved {len(results)} newsletters (total: {count})")
        print(f"  Page size: {newsletters_data.get('page_size')}")
        print(f"  Total pages: {newsletters_data.get('total_pages')}")
        
        for newsletter in results:
            print(f"  - {newsletter.get('title')} (ID: {newsletter.get('id')})")
        
        return results
    else:
        print(f"✗ Failed to list newsletters: {response.status_code}")
        print(f"  Response: {response.text}")
        return []

def test_upload_image(token, newsletter_id, news_type, is_main=False):
    """Upload image to newsletter"""
    print(f"\n=== Uploading Image to Newsletter {newsletter_id} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test image
    test_image = create_test_image(color='blue' if is_main else 'green')
    
    files = {
        'image': ('test_image.jpg', test_image, 'image/jpeg')
    }
    
    data = {
        'is_main': str(is_main).lower(),
        'display_order': 0 if is_main else 1
    }
    
    response = requests.post(
        f"{BASE_URL}/newsletters/{news_type.lower()}/{newsletter_id}/images/upload/",
        headers=headers,
        files=files,
        data=data
    )
    
    if response.status_code == 201:
        data = response.json().get('data', {})
        image_id = data.get('id')
        print(f"✓ Image uploaded successfully")
        print(f"  Image ID: {image_id}")
        print(f"  Filename: {data.get('original_filename')}")
        print(f"  Is main: {data.get('is_main')}")
        print(f"  Download URL: {data.get('download_url')}")
        print(f"  Thumbnail URL: {data.get('thumbnail_url')}")
        return image_id
    else:
        print(f"✗ Failed to upload image: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_download_image(token, image_id):
    """Download image"""
    print(f"\n=== Downloading Image {image_id} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test full image download
    response = requests.get(
        f"{BASE_URL}/newsletters/images/{image_id}/download/",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✓ Full image downloaded successfully")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Size: {len(response.content) / 1024:.1f} KB")
    else:
        print(f"✗ Failed to download image: {response.status_code}")
    
    # Test thumbnail download
    response = requests.get(
        f"{BASE_URL}/newsletters/images/{image_id}/thumbnail/",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✓ Thumbnail downloaded successfully")
        print(f"  Size: {len(response.content) / 1024:.1f} KB")
    else:
        print(f"✗ Failed to download thumbnail: {response.status_code}")

def test_get_newsletter_detail(token, newsletter_id, news_type):
    """Get newsletter detail with images"""
    print(f"\n=== Getting Newsletter {newsletter_id} Detail ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/newsletters/{news_type.lower()}/{newsletter_id}/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Newsletter retrieved successfully")
        print(f"  Title: {data.get('title')}")
        print(f"  News Type: {data.get('news_type')}")
        print(f"  Author: {data.get('author_name')}")
        print(f"  Images: {len(data.get('images', []))}")
        
        main_image = data.get('main_image')
        if main_image:
            print(f"  Main Image: {main_image.get('original_filename')}")
        
        return data
    else:
        print(f"✗ Failed to get newsletter: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Newsletter System Test Suite")
    print("=" * 60)
    
    # 1. Authenticate
    token = test_authentication()
    if not token:
        print("\n✗ Cannot proceed without authentication")
        return
    
    # 2. Test Normal News
    normal_id = test_create_newsletter(
        token, 
        "NORMAL",
        "Breaking News: System Update",
        "The newsletter system has been successfully deployed with BLOB image storage and encryption."
    )
    
    if normal_id:
        test_upload_image(token, normal_id, "normal", is_main=True)
        test_upload_image(token, normal_id, "normal", is_main=False)
    
    # 3. Test Slider News
    slider_id = test_create_newsletter(
        token,
        "SLIDER",
        "Welcome to the New Portal",
        "Explore our enhanced features and improved user experience."
    )
    
    if slider_id:
        image_id = test_upload_image(token, slider_id, "slider", is_main=True)
        if image_id:
            test_download_image(token, image_id)
    
    # 4. Test Achievement
    achievement_id = test_create_newsletter(
        token,
        "ACHIEVEMENT",
        "Employee of the Month: John Doe",
        "Congratulations to John Doe for outstanding performance this month!"
    )
    
    if achievement_id:
        test_upload_image(token, achievement_id, "achievement", is_main=True)
    
    # 5. Test pagination for each type
    test_list_newsletters(token, "normal", page_size=5)
    test_list_newsletters(token, "slider", page_size=3)
    test_list_newsletters(token, "achievement", page_size=10)
    
    # 6. Test detail retrieval
    if normal_id:
        test_get_newsletter_detail(token, normal_id, "normal")
    
    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
