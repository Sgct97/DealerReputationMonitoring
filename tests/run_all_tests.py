"""
Master Test Runner
Runs all component tests in sequence.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def run_all_tests():
    """Run all tests in sequence."""
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "DEALER REPUTATION KEEPER - TEST SUITE" + " " * 10 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    results = {}
    
    # Test 1: Database
    print("🔹 TEST 1/3: Database Module")
    print("-" * 60)
    try:
        from test_database import test_database
        results['database'] = test_database()
    except Exception as e:
        print(f"❌ Database test crashed: {str(e)}")
        results['database'] = False
    
    print("\n" + "=" * 60 + "\n")
    input("Press Enter to continue to AI test...")
    print()
    
    # Test 2: AI Analysis
    print("🔹 TEST 2/3: AI Analysis Module")
    print("-" * 60)
    try:
        from test_ai import test_ai_analyzer
        results['ai'] = test_ai_analyzer()
    except Exception as e:
        print(f"❌ AI test crashed: {str(e)}")
        results['ai'] = False
    
    print("\n" + "=" * 60 + "\n")
    input("Press Enter to continue to Email test...")
    print()
    
    # Test 3: Email Notifications
    print("🔹 TEST 3/3: Email Notification Module")
    print("-" * 60)
    try:
        from test_email import test_email_notifier
        results['email'] = test_email_notifier()
    except Exception as e:
        print(f"❌ Email test crashed: {str(e)}")
        results['email'] = False
    
    # Final Summary
    print("\n\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "TEST SUMMARY" + " " * 26 + "║")
    print("╠" + "═" * 58 + "╣")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"║  {test_name.capitalize():20} {status:36} ║")
    
    print("╚" + "═" * 58 + "╝")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Your system is ready.")
        print("   Next step: Complete the scraper by finding the Google selectors.")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before proceeding.")
        failed = [name for name, passed in results.items() if not passed]
        print(f"   Failed: {', '.join(failed)}")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
