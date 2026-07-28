import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

# Import Gemini and RAG interfaces
from ai_service import ask_gemini, get_sustainability_metrics, calculate_eco_score
from ai_service.rag_loader import VENUES_CACHE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sustainability"])

class SustainabilityMetricsResponse(BaseModel):
    venue_id: str
    phase: str
    energy_kwh: int
    waste_kg: int
    recycled_pct: int
    water_liters: int
    carbon_kg: int
    vs_last_match: Dict[str, int]
    eco_score: int

class SustainabilityInsightRequest(BaseModel):
    venue_id: str
    question: str
    phase: Optional[str] = "during"

class SustainabilityInsightResponse(BaseModel):
    insight: str

class FanEcoScoreResponse(BaseModel):
    venue_id: str
    saved_co2_kg: int
    message: str

@router.get("/{venue_id}", response_model=SustainabilityMetricsResponse)
def get_sustainability_endpoint(venue_id: str, phase: str = "during"):
    """
    GET /sustainability/{venue_id}
    Returns mock sustainability data for a given venue and phase, including a calculated eco-score.
    """
    target_id = venue_id
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    metrics = get_sustainability_metrics(target_id, phase=phase)
    eco_score = calculate_eco_score(metrics)
    
    return SustainabilityMetricsResponse(
        venue_id=target_id,
        phase=phase,
        energy_kwh=metrics["energy_kwh"],
        waste_kg=metrics["waste_kg"],
        recycled_pct=metrics["recycled_pct"],
        water_liters=metrics["water_liters"],
        carbon_kg=metrics["carbon_kg"],
        vs_last_match=metrics["vs_last_match"],
        eco_score=eco_score
    )

@router.post("/insight", response_model=SustainabilityInsightResponse)
async def post_sustainability_insight(payload: SustainabilityInsightRequest):
    """
    POST /sustainability/insight
    Queries Gemini as a sustainability analyst using the current venue sustainability metrics.
    """
    target_id = payload.venue_id
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    metrics = get_sustainability_metrics(target_id, phase=payload.phase or "during")
    eco_score = calculate_eco_score(metrics)
    
    sustainability_data = {
        **metrics,
        "eco_score": eco_score
    }
    
    system_prompt = (
        "You are a sustainability analyst for FIFA World Cup 2026.\n"
        f"Current data: {sustainability_data}. Answer this ops question: {payload.question}\n"
        "Give 2-3 specific, actionable recommendations. Be data-driven."
    )
    
    try:
        reply = await ask_gemini(payload.question, system_prompt=system_prompt)
        return SustainabilityInsightResponse(insight=reply.strip())
    except Exception as e:
        logger.error(f"Failed to query Gemini in post_sustainability_insight: {e}")
        # Build a structured fallback insight based on the metrics
        waste_kg = metrics["waste_kg"]
        recycled_pct = metrics["recycled_pct"]
        energy_kwh = metrics["energy_kwh"]
        
        fallback_insight = (
            "[Sustainability Fallback Advice]\n"
            f"1. Optimize Energy Load: The current phase energy load is {energy_kwh} kWh. "
            "Reduce HVAC and lighting in unoccupied areas.\n"
            f"2. Maximize Recycling: With recycling at {recycled_pct}%, increase sorting bins "
            "near concession stands to process the remaining waste.\n"
            "3. Stakeholder Communication: Push zero-waste and energy-saving initiatives "
            "to fans via stadium display boards."
        )
        return SustainabilityInsightResponse(insight=fallback_insight)

@router.get("/{venue_id}/fan_score", response_model=FanEcoScoreResponse)
def get_fan_eco_score_endpoint(venue_id: str):
    """
    GET /sustainability/{venue_id}/fan_score
    Returns a motivational message for the fan-facing application outlining CO2 savings.
    """
    target_id = venue_id
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    metrics = get_sustainability_metrics(target_id, phase="during")
    
    # Calculate a mock saving of carbon based on recycling improvements
    energy_saved_pct = -metrics["vs_last_match"]["energy_change_pct"]
    waste_saved_pct = -metrics["vs_last_match"]["waste_change_pct"]
    
    saved_co2 = int(metrics["carbon_kg"] * (max(energy_saved_pct, 1) + max(waste_saved_pct, 1)) / 100.0)
    saved_co2 = max(saved_co2, 50)  # guarantee a nice positive number
    
    message = f"This match has saved {saved_co2} kg of CO2 vs average! Thank you for cleaning up and recycling at the venue!"
    
    return FanEcoScoreResponse(
        venue_id=target_id,
        saved_co2_kg=saved_co2,
        message=message
    )
