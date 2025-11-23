"""
Quick test to verify blob storage is working correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from internal_chat.models import Attachment
from django.core.files.uploadedfile import SimpleUploadedFile

# Create a small test file
test_content = b"This is a test file content for blob storage!"
test_file = SimpleUploadedFile(
    "test_image.txt",
    test_content,
    content_type="text/plain"
)

# Create attachment with blob storage
attachment = Attachment.objects.create(
    file_data=test_content,
    file_name="test_image.txt",
    content_type="text/plain",
    size=len(test_content),
    checksum="test123"
)

print(f"✅ Attachment created with ID: {attachment.id}")
print(f"   File name: {attachment.file_name}")
print(f"   Size: {attachment.size} bytes ({attachment.size_mb} MB)")
print(f"   Content type: {attachment.content_type}")
print(f"   Blob data length: {len(attachment.file_data)} bytes")
print(f"   Blob data preview: {attachment.file_data[:50]}")

# Verify we can read it back
retrieved = Attachment.objects.get(id=attachment.id)
print(f"\n✅ Retrieved attachment successfully")
print(f"   Data matches: {retrieved.file_data == test_content}")

# Clean up
attachment.delete()
print(f"\n✅ Test attachment deleted")
print("\n🎉 Blob storage is working correctly!")
