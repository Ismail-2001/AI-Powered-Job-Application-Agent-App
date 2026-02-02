"""
Job Analyzer Agent
Role: Analyze job descriptions to extract requirements, skills, and keywords.
"""

from typing import Dict, Any, List
from utils.deepseek_client import DeepSeekClient

class JobAnalyzer:
    """
    Agent responsible for breaking down job descriptions into structured data.
    """
    
    def __init__(self, client: DeepSeekClient):
        self.client = client
        self.system_instruction = """
        You are an expert Recruitment Analyst with 20 years of experience in Talent Acquisition.
        Your role is to deconstruct job descriptions to understand exactly what the employer is looking for.
        You optimize for Applicant Tracking Systems (ATS) by identifying exact keywords and skills.
        
        CRITICAL: If a specific piece of information (like Company Name or Location) is NOT explicitly 
        mentioned in the text, return exactly "Unknown" for that field. Do NOT guess or hallucinate.
        Return raw JSON only.
        """

    def _validate_analysis(self, analysis: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Validate the analysis results to prevent hallucinations.
        
        Args:
            analysis: The JSON dictionary from LLM
            raw_text: The original job description text
            
        Returns:
            Validated analysis dictionary
        """
        role_info = analysis.get("role_info", {})
        
        # Check for Company Name hallucination
        company = role_info.get("company", "Unknown")
        if company and company != "Unknown":
            # If the company name isn't found in the raw text (case-insensitive check)
            if company.lower() not in raw_text.lower():
                print(f"⚠️  Validation: Detected potential hallucination for company '{company}'. Resetting to 'Unknown'.")
                role_info["company"] = "Unknown"
        
        # Ensure lists are actually lists
        if not isinstance(analysis.get("keywords", {}).get("ats_keywords"), list):
            analysis["keywords"]["ats_keywords"] = []
            
        return analysis

    def analyze(self, job_description: str) -> Dict[str, Any]:
        """
        Analyze a job description string.

        Args:
            job_description: The full text of the job posting

        Returns:
            Structured dictionary containing role info, requirements, and keywords.
        """
        print(f"🔍 Analyzing job description ({len(job_description)} chars)...")

        prompt = f"""
        Analyze this job description and extract comprehensive information:

        JOB DESCRIPTION:
        {job_description}

        Extract and return a JSON object with this EXACT structure:
        {{
          "role_info": {{
            "title": "Job Title",
            "company": "Company Name (if found)",
            "location": "Location (if found)",
            "level": "Junior/Mid/Senior/Lead"
          }},
          "requirements": {{
            "must_have_skills": ["Skill 1", "Skill 2"],
            "nice_to_have_skills": ["Skill 3", "Skill 4"],
            "education": "Required Degree/Certifications",
            "years_experience": "X years"
          }},
          "keywords": {{
            "ats_keywords": ["Keyword1", "Keyword2"],
            "soft_skills": ["Soft Skill 1"]
          }},
          "summary": "Brief 2-sentence summary of the role"
        }}

        CRITICAL RULES:
        1. Extract information EXACTLY as stated in job description
        2. Use EXACT keywords for ATS optimization (preserve capitalization, e.g. "Python" not "python")
        3. Prioritize skills based on emphasis in posting
        4. If information not provided, use null or empty array
        5. Be objective - don't make assumptions
        6. Return ONLY valid JSON
        """

        # Temperature 0.1 for structured extraction
        result = self.client.generate_json(prompt, system_instruction=self.system_instruction, temperature=0.1)
        
        # Apply validation layer
        return self._validate_analysis(result, job_description)
