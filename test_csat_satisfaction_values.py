"""
Test script to verify CSAT satisfaction values are returned in question responses.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

from surveys.models import Survey, Question, QuestionOption
from surveys.serializers import QuestionSerializer
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_csat_satisfaction_values():
    """Test that satisfaction values are returned when CSAT_Calculate is True"""
    
    # Create a test user
    try:
        user = User.objects.filter(role='super_admin').first()
        if not user:
            print("❌ No super admin user found. Please run add_super_admin_user.py first.")
            return
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return
    
    # Create a test survey
    try:
        survey = Survey.objects.create(
            title="Test CSAT Survey",
            description="Testing satisfaction values",
            visibility="PRIVATE",
            creator=user,
            status="draft"
        )
        print(f"✅ Created test survey: {survey.id}")
    except Exception as e:
        print(f"❌ Error creating survey: {e}")
        return
    
    # Test 1: Single choice question with CSAT_Calculate=True
    try:
        question_data = {
            "survey": survey.id,
            "text": "هل يعجبك الاكل الذى سوف يقدم",
            "question_type": "single_choice",
            "options": json.dumps(["نعم", "عادى", "لا"]),
            "is_required": True,
            "order": 1,
            "CSAT_Calculate": True,
            "set_satisfaction_values": [2, 1, 0]  # Satisfied, Neutral, Dissatisfied
        }
        
        # Create question using serializer
        serializer = QuestionSerializer(data=question_data)
        if serializer.is_valid():
            question = serializer.save()
            
            print(f"✅ Created single_choice question: {question.id}")
            
            # Serialize the question to check output
            output_serializer = QuestionSerializer(question)
            output_data = output_serializer.data
            
            print("\n📊 Question Output:")
            print(f"  ID: {output_data['id']}")
            print(f"  Text: {output_data['text']}")
            print(f"  Type: {output_data['question_type']}")
            print(f"  Options: {output_data['options']}")
            print(f"  CSAT_Calculate: {output_data['CSAT_Calculate']}")
            print(f"  options_satisfaction_values: {output_data.get('options_satisfaction_values')}")
            
            # Verify satisfaction values are present
            if 'options_satisfaction_values' in output_data:
                if output_data['options_satisfaction_values'] == [2, 1, 0]:
                    print("✅ SUCCESS: options_satisfaction_values returned correctly!")
                else:
                    print(f"❌ FAILED: Expected [2, 1, 0], got {output_data['options_satisfaction_values']}")
            else:
                print("❌ FAILED: options_satisfaction_values not in output")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
    except Exception as e:
        print(f"❌ Error in test 1: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Yes/No question with CSAT_Calculate=True
    try:
        question_data = {
            "survey": survey.id,
            "text": "هل أنت راض عن الخدمة؟",
            "question_type": "yes_no",
            "options": json.dumps(["نعم", "لا"]),
            "is_required": True,
            "order": 2,
            "CSAT_Calculate": True,
            "set_satisfaction_values": [2, 0]  # Yes=Satisfied, No=Dissatisfied
        }
        
        serializer = QuestionSerializer(data=question_data)
        if serializer.is_valid():
            question = serializer.save()
            
            print(f"\n✅ Created yes_no question: {question.id}")
            
            # Serialize the question
            output_serializer = QuestionSerializer(question)
            output_data = output_serializer.data
            
            print("\n📊 Question Output:")
            print(f"  ID: {output_data['id']}")
            print(f"  Text: {output_data['text']}")
            print(f"  Type: {output_data['question_type']}")
            print(f"  Options: {output_data['options']}")
            print(f"  CSAT_Calculate: {output_data['CSAT_Calculate']}")
            print(f"  options_satisfaction_values: {output_data.get('options_satisfaction_values')}")
            
            # Verify satisfaction values
            if 'options_satisfaction_values' in output_data:
                if output_data['options_satisfaction_values'] == [2, 0]:
                    print("✅ SUCCESS: options_satisfaction_values returned correctly for yes/no!")
                else:
                    print(f"❌ FAILED: Expected [2, 0], got {output_data['options_satisfaction_values']}")
            else:
                print("❌ FAILED: options_satisfaction_values not in output")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
    except Exception as e:
        print(f"❌ Error in test 2: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Question without CSAT_Calculate should return None
    try:
        question_data = {
            "survey": survey.id,
            "text": "What is your name?",
            "question_type": "text",
            "is_required": False,
            "order": 3,
            "CSAT_Calculate": False
        }
        
        serializer = QuestionSerializer(data=question_data)
        if serializer.is_valid():
            question = serializer.save()
            
            print(f"\n✅ Created text question: {question.id}")
            
            # Serialize the question
            output_serializer = QuestionSerializer(question)
            output_data = output_serializer.data
            
            # Verify satisfaction values are None
            if output_data.get('options_satisfaction_values') is None:
                print("✅ SUCCESS: options_satisfaction_values is None for non-CSAT questions!")
            else:
                print(f"❌ FAILED: Expected None, got {output_data['options_satisfaction_values']}")
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
    except Exception as e:
        print(f"❌ Error in test 3: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        survey.delete()
        print("\n✅ Cleaned up test data")
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
    
    print("\n" + "="*60)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_csat_satisfaction_values()
