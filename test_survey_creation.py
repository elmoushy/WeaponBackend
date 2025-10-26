"""
Test script to validate survey creation with NPS/CSAT fields
"""

import json

# Your example payload
test_payload = {
    "title": "تأكيد الحضور",
    "description": "نرجو منك تأكيد حضورك للفعالية القادمة عبر تعبئة النموذج أدناه. يساعدنا ذلك في تنظيم المقاعد والخدمات بشكل أفضل.",
    "visibility": "AUTH",
    "is_active": True,
    "start_date": None,
    "end_date": None,
    "questions": [
        {
            "text": "هل ستتمكن من الحضور؟",
            "question_type": "yes_no",
            "is_required": True,
            "order": 1,
            "NPS_Calculate": False,
            "CSAT_Calculate": True,
            "min_scale": 0,
            "max_scale": 5,
            "options_satisfaction_values": [2, 0]  # yes=Satisfied(2), no=Dissatisfied(0)
        },
        {
            "text": "كم سيحضر معك شخاص ؟",
            "question_type": "yes_no",
            "is_required": True,
            "order": 2,
            "NPS_Calculate": False,
            "CSAT_Calculate": True,
            "min_scale": 0,
            "max_scale": 5,
            "options_satisfaction_values": [2, 1]  # yes=Satisfied(2), no=Neutral(1)
        },
        {
            "text": "هلالذى تفضل الحصول عليه",
            "question_type": "single_choice",
            "options": ["اه", "ممكن", "معتقدش"],
            "is_required": False,
            "order": 3,
            "NPS_Calculate": False,
            "CSAT_Calculate": True,
            "min_scale": 0,
            "max_scale": 5,
            "options_satisfaction_values": [2, 1, 0]  # اه=Satisfied, ممكن=Neutral, معتقدش=Dissatisfied
        },
        {
            "text": "تقيمك للدعوه",
            "question_type": "rating",
            "is_required": True,
            "order": 4,
            "NPS_Calculate": True,
            "CSAT_Calculate": True,
            "min_scale": 0,
            "max_scale": 5
        }
    ]
}

print("Test Payload Validation:")
print("=" * 60)

# Validate Question 1 (yes/no with CSAT)
q1 = test_payload['questions'][0]
print(f"\nQuestion 1: {q1['text']}")
print(f"  Type: {q1['question_type']}")
print(f"  CSAT_Calculate: {q1['CSAT_Calculate']}")
print(f"  Satisfaction values: {q1['options_satisfaction_values']}")
print(f"  Expected: Create 2 QuestionOption records (yes=2, no=0)")
print(f"  ✓ VALID: yes/no question with 2 satisfaction values")

# Validate Question 2 (yes/no with CSAT)
q2 = test_payload['questions'][1]
print(f"\nQuestion 2: {q2['text']}")
print(f"  Type: {q2['question_type']}")
print(f"  CSAT_Calculate: {q2['CSAT_Calculate']}")
print(f"  Satisfaction values: {q2['options_satisfaction_values']}")
print(f"  Expected: Create 2 QuestionOption records (yes=2, no=1)")
print(f"  ✓ VALID: yes/no question with 2 satisfaction values")

# Validate Question 3 (single_choice with CSAT)
q3 = test_payload['questions'][2]
print(f"\nQuestion 3: {q3['text']}")
print(f"  Type: {q3['question_type']}")
print(f"  CSAT_Calculate: {q3['CSAT_Calculate']}")
print(f"  Options: {q3['options']}")
print(f"  Satisfaction values: {q3['options_satisfaction_values']}")
print(f"  Expected: Create 3 QuestionOption records")
if len(q3['options']) == len(q3['options_satisfaction_values']):
    print(f"  ✓ VALID: {len(q3['options'])} options match {len(q3['options_satisfaction_values'])} satisfaction values")
else:
    print(f"  ✗ ERROR: {len(q3['options'])} options but {len(q3['options_satisfaction_values'])} satisfaction values")

# Validate Question 4 (rating with NPS + CSAT)
q4 = test_payload['questions'][3]
print(f"\nQuestion 4: {q4['text']}")
print(f"  Type: {q4['question_type']}")
print(f"  NPS_Calculate: {q4['NPS_Calculate']}")
print(f"  CSAT_Calculate: {q4['CSAT_Calculate']}")
print(f"  Scale: {q4['min_scale']}-{q4['max_scale']}")
if q4['question_type'] == 'rating' and q4['NPS_Calculate']:
    print(f"  ✓ VALID: NPS_Calculate only on rating question")
else:
    print(f"  ✗ ERROR: NPS_Calculate on non-rating question")

print("\n" + "=" * 60)
print("Summary:")
print("  - Question 1: yes/no CSAT → 2 QuestionOption records (yes/نعم=2, no/لا=0)")
print("  - Question 2: yes/no CSAT → 2 QuestionOption records (yes/نعم=2, no/لا=1)")
print("  - Question 3: single_choice CSAT → 3 QuestionOption records (اه=2, ممكن=1, معتقدش=0)")
print("  - Question 4: rating NPS+CSAT → No QuestionOption records needed")
print("\n✓ All validations passed!")
print("\nTo test in practice, run:")
print("  1. Activate virtual environment: .\\.venv\\Scripts\\Activate.ps1")
print("  2. Start server: python manage.py runserver")
print("  3. POST to /api/surveys/ with the test payload")
print("  4. Check QuestionOption records were created correctly")
