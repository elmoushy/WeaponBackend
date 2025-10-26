"""
Debug script to check QuestionOption records creation.
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
from surveys.serializers import SurveySerializer, QuestionSerializer
from django.contrib.auth import get_user_model
import json
import hashlib

User = get_user_model()

def debug_question_options():
    """Debug QuestionOption creation"""
    
    # Get test user
    user = User.objects.filter(role='super_admin').first()
    if not user:
        print("❌ No super admin user found")
        return
    
    # Create a simple survey with one CSAT question
    survey = Survey.objects.create(
        title="Debug CSAT Test",
        description="Testing QuestionOption creation",
        visibility="PUBLIC",
        creator=user,
        status="draft"
    )
    
    # Create a question with satisfaction values
    question_data = {
        "survey": survey.id,
        "text": "How satisfied are you?",
        "question_type": "single_choice",
        "options": json.dumps(["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied"]),
        "is_required": True,
        "order": 1,
        "CSAT_Calculate": True,
        "set_satisfaction_values": [2, 2, 1, 0]
    }
    
    serializer = QuestionSerializer(data=question_data)
    if serializer.is_valid():
        question = serializer.save()
        print(f"✅ Created question: {question.id}")
        
        # Check QuestionOption records
        options = QuestionOption.objects.filter(question=question)
        print(f"\n📊 QuestionOption Records: {options.count()}")
        
        for opt in options:
            print(f"  - Text: {opt.option_text}")
            print(f"    Hash: {opt.option_text_hash}")
            print(f"    Satisfaction Value: {opt.satisfaction_value}")
            print(f"    Order: {opt.order}")
        
        # Test hash calculation
        print(f"\n🔍 Testing hash calculation:")
        options_list = json.loads(question.options)
        for idx, option_text in enumerate(options_list):
            calculated_hash = hashlib.sha256(str(option_text).encode('utf-8')).hexdigest()
            print(f"  Option: {option_text}")
            print(f"    Calculated hash: {calculated_hash}")
            
            # Find matching QuestionOption
            matching = QuestionOption.objects.filter(
                question=question,
                option_text_hash=calculated_hash
            ).first()
            
            if matching:
                print(f"    ✅ Found match! Satisfaction value: {matching.satisfaction_value}")
            else:
                print(f"    ❌ No match found")
        
        # Test serializer output
        print(f"\n📤 Serializer Output:")
        output_serializer = QuestionSerializer(question)
        output_data = output_serializer.data
        print(f"  options_satisfaction_values: {output_data.get('options_satisfaction_values')}")
        
    else:
        print(f"❌ Validation errors: {serializer.errors}")
    
    # Cleanup
    survey.delete()
    print(f"\n✅ Cleaned up")

if __name__ == "__main__":
    debug_question_options()
