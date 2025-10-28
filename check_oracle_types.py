"""
Check Oracle column types and data to debug hash lookup issues.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from django.db import connection

def check_table_structure():
    """Check the actual Oracle table structure."""
    print("=" * 80)
    print("CHECKING ORACLE TABLE STRUCTURE")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # Get column information
        print("\n1. Column definitions for auth_user table:")
        cursor.execute("""
            SELECT column_name, data_type, data_length, nullable
            FROM user_tab_columns
            WHERE table_name = 'AUTH_USER'
            ORDER BY column_id
        """)
        
        for row in cursor.fetchall():
            col_name, data_type, data_length, nullable = row
            print(f"   {col_name:20s} {data_type:15s} Length: {data_length:5d} Null: {nullable}")
        
        # Check actual data
        print("\n2. Actual data for user with ID=1:")
        cursor.execute("""
            SELECT 
                id,
                email,
                DUMP(email) as email_dump,
                email_hash,
                DUMP(email_hash) as hash_dump,
                LENGTH(email_hash) as hash_length,
                LENGTHB(email_hash) as hash_byte_length
            FROM auth_user
            WHERE id = 1
        """)
        
        row = cursor.fetchone()
        if row:
            user_id, email, email_dump, email_hash, hash_dump, hash_len, hash_byte_len = row
            print(f"\n   ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   Email DUMP: {email_dump}")
            print(f"   Email Hash: {email_hash}")
            print(f"   Hash DUMP: {hash_dump}")
            print(f"   Hash Length: {hash_len}")
            print(f"   Hash Byte Length: {hash_byte_len}")
        
        # Test different comparison methods
        print("\n3. Testing different WHERE clause methods:")
        
        test_hash = "9433b98ab7bf9474e29a1cc1b5e49a71faacc8da11ca5dbc88ccfe813cd9fbb0"
        
        # Method 1: Direct comparison
        print(f"\n   Method 1: Direct comparison (email_hash = :hash)")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE email_hash = :hash", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Method 2: TO_CHAR on both sides
        print(f"\n   Method 2: TO_CHAR(email_hash) = TO_CHAR(:hash)")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE TO_CHAR(email_hash) = TO_CHAR(:hash)", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Method 3: TO_CHAR on hash only
        print(f"\n   Method 3: TO_CHAR(email_hash) = :hash")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE TO_CHAR(email_hash) = :hash", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Method 4: UPPER comparison
        print(f"\n   Method 4: UPPER(email_hash) = UPPER(:hash)")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE UPPER(email_hash) = UPPER(:hash)", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Method 5: TRIM comparison
        print(f"\n   Method 5: TRIM(email_hash) = TRIM(:hash)")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE TRIM(email_hash) = TRIM(:hash)", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Method 6: RTRIM comparison (Oracle pads CHAR fields)
        print(f"\n   Method 6: RTRIM(email_hash) = :hash")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE RTRIM(email_hash) = :hash", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Method 7: CAST to NVARCHAR2 (THE FIX)
        print(f"\n   Method 7: email_hash = CAST(:hash AS NVARCHAR2(128)) ⭐ THE FIX")
        try:
            cursor.execute("SELECT COUNT(*) FROM auth_user WHERE email_hash = CAST(:hash AS NVARCHAR2(128))", {'hash': test_hash})
            count = cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        # Check if it's a CHAR vs VARCHAR2 issue
        print("\n4. Checking for padding issues:")
        cursor.execute("""
            SELECT 
                email_hash,
                LENGTH(email_hash) as char_len,
                LENGTHB(email_hash) as byte_len,
                VSIZE(email_hash) as actual_size
            FROM auth_user
            WHERE id = 1
        """)
        row = cursor.fetchone()
        if row:
            hash_val, char_len, byte_len, actual_size = row
            print(f"   Stored hash: '{hash_val}'")
            print(f"   CHAR length: {char_len}")
            print(f"   BYTE length: {byte_len}")
            print(f"   Actual size (VSIZE): {actual_size}")
            print(f"   Expected length: {len(test_hash)}")
            
            if char_len != len(test_hash):
                print(f"\n   ⚠️  LENGTH MISMATCH! Field might be CHAR instead of VARCHAR2!")
                print(f"   This causes padding with spaces.")

if __name__ == "__main__":
    check_table_structure()
