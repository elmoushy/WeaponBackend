"""
Debug the Oracle N prefix query to see what's actually happening.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from django.db import connection
import hashlib

def debug_oracle_query():
    """Debug the exact SQL query with N prefix."""
    print("=" * 80)
    print("DEBUGGING ORACLE N PREFIX QUERY")
    print("=" * 80)
    
    email = "seif778811@gmail.com"
    expected_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    
    print(f"\nEmail: {email}")
    print(f"Expected hash: {expected_hash}")
    
    with connection.cursor() as cursor:
        # Test the exact query we're using in managers.py
        safe_hash = expected_hash.replace("'", "''")
        sql = f"SELECT id FROM auth_user WHERE email_hash = N'{safe_hash}' AND ROWNUM = 1"
        
        print(f"\nSQL Query: {sql}")
        
        cursor.execute(sql)
        row = cursor.fetchone()
        
        print(f"Query result: {row}")
        
        if row:
            user_id = row[0]
            print(f"Found user ID: {user_id}")
            print(f"Type of user ID: {type(user_id)}")
            
            # Test if we can get the user
            from authentication.models import User
            try:
                user = User.objects.get(pk=user_id)
                print(f"✅ Successfully retrieved user: {user.email}")
            except User.DoesNotExist:
                print(f"❌ User with ID {user_id} does not exist!")
                
                # Check what users actually exist
                print("\nExisting users:")
                for u in User.objects.all():
                    print(f"  ID: {u.id}, Email: {u.email}")
            except Exception as e:
                print(f"❌ Error retrieving user: {e}")
        else:
            print("❌ No row returned from SQL query")
            
            # Test without ROWNUM
            print("\nTesting without ROWNUM:")
            sql2 = f"SELECT id FROM auth_user WHERE email_hash = N'{safe_hash}'"
            cursor.execute(sql2)
            rows = cursor.fetchall()
            print(f"Rows without ROWNUM: {rows}")
            
            # Test what's actually in the hash field
            print("\nChecking actual email_hash values:")
            cursor.execute("SELECT id, email, email_hash FROM auth_user")
            for row in cursor.fetchall():
                user_id, db_email, db_hash = row
                print(f"  ID: {user_id}, Email: {db_email}")
                print(f"      Hash: {db_hash}")
                print(f"      Hash == Expected: {db_hash == expected_hash}")

if __name__ == "__main__":
    debug_oracle_query()