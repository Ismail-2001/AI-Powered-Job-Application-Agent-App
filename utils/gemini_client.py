"""
Gemini API Client Wrapper
Role: Handle all interactions with Google Gemini API with robust error handling and retry logic.
"""

from typing import Dict, Any, Optional
import json
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from tenacity import retry, stop_after_attempt, wait_exponential

class GeminiClient:
    """
    Wrapper for Google Gemini API to handle configuration, generation, and error handling.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google API Key
            model_name: Model version to use (default: gemini-1.5-flash)
        """
        if not api_key:
            raise ValueError("API key is required for GeminiClient")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_content(self, prompt: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text content from Gemini with retry logic.

        Args:
            prompt: The input prompt string
            config: Optional generation config (temperature, tokens, etc.)

        Returns:
            Generated text string

        Raises:
            google_exceptions.ResourceExhausted: If rate limit exceeded
            ValueError: If generation fails
        """
        try:
            print(f"🤖 User: Calling Gemini ({self.model_name})...")
            generation_config = config or {"temperature": 0.7}
            
            response = self.model.generate_content(
                prompt, 
                generation_config=generation_config
            )
            return response.text
            
        except google_exceptions.ResourceExhausted:
            print("⚠️  Rate limit exceeded. Retrying...")
            raise
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            raise

    def generate_json(self, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        """
        Generate and parse JSON content.

        Args:
            prompt: Input prompt requesting JSON
            temperature: Lower temperature for structured data (default 0.0)

        Returns:
            Parsed JSON dictionary
        """
        config = {"temperature": temperature, "response_mime_type": "application/json"}
        
        try:
            # Force JSON structure in prompt if not present
            if "JSON" not in prompt:
                prompt += "\n\nReturn the result as a valid JSON object."

            response_text = self.generate_content(prompt, config)
            return self._parse_json_safe(response_text)
            
        except Exception as e:
            print(f"❌ Failed to generate/parse JSON: {e}")
            raise

    def _parse_json_safe(self, text: str) -> Dict[str, Any]:
        """
        Safely parse JSON string, handling Markdown fences and common errors.

        Args:
            text: Raw string from LLM

        Returns:
            Parsed dictionary
        """
        try:
            cleaned = text.strip()
            # Remove markdown code fences
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {e}")
            print(f"Raw text start: {text[:100]}")
            raise ValueError(f"Invalid JSON response: {e}")
