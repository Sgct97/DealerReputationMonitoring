"""
Quick test to verify GPT-5 API configuration works correctly.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env file")
    exit(1)

print("=" * 80)
print("🧪 Testing GPT-5 API Configuration")
print("=" * 80)

client = OpenAI(api_key=api_key)
current_date = datetime.now().strftime("%B %d, %Y")

print(f"\n📅 Current date: {current_date}")
print(f"🤖 Model: gpt-5-mini")
print(f"⚙️  Parameters: reasoning_effort=minimal, verbosity=low")

test_prompt = """You are testing. What year is a 2024 Mercedes GLE?

Respond in format:
YEAR: [the year]
REASONING: [explain if 2024 is current, past, or future based on today's date]"""

try:
    print("\n🔄 Making API call...")
    
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": f"You are a helpful assistant. Today's date is {current_date}."},
            {"role": "user", "content": test_prompt}
        ],
        max_completion_tokens=1000  # Needs room for both reasoning tokens + actual response
    )
    
    print("\n✅ API call successful!")
    print("\n🔍 Debug - Full response object:")
    full_response = response.model_dump_json(indent=2)
    print(full_response)
    print("\n" + "=" * 80)
    
    content = response.choices[0].message.content
    
    print("\n📝 Response:")
    print("-" * 80)
    print(content if content else "[EMPTY RESPONSE]")
    print("-" * 80)
    
    # Check if response makes sense
    if "future" in content.lower():
        print("\n⚠️  WARNING: Model thinks 2024 is in the future!")
        print("   This suggests the date context isn't working properly.")
    elif "2024" in content:
        print("\n✅ SUCCESS: Model correctly understands current date!")
    
    print(f"\n💰 Tokens used: {response.usage.total_tokens}")
    print("\n✅ GPT-5 API configuration is working correctly!")
    
except Exception as e:
    print(f"\n❌ API call failed!")
    print(f"Error: {type(e).__name__}: {str(e)}")
    print("\nThis could mean:")
    print("  - GPT-5 model might not be available yet for your API key")
    print("  - The parameters might be incorrect")
    print("  - There's a network/authentication issue")
    exit(1)

print("\n" + "=" * 80)

