"""
Test script for the Agentic AI API
"""

import requests
import json
import time
import subprocess
import os

def test_api():
    print("🚀 Starting API server for testing...")
    # Start server in background
    process = subprocess.Popen(["py", "api.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5) # Wait for server to boot
    
    try:
        url = "http://127.0.0.1:8000/apply"
        job_desc = """
        Job Title: AI Engineer
        Company: TechNova
        Requirements:
        - Proficiency in Python
        - Experience with LLMs and Agentic Workflows
        - Knowledge of RAG systems
        """
        
        print(f"📡 Sending application request to {url}...")
        response = requests.post(url, json={"job_description": job_desc})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response Received Successfully!")
            print(f"🔍 Analysis: {data['analysis']['role_info']['title']} at {data['analysis']['role_info']['company']}")
            print(f"📄 Generated Files: {data['files']}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        print("🛑 Terminating API server...")
        process.terminate()

if __name__ == "__main__":
    test_api()
