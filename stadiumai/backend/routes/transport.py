import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

# Add project root to path for local execution imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import Gemini, RAG database loaders
from ai_service import ask_gemini_json, get_venue_context
from ai_service.rag_loader import VENUES_CACHE

router = APIRouter(tags=["Transport"])

logger = logging.getLogger(__name__)

# Language code mapped registry
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese (Simplified)"
}

class TransportRequest(BaseModel):
    venue_id: str
    match_time_24h: str
    current_time_24h: str
    origin: str
    language: str

class TransportResponse(BaseModel):
    recommendation: str
    suggested_departure: Optional[str] = None
    options: List[str]

def calculate_minutes_left(match_time_str: str, current_time_str: str) -> int:
    """
    Computes time difference in minutes from match_time_24h and current_time_24h.
    Assumes standard format "HH:MM". Handles cross-midnight wraps safely.
    """
    try:
        match_h, match_m = map(int, match_time_str.split(':'))
        curr_h, curr_m = map(int, current_time_str.split(':'))
        
        match_total = match_h * 60 + match_m
        curr_total = curr_h * 60 + curr_m
        
        diff = match_total - curr_total
        # If difference is negative, assume match time wraps around to the next day
        if diff < -12 * 60:
            diff += 24 * 60
        return diff
    except Exception as e:
        logger.warning(f"Error parsing time inputs: {match_time_str}, {current_time_str}. Defaulting to 90 mins.")
        return 90

@router.post("/recommend", response_model=TransportResponse)
async def get_transport_recommendation(payload: TransportRequest):
    """
    POST /api/transport/recommend
    
    1. Extracts transport context details from stadium database
    2. Calculates minutes until the match kickoff
    3. Prompts Gemini (via ask_gemini) for recommendation lists
    4. Automatically recovers/selects fallback options from the venue DB if AI fails
    """
    target_id = payload.venue_id
    # Resilient key lookup for stadium ID matching (e.g. mapping "sofi" to "venue-sofi")
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    venue = VENUES_CACHE.get(target_id)
    
    # 1. Fetch transport details from data concourse
    transport_context = get_venue_context(target_id, query_keywords=["transport", "metro"])
    
    # 2. Compute minutes remaining
    minutes_left = calculate_minutes_left(payload.match_time_24h, payload.current_time_24h)
    
    # Resolve language
    lang_name = LANGUAGE_MAP.get(payload.language.lower(), payload.language)
    
    system_prompt = f"""You are a transport advisor for the stadium.
Recommend the best way to get from {payload.origin} to the stadium in {lang_name}.
Match at {payload.match_time_24h}, current time {payload.current_time_24h}.
Suggest departure time.
NO markdown, NO headers, NO bullets. Just 2-3 sentences.

Transport options: {transport_context}"""
    
    try:
        from ai_service.response_formatter import format_transport_response, strip_markdown
        from ai_service import ask_gemini
        
        # Call Gemini Text
        ai_response = await ask_gemini(
            f"Best transport from {payload.origin} to stadium", 
            system_prompt=system_prompt, 
            output_format="clean_text"
        )
        ai_response = strip_markdown(ai_response)
        
        formatted = format_transport_response(ai_response)
        
        # Ensure suggested_departure defaults gracefully if extraction missed
        if not formatted.get("suggested_departure"):
            # Deduct 90 mins from kickoff for a logical departure time statement
            try:
                match_h, match_m = map(int, payload.match_time_24h.split(':'))
                dep_m_total = match_h * 60 + match_m - 90
                if dep_m_total < 0:
                    dep_m_total += 24 * 60
                formatted["suggested_departure"] = f"{dep_m_total // 60:02d}:{dep_m_total % 60:02d} PM" if dep_m_total // 60 >= 12 else f"{dep_m_total // 60:02d}:{dep_m_total % 60:02d} AM"
            except Exception:
                formatted["suggested_departure"] = "18:30 PM"
                
        return formatted
    except Exception as e:
        logger.error(f"Gemini transport query failed: {e}")
        
        # 4. Fallback options builder from venue transport database
        fallback_options = []
        if venue:
            t_data = venue.get("transport", {})
            if isinstance(t_data, dict):
                for val in t_data.values():
                    if isinstance(val, list):
                        for item in val:
                            if isinstance(item, str):
                                fallback_options.append(item)
                                
        if not fallback_options:
            fallback_options = ["Local Metro Transit lines", "Public ride-share shuttles", "On-site general parking zones"]
            
        fallback_rec = f"Travel from {payload.origin} via local rail lines is recommended. Available options: {', '.join(fallback_options)}."
        try:
            match_h, match_m = map(int, payload.match_time_24h.split(':'))
            dep_m_total = match_h * 60 + match_m - 90
            if dep_m_total < 0:
                dep_m_total += 24 * 60
            fallback_arr_dep = f"{dep_m_total // 60:02d}:{dep_m_total % 60:02d} PM"
        except Exception:
            fallback_arr_dep = "06:30 PM"
            
        return TransportResponse(
            recommendation=fallback_rec,
            suggested_departure=fallback_arr_dep,
            options=fallback_options
        )

# Direct execution checks
if __name__ == "__main__":
    import asyncio
    
    async def main():
        payload = TransportRequest(
            venue_id="sofi",
            match_time_24h="20:00",
            current_time_24h="18:30",
            origin="Downtown LA",
            language="en"
        )
        print("--- Testing Transport Recommendation Route (Direct Run) ---")
        try:
            response = await get_transport_recommendation(payload)
            print(f"\nRecommendation:\n{response.recommendation}")
            print(f"\nSuggested Departure: {response.suggested_departure}")
            print("\nOptions:")
            for option in response.options:
                print(f"- {option}")
            print("-" * 60)
        except Exception as e:
            print(f"Direct test run failed: {e}")
            
    asyncio.run(main())
