"""Quick AI test with corrected categories"""
import os
from dotenv import load_dotenv
load_dotenv()

from src.ai.analyzer import ReviewAnalyzer

api_key = os.getenv('OPENAI_API_KEY')
analyzer = ReviewAnalyzer(api_key)

print("Testing AI with Corrected Google Categories\n")
print("=" * 70)

# Test 1: Review mentioning employee name (should be Bullying/Harassment)
test1 = "Ron Johnson was rude and unhelpful. Terrible service from him."
result1 = analyzer.analyze_review(test1, "John Doe")
print(f"Test 1: Review mentioning employee name negatively")
print(f"  Category: {result1['category']}")
print(f"  Expected: Bullying or harassment")
print(f"  Result: {'✅ CORRECT' if 'harassment' in result1['category'].lower() else '❌ WRONG'}\n")

# Test 2: Review with actual phone number (should be Personal Information)
test2 = "Call me at 555-123-4567 to discuss this issue"
result2 = analyzer.analyze_review(test2, "Jane Smith")
print(f"Test 2: Review containing actual phone number")
print(f"  Category: {result2['category']}")
print(f"  Expected: Personal information")
print(f"  Result: {'✅ CORRECT' if 'information' in result2['category'].lower() else '❌ WRONG'}\n")

# Test 3: Vague incomplete review (should be Low Quality)
test3 = "Bad experience. Very disappointed."
result3 = analyzer.analyze_review(test3, "Bob Jones")
print(f"Test 3: Vague, unhelpful review")
print(f"  Category: {result3['category']}")
print(f"  Expected: Low quality information or Not helpful")
print(f"  Result: {'✅ CORRECT' if ('low quality' in result3['category'].lower() or 'not helpful' in result3['category'].lower()) else '❌ WRONG'}\n")

print("=" * 70)
