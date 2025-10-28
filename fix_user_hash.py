"""
Fix user hash fields in Oracle database.
Run this to regenerate email_hash and username_hash for users.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from authentication.models import User
from django.db import connection

def fix_user_hash(email=None, user_id=None, fix_all=False):
    """Fix hash fields for user(s)."""
    
    if fix_all:
        print("=" * 80)
        print("FIXING ALL USERS")
        print("=" * 80)
        
        users = User.objects.all()
        total = users.count()
        print(f"\nFound {total} users to fix")
        
        fixed = 0
        for user in users:
            try:
                # Save will regenerate hashes
                user.save()
                print(f"✅ Fixed: {user.email}")
                fixed += 1
            except Exception as e:
                print(f"❌ Error fixing {user.email}: {e}")
        
        print(f"\n✅ Fixed {fixed}/{total} users")
        
    elif email:
        print("=" * 80)
        print(f"FIXING USER: {email}")
        print("=" * 80)
        
        # First try direct query to find the user
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM auth_user WHERE LOWER(email) = LOWER(:email)",
                {'email': email}
            )
            row = cursor.fetchone()
            
            if not row:
                print(f"❌ User not found with email: {email}")
                return
            
            user_id = row[0]
        
        # Get user by ID
        try:
            user = User.objects.get(id=user_id)
            print(f"\nFound user: {user.email}")
            print(f"Current email_hash: {user.email_hash}")
            print(f"Current username_hash: {user.username_hash}")
            
            # Save to regenerate hashes
            user.save()
            
            # Reload to verify
            user.refresh_from_db()
            print(f"\nAfter save:")
            print(f"New email_hash: {user.email_hash}")
            print(f"New username_hash: {user.username_hash}")
            
            print(f"\n✅ Successfully fixed user: {user.email}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
    elif user_id:
        print("=" * 80)
        print(f"FIXING USER ID: {user_id}")
        print("=" * 80)
        
        try:
            user = User.objects.get(id=user_id)
            print(f"\nFound user: {user.email}")
            print(f"Current email_hash: {user.email_hash}")
            print(f"Current username_hash: {user.username_hash}")
            
            # Save to regenerate hashes
            user.save()
            
            # Reload to verify
            user.refresh_from_db()
            print(f"\nAfter save:")
            print(f"New email_hash: {user.email_hash}")
            print(f"New username_hash: {user.username_hash}")
            
            print(f"\n✅ Successfully fixed user: {user.email}")
            
        except User.DoesNotExist:
            print(f"❌ User not found with ID: {user_id}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix user hash fields in Oracle')
    parser.add_argument('--email', help='Email of user to fix')
    parser.add_argument('--user-id', type=int, help='ID of user to fix')
    parser.add_argument('--all', action='store_true', help='Fix all users')
    
    args = parser.parse_args()
    
    if args.all:
        confirm = input("⚠️  Fix ALL users? This may take a while. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            fix_user_hash(fix_all=True)
        else:
            print("Cancelled")
    elif args.email:
        fix_user_hash(email=args.email)
    elif args.user_id:
        fix_user_hash(user_id=args.user_id)
    else:
        # Default to the problematic user
        email = "seif778811@gmail.com"
        print(f"No arguments provided, fixing default user: {email}")
        fix_user_hash(email=email)
