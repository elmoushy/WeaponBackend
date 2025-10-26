"""
Integration test to verify CSAT satisfaction values work with full survey creation workflow.
Tests the entire flow from survey creation to question retrieval.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from surveys.models import Survey, Question
from surveys.serializers import SurveySerializer
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_survey_with_csat_questions():
    """Test creating a complete survey with CSAT questions"""
    
    # Get test user
    try:
        user = User.objects.filter(role='super_admin').first()
        if not user:
            print("❌ No super admin user found. Please run add_super_admin_user.py first.")
            return
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return
    
    print("="*60)
    print("Testing Full Survey Creation with CSAT Questions")
    print("="*60)
    
    # Create survey data with questions
    survey_data = {
        "title": "رضا العملاء - Customer Satisfaction Survey",
        "description": "استطلاع لقياس رضا العملاء عن الخدمات المقدمة",
        "visibility": "PUBLIC",
        "status": "draft",
        "questions": [
            {
                "text": "كيف تقيم جودة الطعام؟",
                "question_type": "single_choice",
                "options": json.dumps(["ممتاز", "جيد", "عادي", "سيء"]),
                "is_required": True,
                "order": 1,
                "CSAT_Calculate": True,
                "options_satisfaction_values": [2, 2, 1, 0]  # Excellent & Good=Satisfied, Average=Neutral, Poor=Dissatisfied
            },
            {
                "text": "هل توصي بخدماتنا لأصدقائك؟",
                "question_type": "yes_no",
                "options": json.dumps(["نعم", "لا"]),
                "is_required": True,
                "order": 2,
                "CSAT_Calculate": True,
                "options_satisfaction_values": [2, 0]  # Yes=Satisfied, No=Dissatisfied
            },
            {
                "text": "ما هو رأيك في سرعة الخدمة؟",
                "question_type": "single_choice",
                "options": json.dumps(["سريع جداً", "سريع", "بطيء", "بطيء جداً"]),
                "is_required": True,
                "order": 3,
                "CSAT_Calculate": True,
                "options_satisfaction_values": [2, 2, 0, 0]
            },
            {
                "text": "ملاحظات إضافية",
                "question_type": "textarea",
                "is_required": False,
                "order": 4,
                "CSAT_Calculate": False
            }
        ]
    }
    
    # Create survey using serializer
    try:
        serializer = SurveySerializer(data=survey_data, context={'request': type('obj', (object,), {'user': user})()})
        if serializer.is_valid():
            survey = serializer.save(creator=user)
            print(f"\n✅ Created survey: {survey.id}")
            print(f"   Title: {survey.title}")
            print(f"   Questions: {survey.questions.count()}")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            return
    except Exception as e:
        print(f"❌ Error creating survey: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Retrieve the survey and check questions
    try:
        output_serializer = SurveySerializer(survey)
        output_data = output_serializer.data
        
        print("\n" + "="*60)
        print("Verifying Question Output")
        print("="*60)
        
        questions_data = output_data.get('questions', [])
        
        for i, q_data in enumerate(questions_data, 1):
            print(f"\n📋 Question {i}:")
            print(f"   Text: {q_data['text']}")
            print(f"   Type: {q_data['question_type']}")
            print(f"   CSAT_Calculate: {q_data['CSAT_Calculate']}")
            
            if q_data['options']:
                print(f"   Options: {q_data['options']}")
            
            sat_values = q_data.get('options_satisfaction_values')
            if sat_values is not None:
                print(f"   ✅ Satisfaction Values: {sat_values}")
                
                # Verify the values match expected
                if i == 1:
                    expected = [2, 2, 1, 0]
                    if sat_values == expected:
                        print(f"      ✅ Correct! (Expected {expected})")
                    else:
                        print(f"      ❌ Wrong! Expected {expected}, got {sat_values}")
                elif i == 2:
                    expected = [2, 0]
                    if sat_values == expected:
                        print(f"      ✅ Correct! (Expected {expected})")
                    else:
                        print(f"      ❌ Wrong! Expected {expected}, got {sat_values}")
                elif i == 3:
                    expected = [2, 2, 0, 0]
                    if sat_values == expected:
                        print(f"      ✅ Correct! (Expected {expected})")
                    else:
                        print(f"      ❌ Wrong! Expected {expected}, got {sat_values}")
            else:
                if q_data['CSAT_Calculate']:
                    print(f"   ❌ Missing satisfaction values (CSAT_Calculate is True)")
                else:
                    print(f"   ✅ No satisfaction values (CSAT_Calculate is False)")
        
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        
        csat_questions = [q for q in questions_data if q['CSAT_Calculate']]
        csat_with_values = [q for q in csat_questions if q.get('options_satisfaction_values')]
        
        print(f"Total Questions: {len(questions_data)}")
        print(f"CSAT Questions: {len(csat_questions)}")
        print(f"CSAT with Satisfaction Values: {len(csat_with_values)}")
        
        if len(csat_questions) == len(csat_with_values):
            print("\n✅ SUCCESS! All CSAT questions have satisfaction values!")
        else:
            print(f"\n❌ FAILED! {len(csat_questions) - len(csat_with_values)} CSAT questions missing satisfaction values")
        
    except Exception as e:
        print(f"❌ Error verifying output: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        survey.delete()
        print("\n✅ Cleaned up test data")
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
    
    print("\n" + "="*60)
    print("✅ Integration test completed!")
    print("="*60)

if __name__ == "__main__":
    test_survey_with_csat_questions()
