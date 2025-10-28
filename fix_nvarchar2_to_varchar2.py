"""
CRITICAL FIX: Convert NVARCHAR2 columns to VARCHAR2 to fix ORA-01722 errors.

Django's Oracle backend with oracledb driver cannot handle NVARCHAR2 columns properly.
This migration converts all NVARCHAR2 columns to VARCHAR2.

Run this on production:
    python fix_nvarchar2_to_varchar2.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from django.db import connection

def fix_nvarchar2_columns():
    """Convert all NVARCHAR2 columns to VARCHAR2."""
    print("=" * 80)
    print("FIXING NVARCHAR2 TO VARCHAR2 CONVERSION")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # Get all NVARCHAR2 columns in auth_user table
        print("\n1. Finding NVARCHAR2 columns in AUTH_USER table...")
        cursor.execute("""
            SELECT column_name, data_type, data_length
            FROM user_tab_columns
            WHERE table_name = 'AUTH_USER'
            AND data_type = 'NVARCHAR2'
            ORDER BY column_id
        """)
        
        nvarchar2_columns = cursor.fetchall()
        
        if not nvarchar2_columns:
            print("   ✅ No NVARCHAR2 columns found - already fixed!")
            return
        
        print(f"   Found {len(nvarchar2_columns)} NVARCHAR2 columns to convert:")
        for col_name, data_type, data_length in nvarchar2_columns:
            print(f"      {col_name}: {data_type}({data_length})")
        
        # Convert each column using the rename method
        print("\n2. Converting columns to VARCHAR2...")
        for col_name, data_type, data_length in nvarchar2_columns:
            # VARCHAR2 length is in bytes, NVARCHAR2 is in characters
            varchar2_length = data_length
            
            temp_col_name = f"{col_name}_NEW"
            
            try:
                print(f"   Converting {col_name}...", end=" ")
                
                # Step 1: Add new VARCHAR2 column
                cursor.execute(f"ALTER TABLE AUTH_USER ADD {temp_col_name} VARCHAR2({varchar2_length})")
                
                # Step 2: Copy data from NVARCHAR2 to VARCHAR2
                cursor.execute(f"UPDATE AUTH_USER SET {temp_col_name} = {col_name}")
                
                # Step 3: Drop old NVARCHAR2 column
                cursor.execute(f"ALTER TABLE AUTH_USER DROP COLUMN {col_name}")
                
                # Step 4: Rename new column to original name
                cursor.execute(f"ALTER TABLE AUTH_USER RENAME COLUMN {temp_col_name} TO {col_name}")
                
                print("✅")
            except Exception as e:
                print(f"❌ Error: {e}")
                # Try to clean up if something failed
                try:
                    cursor.execute(f"ALTER TABLE AUTH_USER DROP COLUMN {temp_col_name}")
                except:
                    pass
        
        # Commit the changes
        print("\n3. Committing changes...")
        connection.commit()
        
        # Verify the conversion
        print("\n4. Verifying conversion...")
        cursor.execute("""
            SELECT column_name, data_type, data_length
            FROM user_tab_columns
            WHERE table_name = 'AUTH_USER'
            AND column_name IN ('USERNAME', 'EMAIL', 'EMAIL_HASH', 'USERNAME_HASH', 
                                'PASSWORD', 'AUTH_TYPE', 'ROLE', 'FIRST_NAME', 'LAST_NAME')
            ORDER BY column_id
        """)
        
        print("\n   Current column types:")
        for col_name, data_type, data_length in cursor.fetchall():
            status = "✅" if data_type == 'VARCHAR2' else "❌"
            print(f"      {status} {col_name}: {data_type}({data_length})")
        
        print("\n" + "=" * 80)
        print("CONVERSION COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Restart Gunicorn: sudo systemctl restart weaponbackend")
        print("2. Test login: curl -X POST https://apps.lightidea.org:9006/api/auth/login/ ...")

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will modify your database schema!")
    print("⚠️  Make sure you have a backup before proceeding.")
    
    confirm = input("\nType 'yes' to proceed with NVARCHAR2 to VARCHAR2 conversion: ")
    
    if confirm.lower() == 'yes':
        fix_nvarchar2_columns()
    else:
        print("\nCancelled. No changes made.")
