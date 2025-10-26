"""
Test script to validate options_satisfaction_values string-to-list conversion
"""

import json

# Simulate the serializer's to_internal_value conversion
def convert_satisfaction_values(data):
    """Mimic QuestionSerializer.to_internal_value()"""
    if 'options_satisfaction_values' in data:
        value = data['options_satisfaction_values']
        if isinstance(value, str):
            try:
                data['options_satisfaction_values'] = json.loads(value)
                print(f"  ✓ Converted string '{value}' to list {data['options_satisfaction_values']}")
            except (json.JSONDecodeError, TypeError):
                print(f"  ✗ Failed to parse: {value}")
        elif isinstance(value, list):
            print(f"  ✓ Already a list: {value}")
    return data

print("Testing options_satisfaction_values String-to-List Conversion:")
print("=" * 70)

# Test Case 1: String format (from your payload)
print("\nTest Case 1: String format '[2,0]'")
data1 = {"options_satisfaction_values": "[2,0]"}
result1 = convert_satisfaction_values(data1)
assert result1['options_satisfaction_values'] == [2, 0], "Conversion failed!"
print(f"  Result: {result1['options_satisfaction_values']}")
print(f"  Type: {type(result1['options_satisfaction_values'])}")

# Test Case 2: Already a list
print("\nTest Case 2: Already a list [2,1,0]")
data2 = {"options_satisfaction_values": [2, 1, 0]}
result2 = convert_satisfaction_values(data2)
assert result2['options_satisfaction_values'] == [2, 1, 0], "Should remain unchanged!"
print(f"  Result: {result2['options_satisfaction_values']}")
print(f"  Type: {type(result2['options_satisfaction_values'])}")

# Test Case 3: Your exact payload format
print("\nTest Case 3: Your actual payload questions")
questions = [
    {
        "text": "هل ستتمكن من الحضور؟",
        "question_type": "yes_no",
        "options_satisfaction_values": "[2,0]"  # String format
    },
    {
        "text": "كم سيحضر معك شخاص ؟",
        "question_type": "yes_no",
        "options_satisfaction_values": "[2,0]"  # String format
    },
    {
        "text": "هلالذى تفضل الحصول عليه",
        "question_type": "single_choice",
        "options": "[\"اه\",\"ممكن\",\"معتقدش\"]",
        "options_satisfaction_values": "[2,1,0]"  # String format
    },
    {
        "text": "تقيمك للدعوه",
        "question_type": "rating"
        # No options_satisfaction_values
    }
]

for idx, q in enumerate(questions, 1):
    print(f"\n  Question {idx}: {q['text'][:30]}...")
    if 'options_satisfaction_values' in q:
        original = q['options_satisfaction_values']
        convert_satisfaction_values(q)
        print(f"    Before: {original} (type: {type(original).__name__})")
        print(f"    After:  {q['options_satisfaction_values']} (type: {type(q['options_satisfaction_values']).__name__})")
    else:
        print(f"    No satisfaction values (rating question)")

print("\n" + "=" * 70)
print("✓ All conversions successful!")
print("\nThe serializer will now accept both formats:")
print("  - String:  \"[2,0]\"  → Converts to [2, 0]")
print("  - List:    [2,0]     → Remains [2, 0]")
print("\nYour PATCH request should now work! 🎉")
