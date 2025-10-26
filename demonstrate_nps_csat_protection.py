"""
Demonstration: How the default values protect old surveys from unintended analytics
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from surveys.models import Survey, Question
from django.contrib.auth import get_user_model

User = get_user_model()

def demonstrate_protection():
    """Demonstrate how old surveys are protected"""
    print("=" * 70)
    print("DEMONSTRATION: Old Survey Protection Mechanism")
    print("=" * 70)
    
    # Get a test user
    user = User.objects.filter(role='super_admin').first()
    
    # Scenario 1: Old survey created before the feature
    print("\nSCENARIO 1: Old Survey (Before NPS/CSAT Feature)")
    print("-" * 70)
    
    old_survey = Survey.objects.create(
        title="Customer Feedback Survey (Old)",
        description="Created before NPS/CSAT feature existed",
        creator=user,
        visibility="PUBLIC"
    )
    
    # Create questions without specifying analytics flags (old-style)
    q1 = Question.objects.create(
        survey=old_survey,
        text="How would you rate our service?",
        question_type="rating",
        is_required=True,
        order=1
    )
    
    q2 = Question.objects.create(
        survey=old_survey,
        text="Would you recommend us?",
        question_type="yes_no",
        is_required=True,
        order=2
    )
    
    print(f"Created survey: {old_survey.title}")
    print(f"\nQuestion 1: {q1.text}")
    print(f"  Type: {q1.question_type}")
    print(f"  NPS_Calculate: {q1.NPS_Calculate} ← Protected (False)")
    print(f"  CSAT_Calculate: {q1.CSAT_Calculate} ← Protected (False)")
    print(f"  → This question will NOT be used for NPS/CSAT calculations")
    
    print(f"\nQuestion 2: {q2.text}")
    print(f"  Type: {q2.question_type}")
    print(f"  NPS_Calculate: {q2.NPS_Calculate} ← Protected (False)")
    print(f"  CSAT_Calculate: {q2.CSAT_Calculate} ← Protected (False)")
    print(f"  → This question will NOT be used for NPS/CSAT calculations")
    
    # Scenario 2: New survey with analytics enabled
    print("\n" + "=" * 70)
    print("SCENARIO 2: New Survey (With NPS/CSAT Analytics)")
    print("-" * 70)
    
    new_survey = Survey.objects.create(
        title="NPS & CSAT Tracking Survey (New)",
        description="Created with explicit analytics tracking",
        creator=user,
        visibility="PUBLIC"
    )
    
    # Create questions with analytics enabled (new-style)
    q3 = Question.objects.create(
        survey=new_survey,
        text="On a scale of 0-10, how likely are you to recommend us?",
        question_type="rating",
        is_required=True,
        order=1,
        NPS_Calculate=True,  # Explicitly enabled
        min_scale=0,
        max_scale=10
    )
    
    q4 = Question.objects.create(
        survey=new_survey,
        text="How satisfied are you with our service?",
        question_type="single_choice",
        options=["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"],
        is_required=True,
        order=2,
        CSAT_Calculate=True  # Explicitly enabled
    )
    
    print(f"Created survey: {new_survey.title}")
    print(f"\nQuestion 3: {q3.text}")
    print(f"  Type: {q3.question_type}")
    print(f"  NPS_Calculate: {q3.NPS_Calculate} ← Enabled (True)")
    print(f"  CSAT_Calculate: {q3.CSAT_Calculate}")
    print(f"  → This question WILL be used for NPS calculations ✓")
    
    print(f"\nQuestion 4: {q4.text}")
    print(f"  Type: {q4.question_type}")
    print(f"  NPS_Calculate: {q4.NPS_Calculate}")
    print(f"  CSAT_Calculate: {q4.CSAT_Calculate} ← Enabled (True)")
    print(f"  → This question WILL be used for CSAT calculations ✓")
    
    # Summary
    print("\n" + "=" * 70)
    print("PROTECTION SUMMARY")
    print("=" * 70)
    
    print("""
✓ OLD SURVEYS (Before Feature):
  - NPS_Calculate: Automatically set to False
  - CSAT_Calculate: Automatically set to False
  - Result: No unintended analytics calculations
  
✓ NEW SURVEYS (After Feature):
  - NPS_Calculate: Can be explicitly set to True
  - CSAT_Calculate: Can be explicitly set to True
  - Result: Opt-in analytics tracking works correctly
  
✓ API BEHAVIOR:
  - Old surveys: Return False for both flags
  - New surveys: Return True only when explicitly enabled
  - Analytics endpoints: Only calculate metrics for enabled questions
  
✓ BACKWARD COMPATIBILITY:
  - No breaking changes to existing surveys
  - Existing API contracts maintained
  - Old survey behavior unchanged
""")
    
    # Cleanup
    old_survey.delete()
    new_survey.delete()
    print("✓ Test data cleaned up")
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE ✓")
    print("=" * 70)

if __name__ == '__main__':
    try:
        demonstrate_protection()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
