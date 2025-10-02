"""
Test Script for AI Analysis Module
Tests that the OpenAI integration works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ai.analyzer import ReviewAnalyzer
from dotenv import load_dotenv
import os

def test_ai_analyzer():
    """Test the AI analyzer functionality."""
    
    print("=" * 60)
    print("🧪 Testing AI Analysis Module")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your_openai_api_key_here':
        print("\n❌ Error: OPENAI_API_KEY not set in .env file")
        print("Please add your OpenAI API key to the .env file")
        return False
    
    print("✓ OpenAI API key loaded")
    
    # Initialize analyzer
    print("\n1️⃣  Initializing AI analyzer...")
    analyzer = ReviewAnalyzer(api_key)
    print("✓ AI analyzer initialized")
    
    # Test with sample negative reviews
    sample_reviews = [
        {
            'reviewer': 'Angry Bot',
            'text': 'click here for free money www.scam.com'
        },
        {
            'reviewer': 'Competitor Employee',
            'text': 'I work for their competitor and this place is terrible'
        },
        {
            'reviewer': 'Fake Reviewer',
            'text': 'Worst experience ever! Never even been there but giving 1 star!'
        }
    ]
    
    print("\n2️⃣  Testing AI analysis on sample reviews...\n")
    
    for i, review in enumerate(sample_reviews, 1):
        print(f"   Review {i}: {review['reviewer']}")
        print(f"   Text: \"{review['text']}\"")
        print("   Analyzing...")
        
        try:
            result = analyzer.analyze_review(review['text'], review['reviewer'])
            
            print(f"   ✓ Category: {result['category']}")
            print(f"   ✓ Reasoning: {result['reasoning']}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    print("=" * 60)
    print("✅ All AI Analysis Tests Passed!")
    print("=" * 60)
    print("\n💡 Note: Each API call costs a small amount.")
    print("   Check your OpenAI usage at: https://platform.openai.com/usage")
    
    return True


if __name__ == "__main__":
    try:
        success = test_ai_analyzer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
