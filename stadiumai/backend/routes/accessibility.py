import logging
from typing import Dict, Any, List
from fastapi import APIRouter
from pydantic import BaseModel

# Import Gemini and RAG interfaces
from ai_service import ask_gemini, get_venue_context
from ai_service.rag_loader import VENUES_CACHE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Accessibility"])

# Language code resolver
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese (Simplified)"
}

class AccessibilityAssistRequest(BaseModel):
    query: str
    venue_id: str
    language: str
    need: str # "mobility" | "visual" | "hearing" | "general"

class AccessibilityAssistResponse(BaseModel):
    response: str
    accessible_features_nearby: List[str]

@router.post("/assist", response_model=AccessibilityAssistResponse)
async def accessibility_assist_endpoint(payload: AccessibilityAssistRequest):
    """
    POST /accessibility/assist
    
    Provides specialized assistance content for fans with accessibility needs.
    """
    target_id = payload.venue_id
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    venue = VENUES_CACHE.get(target_id)
    
    # 1. Fetch relevant sections of the venue context
    context = get_venue_context(target_id, ["gate", "emergency", "exit", "restroom", "facilities"])
    
    # Resolve full language name
    lang_name = LANGUAGE_MAP.get(payload.language.lower(), payload.language)
    
    # 2. Adapt System Prompt guidelines per need
    need = payload.need.lower().strip()
    need_guideline = ""
    if need == "mobility":
        need_guideline = "Focus on ramps, elevators, accessible seating, and accessible restrooms."
    elif need == "visual":
        need_guideline = "Give detailed verbal descriptions and landmark-based directions. Avoid using 'turn left/right' instructions, use distances instead."
    elif need == "hearing":
        need_guideline = "Provide text-based information only. Mention visual announcement boards, and do not make any audio or listening references."
    else:  # general
        need_guideline = "Use a warm, patient tone with short, simple sentences."
        
    system_prompt = (
        "You are StadiumAI Accessibility Copilot for FIFA World Cup 2026.\n"
        f"Always respond in {lang_name}. Max 2 short sentences. Use simple clear words.\n"
        f"Accessibility need instructions: {need_guideline}\n"
        f"Venue layout: {context}"
    )
    
    # 3. Dynamic lookup of accessible features from the venue JSON object
    features = []
    if venue:
        # Resolve accessible gates
        gates = [g.get("name") for g in venue.get("gates", []) if isinstance(g, dict) and g.get("accessible") == True]
        for g in gates:
            features.append(f"Accessible Gate: {g}")
            
        # Resolve restrooms and medical
        facilities = venue.get("facilities", {})
        if isinstance(facilities, dict):
            for restroom in facilities.get("restrooms", []):
                # Include standard concourse restrooms or family restrooms as helpful markers
                features.append(f"Restroom Facility: {restroom}")
            for med in facilities.get("medical", []):
                features.append(f"Medical Aid: {med}")
                
        # Evacuation / emergency exit ramps
        for e in venue.get("emergency_exits", []):
            if "ramp" in e.lower() or "rampa" in e.lower():
                features.append(f"Accessible Exit Ramp: {e}")
                
    # Select first 3 features to return
    accessible_features_nearby = features[:3]
    
    try:
        reply = await ask_gemini(payload.query, system_prompt=system_prompt)
        return AccessibilityAssistResponse(
            response=reply.strip(),
            accessible_features_nearby=accessible_features_nearby
        )
    except Exception as e:
        logger.error(f"Failed to query Gemini in accessibility_assist_endpoint: {e}")
        # Build local fallback response
        if need == "mobility":
            fallback_res = "Ramps and elevators are available at all main color-coded entry zones. Accessible restrooms are located on all concourses."
        elif need == "visual":
            fallback_res = "Staff are positioned every 50 meters to guide you. Landmark announcement points are located at key entrance gates."
        elif need == "hearing":
            fallback_res = "Review visual display boards above each seating tier. Text support is active at the Info Desk."
        else:
            fallback_res = "We are here to support you. Please tell any staff member if you need help."
            
        return AccessibilityAssistResponse(
            response=fallback_res,
            accessible_features_nearby=accessible_features_nearby
        )
