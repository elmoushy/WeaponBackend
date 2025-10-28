"""
Test different parameter binding approaches for Oracle NVARCHAR2.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from django.db import connection
import oracledb

def test_parameter_binding():
    """Test different ways to bind NVARCHAR2 parameters."""
    print("=" * 80)
    print("TESTING ORACLE PARAMETER BINDING FOR NVARCHAR2")
    print("=" * 80)
    
    test_hash = "9433b98ab7bf9474e29a1cc1b5e49a71faacc8da11ca5dbc88ccfe813cd9fbb0"
    
    with connection.cursor() as cursor:
        # Get the underlying Oracle cursor
        oracle_cursor = cursor.cursor
        
        print("\n1. Testing with explicit oracledb.STRING type:")
        try:
            # Create a bind variable with explicit type
            oracle_cursor.setinputsizes(hash=oracledb.STRING)
            oracle_cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE email_hash = :hash",
                {'hash': test_hash}
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        print("\n2. Testing with NCHAR type:")
        try:
            oracle_cursor.setinputsizes(hash=oracledb.NCHAR)
            oracle_cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE email_hash = :hash",
                {'hash': test_hash}
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        print("\n3. Testing with explicit NVARCHAR2 using TO_NCHAR:")
        try:
            oracle_cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE email_hash = TO_NCHAR(:hash)",
                {'hash': test_hash}
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        print("\n4. Testing with UNISTR function:")
        try:
            oracle_cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE email_hash = UNISTR(:hash)",
                {'hash': test_hash}
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        print("\n5. Testing with N prefix (N'...'):")
        try:
            # Build SQL with N prefix directly (not bind variable)
            oracle_cursor.execute(
                f"SELECT COUNT(*) FROM auth_user WHERE email_hash = N'{test_hash}'"
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        print("\n6. Testing comparison direction (parameter first):")
        try:
            oracle_cursor.setinputsizes(hash=oracledb.STRING)
            oracle_cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE :hash = email_hash",
                {'hash': test_hash}
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")
        
        print("\n7. Testing with LIKE operator:")
        try:
            oracle_cursor.setinputsizes(hash=oracledb.STRING)
            oracle_cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE email_hash LIKE :hash",
                {'hash': test_hash}
            )
            count = oracle_cursor.fetchone()[0]
            print(f"   Result: {count} rows found {'✅ SUCCESS!' if count > 0 else '❌'}")
        except Exception as e:
            print(f"   Result: ❌ Error - {e}")

if __name__ == "__main__":
    test_parameter_binding()
