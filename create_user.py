"""
Script to create a user in the production Oracle database.
Run on production server with: python create_user.py
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from authentication.models import User

def create_user():
    """Create the seif778811@gmail.com user in Oracle database."""
    email = "seif778811@gmail.com"
    password = input(f"Enter password for {email}: ")
    
    # Check if user already exists
    if User.objects.filter_by_email(email).exists():
        print(f"❌ User with email {email} already exists!")
        existing_user = User.objects.get_by_email(email)
        print(f"   Username: {existing_user.username}")
        print(f"   Role: {existing_user.role}")
        print(f"   Auth Type: {existing_user.auth_type}")
        return
    
    # Get role
    print("\nAvailable roles:")
    print("1. user (default)")
    print("2. admin")
    print("3. super_admin")
    role_choice = input("Select role (1-3, default=1): ").strip() or "1"
    
    role_map = {
        "1": "user",
        "2": "admin", 
        "3": "super_admin"
    }
    role = role_map.get(role_choice, "user")
    
    # Create user
    try:
        user = User.objects.create_user(
            username=email,  # Use email as username for regular users
            email=email,
            password=password,
            auth_type='regular',
            role=role,
            is_active=True
        )
        
        # Set additional fields if super admin
        if role == 'super_admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        print(f"\n✅ Successfully created user:")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Role: {user.role}")
        print(f"   Auth Type: {user.auth_type}")
        print(f"   Active: {user.is_active}")
        
        if role == 'super_admin':
            print(f"   Staff: {user.is_staff}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"\n   Can access Django Admin at: https://apps.lightidea.org:9006/admin/")
        
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Create User in Oracle Database")
    print("=" * 60)
    print(f"Database: Oracle (USE_ORACLE=True)")
    print()
    
    create_user()
