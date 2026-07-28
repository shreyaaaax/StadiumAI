import os
import logging
import asyncio
import datetime
import json
import re
from typing import Dict, Any, Optional

try:
    from rate_guard import check_rate_limit, add_to_rate_guard_cache
except ImportError:
    try:
        from ai_service.rate_guard import check_rate_limit, add_to_rate_guard_cache
    except ImportError:
        from stadiumai.ai_service.rate_guard import check_rate_limit, add_to_rate_guard_cache
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from standard paths
load_dotenv()
# Also search parent directory of the current file (which is the stadiumai root) for .env
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Retrieve the API key. Fall back to genai_stadium_apikey if GEMINI_API_KEY is not defined directly.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("genai_stadium_apikey")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def ask_gemini(prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 1000, output_format: str = "clean_text") -> str:
    """
    Sends a text prompt to the Gemini API and returns the generated response.
    
    - Supports custom system instructions/prompts
    - Limits response tokens to max_tokens (defaults to 1000 for free tier limits)
    - Retries once after waiting 60 seconds on a 429 rate limit error
    - Logs request and response timestamps to the console
    """
    # Enforce RateGuard check
    guard_result = check_rate_limit(prompt, system_prompt)
    if guard_result is not None:
        logger.warning("RateGuard returned fallback/busy response instead of making API call.")
        return guard_result

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Please configure it in your .env file.")

    # Add formatting instruction to system prompt
    format_instructions = {
        "clean_text": "Output ONLY plain text. NO markdown, NO **, NO headers (###), NO bullets (*). Just clear, simple sentences.",
        "json": "Output ONLY valid JSON. No markdown, no text before/after JSON.",
        "structured": "Output ONLY 2-3 short sentences. No markdown, no bullets, no headers. Be concise."
    }
    
    enhanced_system = f"{system_prompt}\n\n[CRITICAL FORMAT INSTRUCTION: {format_instructions.get(output_format, format_instructions['clean_text'])}]"

    url = f"{BASE_URL}/models/{MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    payload: Dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    if enhanced_system:
        payload["systemInstruction"] = {
            "parts": [
                {"text": enhanced_system}
            ]
        }
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        timestamp_send = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp_send}] Sending text request to Gemini API (Model: {MODEL})")
        
        response = await client.post(url, json=payload)
        
        if response.status_code == 429:
            timestamp_limit = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_limit}] Rate limit hit (429). Waiting 60 seconds before retrying...")
            await asyncio.sleep(60)
            
            timestamp_retry = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_retry}] Retrying text request to Gemini API (Model: {MODEL})")
            response = await client.post(url, json=payload)
            
        response.raise_for_status()
        data = response.json()
        
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            timestamp_recv = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_recv}] Response successfully received from Gemini API")
            
            # Cache the successful response
            venue_match = re.search(r"\b(venue-\w+)\b", system_prompt + " " + prompt, re.IGNORECASE)
            venue_id = venue_match.group(1).lower() if venue_match else "general"
            add_to_rate_guard_cache(venue_id, prompt, text)
            
            return text
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response structure from Gemini API: {data}") from e

async def ask_gemini_json(prompt: str, schema_hint: Any, max_tokens: int = 1000) -> dict:
    """
    Sends a prompt to the Gemini API, requesting a structured response in JSON format.
    
    - Injects structural instructions and the schema content into the prompt
    - Configures Gemini generationConfig with application/json mimetype and maxOutputTokens
    - Retries once after waiting 60 seconds on a 429 rate limit error
    - Logs request and response timestamps to the console
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Please configure it in your .env file.")

    url = f"{BASE_URL}/models/{MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    generation_config: Dict[str, Any] = {
        "temperature": 0.1,  # Low temperature works best for JSON/structured responses
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json"
    }
    
    # Enable schema validation if a schema dict/JSON-schema is supplied
    if schema_hint and isinstance(schema_hint, dict):
        generation_config["responseSchema"] = schema_hint
        
    # Standardize prompt with the schema information to guide the model
    formatted_prompt = prompt
    formatted_prompt += "\n\nCRITICAL: The output must be valid JSON in the following format:\n"
    if isinstance(schema_hint, str):
        formatted_prompt += schema_hint
    else:
        formatted_prompt += json.dumps(schema_hint, indent=2)
        
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": formatted_prompt}
                ]
            }
        ],
        "generationConfig": generation_config
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        timestamp_send = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp_send}] Sending JSON request to Gemini API (Model: {MODEL})")
        
        response = await client.post(url, json=payload)
        
        if response.status_code == 429:
            timestamp_limit = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_limit}] Rate limit hit (429). Waiting 60 seconds before retrying...")
            await asyncio.sleep(60)
            
            timestamp_retry = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_retry}] Retrying JSON request to Gemini API (Model: {MODEL})")
            response = await client.post(url, json=payload)
            
        response.raise_for_status()
        data = response.json()
        
        text = ""
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            timestamp_recv = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp_recv}] JSON response successfully received from Gemini API")
            return json.loads(text.strip())
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response structure from Gemini API: {data}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse response text as JSON. Response: '{text}'") from e

class GeminiClient:
    """
    Backward-compatible client class wrapping ask_gemini/ask_gemini_json.
    """
    def __init__(self, api_key: Optional[str] = None):
        global GEMINI_API_KEY
        if api_key:
            GEMINI_API_KEY = api_key
            
    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        return await ask_gemini(prompt, system_prompt=system_instruction or "")

# Core main entry point for quick verification
if __name__ == "__main__":
    async def main():
        print("--- Testing Gemini Client ask_gemini ---")
        try:
            result = await ask_gemini("What is FIFA World Cup 2026?")
            print("\nResult:")
            print(result)
            print("-" * 40)
            
            print("\n--- Testing Gemini Client ask_gemini_json ---")
            sample_schema = {
                "type": "object",
                "properties": {
                    "host_countries": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "year": {"type": "integer"},
                    "teams_count": {"type": "integer"}
                },
                "required": ["host_countries", "year", "teams_count"]
            }
            json_result = await ask_gemini_json("Give me the host countries, year, and teams count for FIFA World Cup 2026.", sample_schema)
            print("\nJSON Result:")
            print(json.dumps(json_result, indent=2))
            print("-" * 40)
            
        except Exception as e:
            print(f"\nError occurred during testing: {e}")
            print("-" * 40)

    asyncio.run(main())
