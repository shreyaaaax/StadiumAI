import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Add project root to path for local imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import Gemini Client
from ai_service import ask_gemini

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Crowd"])

class PredictRequest(BaseModel):
    venue_id: str
    current_phase: str
    query: str

class ZoneDetail(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    density_percent: Optional[int] = None
    status: Optional[str] = None

class PredictResponse(BaseModel):
    zones: list[ZoneDetail]
    summary: str
    recommendations: list[str]
    recommendation: Optional[str] = None

def get_crowd_snapshot(venue_id: str, phase: str = "during_match") -> dict:
    """
    Generate mock crowd density data for a venue.
    Returns a clean dict with zones only — no raw JSON strings.
    """
    # Simulate crowd density per zone based on match phase
    base_data = {
        "pre_match": {
            "zones": [
                {"id": "gate_a", "name": "Gate A - North Entrance", "location": "North side", "type": "gate", "density_percent": 10},
                {"id": "gate_c", "name": "Gate C - South Entrance", "location": "South side", "type": "gate", "density_percent": 14},
                {"id": "concourse_north", "name": "North Concourse", "location": "Level 1, North", "type": "concourse", "density_percent": 60},
                {"id": "concourse_general", "name": "General Concourse", "location": "Level 1, Center", "type": "concourse", "density_percent": 20},
                {"id": "section_upper_west", "name": "Upper Deck - West", "location": "Level 3, West", "type": "seating", "density_percent": 97},
                {"id": "section_mezzanine_east", "name": "Mezzanine - East", "location": "Level 2, East", "type": "seating", "density_percent": 96},
                {"id": "section_lower_north", "name": "Lower Bowl - North", "location": "Level 1, North", "type": "seating", "density_percent": 95},
                {"id": "food_east", "name": "East Concourse Diner", "location": "Level 2, East plaza section", "type": "food", "density_percent": 18},
                {"id": "food_north", "name": "North Plaza Food Court", "location": "Ground level, North concourse", "type": "food", "density_percent": 15},
            ]
        },
        "during_match": {
            "zones": [
                {"id": "gate_a", "name": "Gate A - North Entrance", "location": "North side", "type": "gate", "density_percent": 5},
                {"id": "gate_c", "name": "Gate C - South Entrance", "location": "South side", "type": "gate", "density_percent": 8},
                {"id": "concourse_north", "name": "North Concourse", "location": "Level 1, North", "type": "concourse", "density_percent": 15},
                {"id": "concourse_general", "name": "General Concourse", "location": "Level 1, Center", "type": "concourse", "density_percent": 100},
                {"id": "section_upper_west", "name": "Upper Deck - West", "location": "Level 3, West", "type": "seating", "density_percent": 99},
                {"id": "section_mezzanine_east", "name": "Mezzanine - East", "location": "Level 2, East", "type": "seating", "density_percent": 98},
                {"id": "section_lower_north", "name": "Lower Bowl - North", "location": "Level 1, North", "type": "seating", "density_percent": 97},
                {"id": "food_east", "name": "East Concourse Diner", "location": "Level 2, East plaza section", "type": "food", "density_percent": 45},
                {"id": "food_north", "name": "North Plaza Food Court", "location": "Ground level, North concourse", "type": "food", "density_percent": 35},
            ]
        },
        "half_time": {
            "zones": [
                {"id": "gate_a", "name": "Gate A - North Entrance", "location": "North side", "type": "gate", "density_percent": 65},
                {"id": "gate_c", "name": "Gate C - South Entrance", "location": "South side", "type": "gate", "density_percent": 70},
                {"id": "concourse_north", "name": "North Concourse", "location": "Level 1, North", "type": "concourse", "density_percent": 85},
                {"id": "concourse_general", "name": "General Concourse", "location": "Level 1, Center", "type": "concourse", "density_percent": 90},
                {"id": "section_upper_west", "name": "Upper Deck - West", "location": "Level 3, West", "type": "seating", "density_percent": 40},
                {"id": "section_mezzanine_east", "name": "Mezzanine - East", "location": "Level 2, East", "type": "seating", "density_percent": 35},
                {"id": "section_lower_north", "name": "Lower Bowl - North", "location": "Level 1, North", "type": "seating", "density_percent": 30},
                {"id": "food_east", "name": "East Concourse Diner", "location": "Level 2, East plaza section", "type": "food", "density_percent": 90},
                {"id": "food_north", "name": "North Plaza Food Court", "location": "Ground level, North concourse", "type": "food", "density_percent": 85},
            ]
        },
        "post_match": {
            "zones": [
                {"id": "gate_a", "name": "Gate A - North Entrance", "location": "North side", "type": "gate", "density_percent": 95},
                {"id": "gate_c", "name": "Gate C - South Entrance", "location": "South side", "type": "gate", "density_percent": 92},
                {"id": "concourse_north", "name": "North Concourse", "location": "Level 1, North", "type": "concourse", "density_percent": 88},
                {"id": "concourse_general", "name": "General Concourse", "location": "Level 1, Center", "type": "concourse", "density_percent": 85},
                {"id": "section_upper_west", "name": "Upper Deck - West", "location": "Level 3, West", "type": "seating", "density_percent": 10},
                {"id": "section_mezzanine_east", "name": "Mezzanine - East", "location": "Level 2, East", "type": "seating", "density_percent": 8},
                {"id": "section_lower_north", "name": "Lower Bowl - North", "location": "Level 1, North", "type": "seating", "density_percent": 5},
                {"id": "food_east", "name": "East Concourse Diner", "location": "Level 2, East plaza section", "type": "food", "density_percent": 20},
                {"id": "food_north", "name": "North Plaza Food Court", "location": "Ground level, North concourse", "type": "food", "density_percent": 15},
            ]
        }
    }
    
    # Return the correct phase data
    return {"phase": phase, "zones": base_data.get(phase, base_data["during_match"])["zones"]}

@router.get("/{venue_id}")
@router.get("/crowd/{venue_id}")
async def get_crowd(venue_id: str, phase: str = "during_match"):
    """
    Get crowd density snapshot for a venue.
    Returns clean JSON: {"phase": str, "zones": [...]}
    Each zone: {"id", "name", "location", "type", "density_percent"}
    """
    try:
        snapshot = get_crowd_snapshot(venue_id, phase)
        return snapshot
    except Exception as e:
        print(f"Error getting crowd snapshot: {e}")
        return {"phase": phase, "zones": [], "error": str(e)}

@router.post("/predict", response_model=PredictResponse)
async def predict_crowd_recommendation(payload: PredictRequest):
    """
    POST /api/crowd/predict
    Given a target venue, current phase, and user operations query,
    retrieves simulated crowd state and prompts Gemini for recommendation.
    """
    # 1. Fetch current density snapshot
    snapshot = get_crowd_snapshot(payload.venue_id, payload.current_phase)
    
    # Translate flat snapshot structure to format expected by response formatter
    density_data = {
        "zones": [
            {
                "name": zone["name"],
                "location": zone["location"],
                "density_percent": zone["density_percent"]
            }
            for zone in snapshot.get("zones", [])
        ]
    }
    
    # 2. Formulate prompts
    system_prompt = (
        "You are a stadium crowd management expert.\n"
        "Analyze this crowd density snapshot and answer the query.\n"
        "Be direct and actionable. 2-3 short sentences max.\n"
        "NO markdown, NO headers, NO bullets. Plain text only."
    )
    
    user_prompt = (
        f"Given this crowd density data: {json.dumps(density_data)}\n"
        f"Query: {payload.query}\n"
        "Identify what areas fans should avoid, and suggest structural alternatives."
    )
    
    try:
        from ai_service.response_formatter import format_crowd_response, strip_markdown
        
        # Call Gemini Text
        ai_response = await ask_gemini(user_prompt, system_prompt=system_prompt, output_format="clean_text")
        ai_response = strip_markdown(ai_response)
        
        formatted = format_crowd_response(density_data, ai_response)
        formatted["recommendation"] = formatted["summary"]  # Compatibility field
        
        return formatted
    except Exception as e:
        logger.error(f"Gemini call failed inside crowd predict: {e}")
        
        # Build logical emergency fallback recommendation based on snapshot data
        congested_zones = [zone["name"] for zone in snapshot.get("zones", []) if zone["density_percent"] >= 80]
        summary = "No critical congestion hotspots above 80% density identified."
        recommendations = ["General flow is normal. Standard operation protocols apply."]
        
        if congested_zones:
            congested_str = ", ".join(congested_zones)
            summary = f"Highly heavy congestion detected at: {congested_str}."
            recommendations = ["Redistribute operators to hotspots", "Open secondary gates"]
            
        formatted = {
            "zones": [
                {
                    "name": zone["name"],
                    "location": zone["location"],
                    "density_percent": zone["density_percent"],
                    "status": "critical" if zone["density_percent"] > 80 else "high" if zone["density_percent"] > 60 else "moderate"
                }
                for zone in snapshot.get("zones", [])
            ],
            "summary": summary,
            "recommendations": recommendations
        }
        formatted["recommendation"] = formatted["summary"]
        return formatted
