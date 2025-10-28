"""
Diagnostic script to check user data in Oracle database.
Run on production server to diagnose authentication issues.
"""
import os
import django
import hashlib

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from authentication.models import User
from django.db import connection

def diagnose_user(email):
    """Diagnose user authentication issues."""
    print("=" * 80)
    print(f"DIAGNOSING USER: {email}")
    print("=" * 80)
    
    # Calculate expected hash
    expected_email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    print(f"\n1. Expected email_hash: {expected_email_hash}")
    
    # Check if user exists with direct SQL
    print("\n2. Direct SQL Query (bypassing ORM):")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, email, email_hash, username_hash, auth_type, role, is_active FROM auth_user WHERE LOWER(email) = LOWER(:email)",
            {'email': email}
        )
        rows = cursor.fetchall()
        
        if rows:
            print(f"   Found {len(rows)} user(s) with direct email match:")
            for row in rows:
                user_id, username, db_email, db_email_hash, db_username_hash, auth_type, role, is_active = row
                print(f"\n   User ID: {user_id}")
                print(f"   Username: {username}")
                print(f"   Email: {db_email}")
                print(f"   Email Hash (DB): {db_email_hash}")
                print(f"   Expected Hash:   {expected_email_hash}")
                print(f"   Hash Match: {db_email_hash == expected_email_hash}")
                print(f"   Username Hash: {db_username_hash}")
                print(f"   Auth Type: {auth_type}")
                print(f"   Role: {role}")
                print(f"   Active: {is_active}")
                
                # Check if hash is NULL or empty
                if not db_email_hash:
                    print(f"   ⚠️  WARNING: email_hash is NULL/empty!")
                if not db_username_hash:
                    print(f"   ⚠️  WARNING: username_hash is NULL/empty!")
        else:
            print(f"   ❌ No user found with email: {email}")
    
    # Try hash-based lookup
    print("\n3. Hash-based SQL Query (using TO_CHAR):")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, username, email, email_hash, TO_CHAR(email_hash) as email_hash_str
            FROM auth_user 
            WHERE TO_CHAR(email_hash) = TO_CHAR(:email_hash)
            AND ROWNUM = 1
            """,
            {'email_hash': expected_email_hash}
        )
        row = cursor.fetchone()
        
        if row:
            print(f"   ✅ Found user via hash lookup!")
            print(f"   User ID: {row[0]}")
            print(f"   Username: {row[1]}")
            print(f"   Email: {row[2]}")
            print(f"   Email Hash (raw): {row[3]}")
            print(f"   Email Hash (TO_CHAR): {row[4]}")
        else:
            print(f"   ❌ No user found with hash: {expected_email_hash}")
    
    # Try ORM lookup
    print("\n4. ORM Hash Lookup (User.objects.get_by_email):")
    try:
        user = User.objects.get_by_email(email)
        if user:
            print(f"   ✅ Found user via ORM!")
            print(f"   User ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Email Hash: {user.email_hash}")
            print(f"   Auth Type: {user.auth_type}")
            print(f"   Role: {user.role}")
            print(f"   Active: {user.is_active}")
        else:
            print(f"   ❌ ORM returned None")
    except Exception as e:
        print(f"   ❌ ORM Error: {type(e).__name__}: {e}")
    
    # Check all users for comparison
    print("\n5. All Users in Database (first 10):")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, email, email_hash, auth_type FROM auth_user WHERE ROWNUM <= 10"
        )
        rows = cursor.fetchall()
        print(f"   Total users shown: {len(rows)}")
        for row in rows:
            user_id, db_email, db_email_hash, auth_type = row
            hash_status = "✅" if db_email_hash else "❌ NULL"
            print(f"   [{user_id}] {db_email} - Hash: {hash_status} - Type: {auth_type}")
            if db_email_hash:
                print(f"       Stored hash: {db_email_hash}")
                # Compare with expected
                if db_email == email:
                    print(f"       Expected:    {expected_email_hash}")
                    print(f"       Match: {'✅ YES' if db_email_hash == expected_email_hash else '❌ NO'}")
    
    # Suggest fix
    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    
    print("\n6. Recommended Actions:")
    
    # Check if hash needs to be regenerated
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, email, email_hash FROM auth_user WHERE LOWER(email) = LOWER(:email)",
            {'email': email}
        )
        row = cursor.fetchone()
        
        if row:
            user_id, db_email, db_hash = row
            
            # Check for encoding/whitespace issues
            print(f"\n   📧 Email analysis:")
            print(f"      Input email: '{email}'")
            print(f"      Input length: {len(email)} chars")
            print(f"      Input bytes: {email.encode('utf-8').hex()}")
            print(f"\n      DB email: '{db_email}'")
            print(f"      DB length: {len(db_email)} chars")
            print(f"      DB bytes: {db_email.encode('utf-8').hex()}")
            print(f"\n      Exact match: {email == db_email}")
            
            if not db_hash or db_hash != expected_email_hash:
                print(f"\n   ⚠️  Hash mismatch or missing!")
                print(f"\n   Expected hash: {expected_email_hash}")
                print(f"   Actual hash:   {db_hash}")
                print(f"\n   🔧 Run this to fix:")
                print(f"\n   python fix_user_hash.py --user-id {user_id}")
                print(f"\n   Or in Django shell:")
                print(f"   from authentication.models import User")
                print(f"   user = User.objects.get(id={user_id})")
                print(f"   user.save()  # This will regenerate hashes")
            else:
                print(f"\n   ✅ Hash is correct - issue may be elsewhere")
        else:
            print(f"\n   ❌ User doesn't exist - create with:")
            print(f"\n   python create_user.py")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "seif778811@gmail.com"  # Default
    
    diagnose_user(email)
