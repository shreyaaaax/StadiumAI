import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

import sys
from pathlib import Path

# Add project root to path for local execution imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import Gemini and RAG interfaces
from ai_service import ask_gemini, ask_gemini_json, get_venue_context
from ai_service.rag_loader import VENUES_CACHE

router = APIRouter(tags=["Navigation"])

logger = logging.getLogger(__name__)

# Language code resolution registry
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese (Simplified)"
}

class NavigationRequest(BaseModel):
    from_location: str
    to_location: str
    venue_id: str
    language: str
    accessible: bool

class NavigationResponse(BaseModel):
    text_directions: str
    steps: List[str]
    estimated_minutes: int
    accessible_route: bool
    summary: str
    accessible: bool

@router.post("", response_model=NavigationResponse)
async def get_navigation_directions(payload: NavigationRequest):
    """
    POST /api/navigation/
    
    1. Retrieves the total context summary detailing gates and facilities
    2. Builds instructions depending on the ADA routing flag ('accessible')
    3. Calls ask_gemini (Text) with output_format="clean_text"
    4. Combines responses or resolves target defaults for robust recovery
    """
    target_id = payload.venue_id
    # Resilient key lookup for stadium IDs (e.g. mapping "metlife" to "venue-metlife")
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    # 1. Fetch complete layout containing all keywords (gates, facilities, transit, etc.)
    all_keywords = ["gate", "entrance", "food", "eat", "facilities", "sections", "transport", "metro", "emergency", "exit"]
    context = get_venue_context(target_id, query_keywords=all_keywords)
    
    # Translate language
    lang_name = LANGUAGE_MAP.get(payload.language.lower(), payload.language)
    
    # 2. Compile instructions
    accessibility_instruction = "avoid stairs and suggest ramps/elevators only" if payload.accessible else "suggest standard walkways/stairs/ramps as appropriate"
    accessible_route_context = ""
    if payload.accessible:
        venue = VENUES_CACHE.get(target_id)
        if venue:
            exits = [str(e) for e in venue.get("emergency_exits", []) if e is not None]
            gates = [str(g.get("name")) for g in venue.get("gates", []) if isinstance(g, dict) and g.get("accessible") is True and g.get("name") is not None]
            accessible_route_context = (
                f"\nDedicated Accessible Route Context:\n"
                f"- Accessible Entry/Exit Gates: {', '.join(gates)}\n"
                f"- Dedicated Evacuation and Exit Ramps: {', '.join(exits)}"
            )

    system_prompt = (
        "You are a stadium navigation assistant.\n"
        f"Give step-by-step directions from {payload.from_location} to {payload.to_location}.\n"
        f"Accessible route: {payload.accessible}\n"
        "NO markdown, NO headers, NO bullets. Just numbered steps."
    )
    
    try:
        from ai_service.response_formatter import format_navigation_response, strip_markdown
        
        # Call Gemini Text
        ai_response = await ask_gemini(
            f"Navigate from {payload.from_location} to {payload.to_location}", 
            system_prompt=system_prompt, 
            output_format="clean_text"
        )
        ai_response = strip_markdown(ai_response)
        
        # Extract steps (numbered 1. 2. 3. format)
        steps = [s.strip() for s in ai_response.split('\n') if s.strip()]
        
        formatted = format_navigation_response(steps, ai_response)
        # Compatibility fields
        formatted["text_directions"] = formatted["summary"]
        formatted["accessible_route"] = formatted["accessible"]
        
        return formatted
    except Exception as e:
        logger.error(f"Fallback text directions used due to error: {e}")
        fallback_steps = [
            f"Start walking from {payload.from_location}.",
            f"Follow main corridor signs to {payload.to_location}."
        ]
        formatted = {
            "steps": fallback_steps,
            "summary": f"Directions from {payload.from_location} to {payload.to_location}.",
            "accessible": payload.accessible,
            "estimated_minutes": 8 if payload.accessible else 5,
            "text_directions": f"Directions from {payload.from_location} to {payload.to_location}.",
            "accessible_route": payload.accessible
        }
        return formatted

# Direct execution check
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Setup the requested test parameters
        payload = NavigationRequest(
            from_location="Gate A",
            to_location="Section 112",
            venue_id="metlife",
            language="en",
            accessible=False
        )
        print("--- Testing Navigation Logic (Direct Function Call) ---")
        try:
            response = await get_navigation_directions(payload)
            print(f"\nText Directions:\n{response.text_directions}")
            print("\nJSON Steps:")
            for step in response.steps:
                print(f"- {step}")
            print(f"\nEstimated Minutes: {response.estimated_minutes}")
            print(f"Accessible Route: {response.accessible_route}")
            print("-" * 55)
        except Exception as e:
            print(f"Execution failed: {e}")

    asyncio.run(main())
