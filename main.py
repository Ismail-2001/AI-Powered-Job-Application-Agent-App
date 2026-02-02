"""
AI-Powered Job Application Agent
Main Orchestrator

Role: Coordinate the workflow between JobAnalyzer, CVCustomizer, and DocumentBuilder.
"""

import os
import sys
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Import our modular components
from utils.deepseek_client import DeepSeekClient
from utils.document_builder import DocumentBuilder
from utils.match_calculator import MatchCalculator
from agents.job_analyzer import JobAnalyzer
from agents.cv_customizer import CVCustomizer
from agents.cover_letter_generator import CoverLetterGenerator
from utils.rag_engine import RAGEngine

# Load environment variables
load_dotenv()

def load_profile(path: str = "data/master_profile.json") -> Dict[str, Any]:
    """
    Load the master profile JSON file.
    
    Args:
        path: Path to the master profile JSON file
        
    Returns:
        Dictionary containing the candidate's profile data
        
    Raises:
        SystemExit: If file not found or invalid JSON
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Profile file not found at {path}")
        print("💡 Tip: Update 'data/master_profile.json' with your details.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {path}")
        sys.exit(1)

def calculate_match_score(customized_cv: Dict[str, Any], job_keywords: List[str]) -> Dict[str, Any]:
    """
    Calculate the keyword match score between the CV and Job requirements.
    
    Args:
        customized_cv: The tailored CV data
        job_keywords: List of keywords extracted from job description
        
    Returns:
        Dictionary with score metrics
    """
    # 1. Flatten CV content into a single string for searching
    cv_text = f"{customized_cv.get('summary', '')} "
    
    # Add skills
    skills_data = customized_cv.get('skills', {})
    if isinstance(skills_data, dict):
        for category in skills_data:
            cv_text += " ".join(skills_data[category]) + " "
    
    # Add experience achievements
    for role in customized_cv.get('experience', []):
        cv_text += f"{role.get('title', '')} "
        cv_text += " ".join(role.get('achievements', [])) + " "
    
    cv_text = cv_text.lower()
    
    # 2. Count matches
    matched = []
    missing = []
    
    for kw in job_keywords:
        if kw.lower() in cv_text:
            matched.append(kw)
        else:
            missing.append(kw)
            
    total = len(job_keywords)
    score = (len(matched) / total * 100) if total > 0 else 0
    
    return {
        "score": round(score, 1),
        "total": total,
        "matched_count": len(matched),
        "matched_list": matched,
        "missing_list": missing
    }

def get_job_description() -> str:
    """
    Get job description from user input.
    
    Returns:
        Job description text as a string
    """
    print("\n📋 Paste the Job Description below (Press Ctrl+Z/D then Enter when done):")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)

def main():
    """
    Main entry point for the application.
    """
    print("🚀 AI-Powered Job Application Agent Initializing (DeepSeek Edition)...")
    
    # 1. Setup & Config
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ Error: DEEPSEEK_API_KEY not found in environment variables.")
        print("💡 Tip: Add DEEPSEEK_API_KEY=your_key to .env file.")
        return

    try:
        client = DeepSeekClient(api_key=api_key)
        builder = DocumentBuilder()
        match_calculator = MatchCalculator()
        
        # Initialize Agents
        job_analyzer = JobAnalyzer(client)
        cv_customizer = CVCustomizer(client)
        cover_letter_generator = CoverLetterGenerator(client)
        rag_engine = RAGEngine()

        # 2. Load Data
        print("\n📂 Loading master profile...")
        profile = load_profile()
        print(f"✅ Loaded profile for {profile.get('personal_info', {}).get('name')}")

        # 3. Get Input
        job_description = get_job_description()
        if len(job_description) < 50:
            print("⚠️  Warning: Job description seems too short. Results may be poor.")

        # 4. Analyze Job
        print("\n🔍 Phase 1: Analyzing Job Description...")
        analysis = job_analyzer.analyze(job_description)
        # Debug print
        # print(json.dumps(analysis, indent=2))
        
        role_title = analysis.get('role_info', {}).get('title', 'Unknown Role')
        company = analysis.get('role_info', {}).get('company', 'Unknown Company')
        print(f"✅ Job Analyzed: {role_title} at {company}")
        
        # 4.5. RAG Retrieval (New Strategic Improvement)
        print("\n🔍 Phase 1.5: Retrieving Relevant Contexts (RAG)...")
        keywords = analysis.get("keywords", {}).get("ats_keywords", [])
        relevant_snippets = rag_engine.retrieve_relevant_experience(keywords)
        
        # 5. Customize CV
        print("\n🎨 Phase 2: Customizing CV...")
        customized_cv = cv_customizer.customize(profile, analysis, relevant_snippets)
        print("✅ CV content customized for ATS optimization.")

        # 5.1 Calculate Match Score (New Validation Step)
        job_keywords = analysis.get("keywords", {}).get("ats_keywords", [])
        match_metrics = calculate_match_score(customized_cv, job_keywords)
        print(f"\n📊 ATS Match Score: {match_metrics['score']}%")
        print(f"   🔑 Keywords Matched: {match_metrics['matched_count']}/{match_metrics['total']}")
        
        if match_metrics['score'] < 70:
            print(f"   ⚠️  Warning: Lower match score. Consider adding more details to your master profile.")
        
        # 6. Generate Information
        print("\n✍️  Phase 3: Writing Cover Letter...")
        cover_letter_text = cover_letter_generator.generate(profile, analysis)

        # 7. Generate Documents
        print("\n📄 Phase 4: Generating Documents...")
        # Sanitize filename for Windows
        import re
        def sanitize_filename(name):
            return re.sub(r'[<>:"/\\|?*]', '', name).strip().replace(' ', '_')

        safe_title = sanitize_filename(role_title)
        safe_company = sanitize_filename(company)
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        cv_filename = f"output/CV_{safe_company}_{safe_title}.docx"
        cl_filename = f"output/CL_{safe_company}_{safe_title}.docx"
        
        # Save CV
        builder.create_cv(customized_cv, cv_filename)
        # Save Cover Letter
        builder.create_cover_letter(cover_letter_text, profile, cl_filename)
        
        print(f"\n✨ SUCCESS!")
        print(f"   1. CV: {cv_filename}")
        print(f"   2. Cover Letter: {cl_filename}")
        print("   Good luck with your application! 🚀")

    except Exception as e:
        print(f"\n❌ An error occurred during the process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
