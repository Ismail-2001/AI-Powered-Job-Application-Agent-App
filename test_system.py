"""
Test script to verify the AI-Powered Job Application Agent setup.
This script checks dependencies, configuration, and basic functionality.
"""

import sys
import os
import json
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def check_dependencies():
    """Check if all required packages are installed."""
    print("🔍 Checking dependencies...")
    required = {
        'openai': 'openai',
        'docx': 'python-docx',
        'tenacity': 'tenacity',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """Check if .env file exists and has API key."""
    print("\n🔍 Checking environment configuration...")
    env_path = Path(".env")
    
    if not env_path.exists():
        print("  ⚠️  .env file not found")
        print("  💡 Create .env file with: DEEPSEEK_API_KEY=your_key_here")
        return False
    
    # Check if API key is set (don't print the actual key)
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        print("  ⚠️  DEEPSEEK_API_KEY not set or using placeholder")
        print("  💡 Update .env file with your actual API key")
        return False
    
    print("  ✅ .env file found with API key configured")
    return True

def check_profile():
    """Check if master profile exists and is valid JSON."""
    print("\n🔍 Checking master profile...")
    profile_path = Path("data/master_profile.json")
    
    if not profile_path.exists():
        print("  ❌ data/master_profile.json not found")
        return False
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        # Check required fields
        required_fields = ['personal_info', 'summary', 'skills', 'experience']
        missing_fields = [field for field in required_fields if field not in profile]
        
        if missing_fields:
            print(f"  ⚠️  Missing fields: {', '.join(missing_fields)}")
            return False
        
        name = profile.get('personal_info', {}).get('name', 'Unknown')
        print(f"  ✅ Profile loaded for: {name}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error reading profile: {e}")
        return False

def check_structure():
    """Check if project structure is correct."""
    print("\n🔍 Checking project structure...")
    
    required_dirs = ['agents', 'utils', 'data', 'output']
    required_files = [
        'main.py',
        'requirements.txt',
        'agents/job_analyzer.py',
        'agents/cv_customizer.py',
        'utils/deepseek_client.py',
        'utils/document_builder.py'
    ]
    
    all_good = True
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (missing)")
            all_good = False
    
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (missing)")
            all_good = False
    
    return all_good

def main():
    """Run all checks."""
    print("=" * 60)
    print("🧪 AI-Powered Job Application Agent - System Test")
    print("=" * 60)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Project Structure", check_structure),
        ("Master Profile", check_profile),
        ("Environment Config", check_env_file),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Error during {name} check: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✨ All checks passed! System is ready to use.")
        print("💡 Run 'py main.py' to start the application.")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("💡 Refer to README.md for setup instructions.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
