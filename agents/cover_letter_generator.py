"""
Cover Letter Generator Agent
Role: Generate personalized, compelling cover letters matching the job and candidate profile.
"""

import json
from typing import Dict, Any
from utils.deepseek_client import DeepSeekClient

class CoverLetterGenerator:
    """
    Agent responsible for writing cover letters.
    """
    
    def __init__(self, client: DeepSeekClient):
        self.client = client
        self.system_instruction = """
        You are an expert Career Coach and Copywriter specializing in cover letters.
        Your goal is to write compelling, personalized letters that connect the candidate's unique value to the company's needs.
        You avoid generic clichés (e.g., "I am writing to apply...").
        You use a professional yet enthusiastic tone.
        """

    def generate(self, profile: Dict[str, Any], job_analysis: Dict[str, Any]) -> str:
        """
        Generate a cover letter.

        Args:
            profile: Candidate's master profile
            job_analysis: Analyzed job requirements

        Returns:
            The body of the cover letter text.
        """
        print("✍️  Writing cover letter...")
        
        prompt = f"""
        Create a compelling cover letter for this job application.

        CANDIDATE PROFILE:
        {json.dumps(profile, indent=2)}

        JOB ANALYSIS:
        {json.dumps(job_analysis, indent=2)}

        STRUCTURE:
        Paragraph 1 (Opening): Strong hook + excitement about the specific role/company.
        Paragraph 2 (The Match): Why this company? Connect their mission/needs to candidate's background.
        Paragraph 3 (The Proof): Highlight the most relevant achievement from the profile that solves a key problem they have.
        Paragraph 4 (Closing): Call to action, availability, and professional sign-off.

        CRITICAL RULES:
        1. Tone: Professional, confident, but grounded (not arrogant).
        2. Length: 250-350 words.
        3. Do NOT include placeholder addresses (header will be handled separately). Just the body.
        4. Use specific keywords from the job analysis.
        5. "Show, don't just tell" - use metrics from the profile.
        """

        # Temperature 0.7 for creativity/personality
        return self.client.generate_content(
            prompt, 
            system_instruction=self.system_instruction, 
            config={"temperature": 0.7}
        )
