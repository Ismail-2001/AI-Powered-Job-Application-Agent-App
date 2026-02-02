"""
Quick verification script to test if all services are running correctly
"""
import requests
import sys

def test_api_health():
    """Test if the FastAPI server is running"""
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code == 200:
            print("✅ API Server (Port 8000): ONLINE")
            return True
        else:
            print(f"⚠️  API Server: Unexpected status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API Server (Port 8000): OFFLINE - {e}")
        return False

def test_web_interface():
    """Test if the web interface is accessible"""
    try:
        response = requests.get('http://localhost:3000/', timeout=5)
        if response.status_code == 200:
            print("✅ Web Interface (Port 3000): ONLINE")
            return True
        else:
            print(f"⚠️  Web Interface: Unexpected status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Web Interface (Port 3000): OFFLINE - {e}")
        return False

def test_api_docs():
    """Test if API documentation is accessible"""
    try:
        response = requests.get('http://localhost:8000/docs', timeout=5)
        if response.status_code == 200:
            print("✅ API Documentation (/docs): ACCESSIBLE")
            return True
        else:
            print(f"⚠️  API Docs: Unexpected status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API Documentation: NOT ACCESSIBLE - {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing AI Job Application Agent Services...\n")
    
    results = []
    results.append(test_api_health())
    results.append(test_web_interface())
    results.append(test_api_docs())
    
    print("\n" + "="*50)
    if all(results):
        print("✅ ALL SERVICES RUNNING SUCCESSFULLY!")
        print("\n📍 Access Points:")
        print("   • Web Interface: http://localhost:3000")
        print("   • API Server: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("⚠️  SOME SERVICES ARE NOT RUNNING")
        print("\n💡 Make sure to start:")
        print("   1. python api.py")
        print("   2. cd web && python -m http.server 3000")
        sys.exit(1)
