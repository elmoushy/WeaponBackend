"""
Test that options_satisfaction_values works when sent as JSON strings.
This matches the real API request format.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from surveys.serializers import SurveySerializer
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_json_string_satisfaction_values():
    """Test creating survey with satisfaction values as JSON strings"""
    
    # Get test user
    user = User.objects.filter(role='super_admin').first()
    if not user:
        print("❌ No super admin user found")
        return
    
    print("="*60)
    print("Testing Survey Creation with JSON String Satisfaction Values")
    print("="*60)
    
    # This mimics the actual API request payload
    survey_data = {
        "title": "تأكيد الحضور اختبار 1",
        "description": "نرجو منك تأكيد حضورك للفعالية القادمة",
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
                "options_satisfaction_values": "[2,1]"  # JSON STRING, not array!
            },
            {
                "text": "هل يعجبك الاكل الذى سوف يقدم",
                "question_type": "single_choice",
                "options": "[\"نعم\",\"عادى\",\"لا\"]",  # JSON string
                "is_required": True,
                "order": 2,
                "NPS_Calculate": False,
                "CSAT_Calculate": True,
                "min_scale": 0,
                "max_scale": 5,
                "options_satisfaction_values": "[2,1,0]"  # JSON STRING!
            },
            {
                "text": "هل لديك أي متطلبات خاصة أو ملاحظات تود مشاركتها؟",
                "question_type": "rating",
                "is_required": True,
                "order": 3,
                "NPS_Calculate": True,
                "CSAT_Calculate": True,
                "min_scale": 0,
                "max_scale": 5
            }
        ],
        "per_device_access": False
    }
    
    # Create mock request context
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    try:
        print("\n📤 Sending survey data with JSON string satisfaction values...")
        serializer = SurveySerializer(data=survey_data, context={'request': MockRequest(user)})
        
        if serializer.is_valid():
            survey = serializer.save()
            print(f"✅ Survey created successfully: {survey.id}")
            print(f"   Title: {survey.title}")
            print(f"   Questions: {survey.questions.count()}")
            
            # Verify the questions
            print("\n📋 Verifying Questions:")
            from surveys.models import Question
            from surveys.serializers import QuestionSerializer
            
            questions = Question.objects.filter(survey=survey).order_by('order')
            
            for idx, question in enumerate(questions, 1):
                q_serializer = QuestionSerializer(question)
                q_data = q_serializer.data
                
                print(f"\n  Question {idx}: {q_data['text'][:50]}...")
                print(f"    Type: {q_data['question_type']}")
                print(f"    CSAT_Calculate: {q_data['CSAT_Calculate']}")
                
                sat_values = q_data.get('options_satisfaction_values')
                if sat_values is not None:
                    print(f"    ✅ Satisfaction Values: {sat_values}")
                else:
                    if q_data['CSAT_Calculate'] and q_data['question_type'] in ['single_choice', 'yes_no']:
                        print(f"    ❌ Missing satisfaction values!")
                    else:
                        print(f"    ⚪ No satisfaction values (not applicable)")
            
            # Cleanup
            survey.delete()
            print("\n✅ Test completed successfully!")
            
        else:
            print(f"❌ Validation errors:")
            print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_string_satisfaction_values()
