"""
Quick test to verify database default values work correctly for NPS/CSAT flags.
This simulates creating an old-style question without specifying the flags.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from surveys.models import Survey, Question
from django.contrib.auth import get_user_model

User = get_user_model()

def test_default_values():
    """Test that new questions get default False values automatically"""
    print("=" * 60)
    print("TEST: Default Values for Old-Style Question Creation")
    print("=" * 60)
    
    # Get or create a test user
    user = User.objects.filter(role='super_admin').first()
    if not user:
        print("✗ No super admin user found. Creating test user...")
        user = User.objects.create_user(
            username="test_defaults@example.com",
            email="test_defaults@example.com",
            password="test123",
            role="super_admin"
        )
    
    # Create a test survey
    survey = Survey.objects.create(
        title="Test Survey - Default Values Check",
        description="Testing default NPS/CSAT flags",
        creator=user,
        visibility="PRIVATE"
    )
    
    print(f"\n✓ Created test survey: {survey.title}")
    
    # Create a question WITHOUT specifying NPS_Calculate or CSAT_Calculate
    # This simulates old survey creation before the feature existed
    question = Question.objects.create(
        survey=survey,
        text="How satisfied are you?",
        question_type="single_choice",
        options=["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"],
        is_required=True,
        order=1
    )
    
    print(f"\n✓ Created question: {question.text}")
    print(f"  Question type: {question.question_type}")
    
    # Check the default values
    print("\nChecking default values:")
    print(f"  NPS_Calculate: {question.NPS_Calculate} (expected: False)")
    print(f"  CSAT_Calculate: {question.CSAT_Calculate} (expected: False)")
    
    # Verify the values
    assert question.NPS_Calculate == False, "NPS_Calculate should be False by default"
    assert question.CSAT_Calculate == False, "CSAT_Calculate should be False by default"
    
    print("\n✓ SUCCESS: Default values are correctly set to False")
    
    # Clean up
    survey.delete()
    print("\n✓ Cleaned up test data")
    
    print("\n" + "=" * 60)
    print("TEST PASSED ✓")
    print("=" * 60)
    print("\nConclusion: Old surveys created before this feature will have")
    print("NPS_Calculate and CSAT_Calculate set to False, preventing")
    print("unintended analytics calculations.")

if __name__ == '__main__':
    try:
        test_default_values()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
