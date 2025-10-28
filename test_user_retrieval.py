"""
Test different ways to retrieve the user to isolate the ORM issue.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from django.db import connection, transaction
from authentication.models import User
import hashlib

def test_user_retrieval():
    """Test different ways to retrieve the user."""
    print("=" * 80)
    print("TESTING USER RETRIEVAL METHODS")
    print("=" * 80)
    
    email = "seif778811@gmail.com"
    expected_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    
    print(f"\nEmail: {email}")
    print(f"Expected hash: {expected_hash}")
    
    # Method 1: Direct ORM get by ID
    print(f"\n1. Testing User.objects.get(pk=1):")
    try:
        user = User.objects.get(pk=1)
        print(f"   ✅ Success: {user.email}")
    except User.DoesNotExist:
        print(f"   ❌ DoesNotExist error")
    except Exception as e:
        print(f"   ❌ Other error: {e}")
    
    # Method 2: Direct ORM get by ID (explicit transaction)
    print(f"\n2. Testing with explicit transaction:")
    try:
        with transaction.atomic():
            user = User.objects.get(pk=1)
            print(f"   ✅ Success: {user.email}")
    except User.DoesNotExist:
        print(f"   ❌ DoesNotExist error")
    except Exception as e:
        print(f"   ❌ Other error: {e}")
    
    # Method 3: Filter instead of get
    print(f"\n3. Testing User.objects.filter(pk=1).first():")
    try:
        user = User.objects.filter(pk=1).first()
        if user:
            print(f"   ✅ Success: {user.email}")
        else:
            print(f"   ❌ No user returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 4: Using raw SQL to get user data
    print(f"\n4. Testing raw SQL to fetch user data:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email, username FROM auth_user WHERE id = 1")
            row = cursor.fetchone()
            if row:
                user_id, db_email, username = row
                print(f"   ✅ Raw SQL Success: ID={user_id}, Email={db_email}, Username={username}")
            else:
                print(f"   ❌ No row returned from raw SQL")
    except Exception as e:
        print(f"   ❌ Raw SQL error: {e}")
    
    # Method 5: Check if it's a Manager issue
    print(f"\n5. Testing User.objects.all().get(pk=1):")
    try:
        user = User.objects.all().get(pk=1)
        print(f"   ✅ Success: {user.email}")
    except User.DoesNotExist:
        print(f"   ❌ DoesNotExist error")
    except Exception as e:
        print(f"   ❌ Other error: {e}")
    
    # Method 6: Check the actual queryset
    print(f"\n6. Testing queryset debugging:")
    try:
        qs = User.objects.filter(pk=1)
        print(f"   Queryset SQL: {qs.query}")
        print(f"   Queryset count: {qs.count()}")
        print(f"   Queryset exists: {qs.exists()}")
        
        users = list(qs)
        print(f"   Users in queryset: {len(users)}")
        if users:
            print(f"   First user: {users[0].email}")
    except Exception as e:
        print(f"   ❌ Queryset error: {e}")
    
    # Method 7: Check if there's a default manager issue
    print(f"\n7. Testing different manager:")
    try:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        
        # Try the base manager
        user = UserModel._base_manager.get(pk=1)
        print(f"   ✅ Base manager success: {user.email}")
    except User.DoesNotExist:
        print(f"   ❌ Base manager DoesNotExist error")
    except Exception as e:
        print(f"   ❌ Base manager error: {e}")

if __name__ == "__main__":
    test_user_retrieval()