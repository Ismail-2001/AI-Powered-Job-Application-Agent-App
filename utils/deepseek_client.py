"""
DeepSeek API Client Wrapper
Role: Handle all interactions with DeepSeek API via OpenAI client with robust error handling.
"""

from typing import Dict, Any, Optional
import json
import os
from openai import OpenAI, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential

class DeepSeekClient:
    """
    Wrapper for DeepSeek API (OpenAI-compatible) to handle configuration, generation, and error handling.
    """
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        """
        Initialize the DeepSeek client.

        Args:
            api_key: DeepSeek API Key
            model_name: Model version to use (default: deepseek-chat)
        """
        if not api_key:
            raise ValueError("API key is required for DeepSeekClient")
            
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model_name = model_name

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_content(self, prompt: str, system_instruction: str = "", config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text content from DeepSeek with retry logic.

        Args:
            prompt: The input prompt string
            system_instruction: System prompt/role definition
            config: Optional generation config (temperature, etc.)

        Returns:
            Generated text string
        """
        try:
            print(f"🤖 User: Calling DeepSeek ({self.model_name})...")
            temperature = config.get("temperature", 0.7) if config else 0.7
            
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                stream=False
            )
            return response.choices[0].message.content
            
        except RateLimitError:
            print("⚠️  Rate limit exceeded. Retrying...")
            raise
        except Exception as e:
            print(f"❌ DeepSeek API Error: {e}")
            raise

    def generate_json(self, prompt: str, system_instruction: str = "", temperature: float = 0.0) -> Dict[str, Any]:
        """
        Generate and parse JSON content.

        Args:
            prompt: Input prompt requesting JSON
            system_instruction: System role
            temperature: Lower temperature for structured data (default 0.0)

        Returns:
            Parsed JSON dictionary
        """
        config = {"temperature": temperature}
        
        try:
            # Force JSON structure in prompt if not present
            if "JSON" not in prompt:
                prompt += "\n\nReturn the result as a valid JSON object."
            if "JSON" not in system_instruction:
                system_instruction += "\nProvide output in JSON format."

            response_text = self.generate_content(prompt, system_instruction, config)
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
            # Try to extract JSON from text if it's embedded
            try:
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
            except:
                pass
            raise ValueError(f"Invalid JSON response: {e}")
