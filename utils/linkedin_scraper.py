"""
LinkedIn Profile Scraper
Extracts profile data from LinkedIn using web scraping.
Note: For production, use LinkedIn's official API with proper OAuth.
"""

import os
import json
import re
from typing import Dict, Any, Optional

class LinkedInScraper:
    """
    Scrapes LinkedIn profile data.
    Uses AI to parse the raw HTML/text content into structured data.
    """
    
    def __init__(self, llm_client=None):
        """Initialize with optional LLM client for smart parsing"""
        self.llm_client = llm_client
    
    def parse_profile_text(self, profile_text: str) -> Dict[str, Any]:
        """
        Parse raw LinkedIn profile text/content into structured format.
        Uses LLM for intelligent extraction.
        """
        if not self.llm_client:
            raise ValueError("LLM client required for parsing")
        
        prompt = f"""
        Parse this LinkedIn profile content and extract structured information.
        
        LINKEDIN PROFILE CONTENT:
        {profile_text[:8000]}  # Limit to avoid token overflow
        
        OUTPUT FORMAT (JSON):
        {{
            "personal_info": {{
                "name": "Full Name",
                "email": "email if visible or null",
                "phone": "phone if visible or null", 
                "linkedin": "LinkedIn URL",
                "location": "City, Country",
                "headline": "Professional headline"
            }},
            "summary": "Professional summary/about section (2-3 sentences)",
            "skills": {{
                "Technical": ["Skill 1", "Skill 2"],
                "Soft Skills": ["Skill 1", "Skill 2"],
                "Tools": ["Tool 1", "Tool 2"]
            }},
            "experience": [
                {{
                    "company": "Company Name",
                    "title": "Job Title",
                    "dates": "Start - End",
                    "location": "Location",
                    "responsibilities": [
                        "Achievement 1",
                        "Achievement 2"
                    ]
                }}
            ],
            "education": [
                {{
                    "school": "University Name",
                    "degree": "Degree Type",
                    "field": "Field of Study",
                    "dates": "Start - End"
                }}
            ],
            "certifications": ["Cert 1", "Cert 2"]
        }}
        
        RULES:
        1. Extract ALL work experience entries
        2. Preserve exact job titles and company names
        3. Convert responsibilities to achievement-focused bullet points
        4. If data is not available, use null or empty array
        5. Return ONLY valid JSON
        """
        
        return self.llm_client.generate_json(prompt, temperature=0.2)
    
    def create_master_profile(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parsed LinkedIn data into master_profile.json format.
        """
        # Ensure all required fields exist
        personal_info = parsed_data.get("personal_info", {})
        
        master_profile = {
            "personal_info": {
                "name": personal_info.get("name", ""),
                "email": personal_info.get("email", "your.email@example.com"),
                "phone": personal_info.get("phone", "+1 555-0000"),
                "linkedin": personal_info.get("linkedin", ""),
                "location": personal_info.get("location", "")
            },
            "summary": parsed_data.get("summary", ""),
            "skills": parsed_data.get("skills", {
                "Technical": [],
                "Soft Skills": [],
                "Tools": []
            }),
            "experience": parsed_data.get("experience", []),
            "education": parsed_data.get("education", []),
            "certifications": parsed_data.get("certifications", [])
        }
        
        return master_profile
    
    def save_master_profile(self, profile: Dict[str, Any], path: str = "data/master_profile.json"):
        """Save the profile to file"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return path


def import_from_linkedin_text(profile_text: str, llm_client) -> Dict[str, Any]:
    """
    Main function to import LinkedIn profile from pasted text.
    
    Args:
        profile_text: Raw text copied from LinkedIn profile page
        llm_client: DeepSeek or other LLM client for parsing
    
    Returns:
        Parsed and saved master profile
    """
    scraper = LinkedInScraper(llm_client)
    
    # Parse the profile text
    parsed_data = scraper.parse_profile_text(profile_text)
    
    # Convert to master profile format
    master_profile = scraper.create_master_profile(parsed_data)
    
    # Save to file
    scraper.save_master_profile(master_profile)
    
    return master_profile
