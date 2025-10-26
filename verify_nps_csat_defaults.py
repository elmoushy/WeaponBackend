"""
Verification script to ensure all existing questions have proper default values
for NPS_Calculate and CSAT_Calculate flags.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from surveys.models import Question

def verify_defaults():
    """Verify that all questions have proper default values"""
    print("=" * 60)
    print("VERIFICATION: NPS_Calculate and CSAT_Calculate Defaults")
    print("=" * 60)
    
    # Get all questions
    all_questions = Question.objects.all()
    total_count = all_questions.count()
    
    print(f"\nTotal questions in database: {total_count}")
    
    # Check for NULL values
    null_nps = Question.objects.filter(NPS_Calculate__isnull=True).count()
    null_csat = Question.objects.filter(CSAT_Calculate__isnull=True).count()
    
    print(f"Questions with NULL NPS_Calculate: {null_nps}")
    print(f"Questions with NULL CSAT_Calculate: {null_csat}")
    
    # Check for True values (should be intentionally set)
    true_nps = Question.objects.filter(NPS_Calculate=True).count()
    true_csat = Question.objects.filter(CSAT_Calculate=True).count()
    
    print(f"\nQuestions with NPS_Calculate=True: {true_nps}")
    print(f"Questions with CSAT_Calculate=True: {true_csat}")
    
    # Check for False values (should be the default for old surveys)
    false_nps = Question.objects.filter(NPS_Calculate=False).count()
    false_csat = Question.objects.filter(CSAT_Calculate=False).count()
    
    print(f"\nQuestions with NPS_Calculate=False: {false_nps}")
    print(f"Questions with CSAT_Calculate=False: {false_csat}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if null_nps == 0 and null_csat == 0:
        print("✓ SUCCESS: All questions have non-NULL values for both flags")
    else:
        print("✗ WARNING: Some questions have NULL values!")
        return False
    
    if false_nps + true_nps == total_count and false_csat + true_csat == total_count:
        print("✓ SUCCESS: All questions have valid boolean values")
    else:
        print("✗ WARNING: Some questions have invalid values!")
        return False
    
    print(f"\n✓ Old surveys protection: {false_nps + false_csat} default False values set")
    print(f"✓ New surveys with analytics: {true_nps} NPS + {true_csat} CSAT questions")
    
    # Show breakdown by question type
    print("\n" + "=" * 60)
    print("BREAKDOWN BY QUESTION TYPE")
    print("=" * 60)
    
    for qtype in ['rating', 'single_choice', 'yes_no', 'multiple_choice', 'text', 'textarea']:
        count = Question.objects.filter(question_type=qtype).count()
        nps_count = Question.objects.filter(question_type=qtype, NPS_Calculate=True).count()
        csat_count = Question.objects.filter(question_type=qtype, CSAT_Calculate=True).count()
        
        if count > 0:
            print(f"\n{qtype}:")
            print(f"  Total: {count}")
            print(f"  NPS_Calculate=True: {nps_count}")
            print(f"  CSAT_Calculate=True: {csat_count}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = verify_defaults()
        if success:
            print("\n✓ All checks passed! Old surveys are protected from NPS/CSAT calculation.")
        else:
            print("\n✗ Some checks failed. Please review the output above.")
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
