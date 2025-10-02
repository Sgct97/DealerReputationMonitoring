"""
Quick Proxy Test Script
Tests Oxylabs proxy connection before running the full scraper.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get proxy configuration
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

print("=" * 60)
print("🔌 Testing Oxylabs Proxy Connection")
print("=" * 60)

# Check if proxy is configured
if not proxy_server or not proxy_username or not proxy_password:
    print("❌ Error: Proxy not configured in .env file")
    print(f"   PROXY_SERVER: {'✓' if proxy_server else '✗ Missing'}")
    print(f"   PROXY_USERNAME: {'✓' if proxy_username else '✗ Missing'}")
    print(f"   PROXY_PASSWORD: {'✓' if proxy_password else '✗ Missing'}")
    exit(1)

print(f"\n📋 Configuration:")
print(f"   Server: {proxy_server}")
print(f"   Username: {proxy_username}")
print(f"   Password: {'*' * len(proxy_password)} (hidden)")

# Build proxy URL with authentication
proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_server.replace('http://', '')}"

proxies = {
    'http': proxy_url,
    'https': proxy_url
}

print(f"\n🔍 Testing connection to IP check service...")

try:
    # Test 1: Check IP address
    print("\n1️⃣ Checking your IP address through proxy...")
    response = requests.get('http://ip.oxylabs.io/location', proxies=proxies, timeout=30)
    
    if response.status_code == 200:
        print("✅ Proxy connection successful!")
        print(f"\n📍 IP Information:")
        data = response.json()
        print(f"   IP Address: {data.get('ip', 'N/A')}")
        print(f"   Country: {data.get('country', 'N/A')}")
        print(f"   City: {data.get('city', 'N/A')}")
        print(f"   Provider: {data.get('asn', {}).get('name', 'N/A')}")
        
        # Check if it's a residential IP
        if 'asn' in data and 'name' in data['asn']:
            provider = data['asn']['name'].lower()
            if any(isp in provider for isp in ['comcast', 'verizon', 'att', 'charter', 'cox', 'frontier']):
                print(f"\n✅ Confirmed: This is a RESIDENTIAL IP (ISP: {data['asn']['name']})")
            else:
                print(f"\n⚠️  Note: IP provider is {data['asn']['name']}")
    else:
        print(f"❌ Error: Got status code {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
    
    # Test 2: Quick Google test
    print(f"\n2️⃣ Testing access to Google...")
    google_response = requests.get('https://www.google.com', proxies=proxies, timeout=30)
    
    if google_response.status_code == 200:
        print("✅ Can access Google through proxy!")
    else:
        print(f"⚠️  Google returned status code: {google_response.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ Proxy Test Complete - Ready to scrape!")
    print("=" * 60)
    
except requests.exceptions.ProxyError as e:
    print(f"\n❌ Proxy Connection Failed!")
    print(f"   Error: {str(e)}")
    print(f"\n💡 Check:")
    print(f"   1. Username and password are correct")
    print(f"   2. Proxy server address is correct")
    print(f"   3. Your Oxylabs account has active residential proxies")
    exit(1)
    
except requests.exceptions.Timeout:
    print(f"\n❌ Connection Timeout!")
    print(f"   The proxy took too long to respond")
    exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {str(e)}")
    exit(1)

