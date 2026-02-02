import sys
try:
    import google.generativeai
    import docx
    import tenacity
    import dotenv
    print("✅ All dependencies imported successfully!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
