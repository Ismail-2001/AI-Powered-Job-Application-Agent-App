import os
import io
import json
from typing import Dict, Any
import PyPDF2
import docx
from utils.deepseek_client import DeepSeekClient

class ResumeParser:
    """Utility to extract text from documents and structure it using AI."""
    
    def __init__(self, client: DeepSeekClient):
        self.client = client

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract plain text from a PDF file."""
        text = ""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract plain text from a DOCX file."""
        text = ""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
        return text

    def parse_resume(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Process the file and return a structured profile JSON."""
        ext = filename.split('.')[-1].lower()
        
        if ext == 'pdf':
            raw_text = self.extract_text_from_pdf(file_bytes)
        elif ext in ['docx', 'doc']:
            raw_text = self.extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
        if not raw_text.strip():
            raise ValueError("Could not extract any text from the resume.")

        # AI Structuring Prompt
        system_prompt = """
        You are an expert Resume Parser. Your goal is to extract information from raw resume text 
        and format it into a high-quality, structured JSON profile.
        
        JSON Structure:
        {
            "personal_info": { "name": "", "email": "", "phone": "", "location": "" },
            "summary": "Professional summary...",
            "experience": [
                { "title": "", "company": "", "duration": "", "description": ["bullet points"] }
            ],
            "education": [
                { "degree": "", "school": "", "year": "" }
            ],
            "skills": { "Category": ["Skill 1", "Skill 2"] }
        }
        
        Rules:
        1. Be thorough and accurate.
        2. If a field is missing, leave it as an empty string or empty list.
        3. Extract experience bullets carefully.
        4. Focus on professional details.
        """
        
        prompt = f"Extract the profile information from this resume text:\n\n{raw_text}"
        
        try:
            structured_data = self.client.generate_json(prompt, system_prompt)
            return structured_data
        except Exception as e:
            print(f"AI Parsing error: {e}")
            raise ValueError(f"AI failed to structure the resume: {str(e)}")
