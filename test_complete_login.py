"""
Test the actual login flow to see where it's failing.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from authentication.models import User
from django.db import connection
import hashlib

def test_login_flow():
    """Test the complete login flow."""
    print("=" * 80)
    print("TESTING COMPLETE LOGIN FLOW")
    print("=" * 80)
    
    email = "seif778811@gmail.com"
    
    print(f"\n1. Testing User.objects.get_by_email('{email}'):")
    try:
        user = User.objects.get_by_email(email)
        if user:
            print(f"   ✅ Success: Found user ID {user.id}, Email: {user.email}")
            print(f"      Username: {user.username}")
            print(f"      Auth type: {user.auth_type}")
            print(f"      Role: {user.role}")
            print(f"      Active: {user.is_active}")
        else:
            print(f"   ❌ Returned None")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n2. Testing direct filter by ID:")
    try:
        user = User.objects.filter(pk=1).first()
        if user:
            print(f"   ✅ Success: {user.email}")
        else:
            print(f"   ❌ Returned None")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n3. Testing raw SQL + filter approach (what get_by_email does):")
    try:
        expected_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
        safe_hash = expected_hash.replace("'", "''")
        
        with connection.cursor() as cursor:
            sql = f"SELECT id FROM auth_user WHERE email_hash = N'{safe_hash}' AND ROWNUM = 1"
            print(f"   SQL: {sql}")
            cursor.execute(sql)
            row = cursor.fetchone()
            print(f"   Row result: {row}")
            
            if row:
                user_id = row[0]
                print(f"   Found user_id: {user_id} (type: {type(user_id)})")
                
                # Try the filter approach
                print(f"   Calling User.objects.filter(pk={user_id}).first()...")
                user = User.objects.filter(pk=user_id).first()
                
                if user:
                    print(f"   ✅ Filter success: {user.email}")
                else:
                    print(f"   ❌ Filter returned None")
                    
                    # Debug why filter returns None
                    print(f"\n   Debugging filter issue:")
                    qs = User.objects.filter(pk=user_id)
                    print(f"   QuerySet: {qs}")
                    print(f"   QuerySet SQL: {qs.query}")
                    print(f"   QuerySet count: {qs.count()}")
                    print(f"   QuerySet exists: {qs.exists()}")
                    
                    # Try all()
                    all_users = User.objects.all()
                    print(f"\n   All users count: {all_users.count()}")
                    for u in all_users:
                        print(f"      ID: {u.id}, Email: {u.email}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n4. Testing if it's a Manager issue:")
    try:
        # Bypass our custom manager
        from django.db.models import Manager
        default_manager = Manager()
        default_manager.model = User
        
        # This won't work but let's see the error
        print(f"   Trying default Manager...")
        user = User.objects.using('default').filter(pk=1).first()
        if user:
            print(f"   ✅ Success with using('default'): {user.email}")
        else:
            print(f"   ❌ Still returned None")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n5. Testing authentication (password check):")
    try:
        from django.contrib.auth import authenticate
        
        # First get the user to see the username
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, email, password FROM auth_user WHERE id = 1")
            row = cursor.fetchone()
            if row:
                user_id, username, db_email, password_hash = row
                print(f"   User data from DB:")
                print(f"      ID: {user_id}")
                print(f"      Username: {username}")
                print(f"      Email: {db_email}")
                print(f"      Password hash exists: {bool(password_hash)}")
                
                # Try authenticating with username
                test_password = input(f"\n   Enter password for {email} to test authentication: ")
                auth_user = authenticate(username=username, password=test_password)
                
                if auth_user:
                    print(f"   ✅ Authentication success: {auth_user.email}")
                else:
                    print(f"   ❌ Authentication failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_flow()
