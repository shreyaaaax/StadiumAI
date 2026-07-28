import re
import datetime
import logging
from typing import Literal, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

# Import Gemini and RAG interfaces
from ai_service import ask_gemini, get_venue_context
from ai_service.rag_loader import VENUES_CACHE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Staff"])

class StaffQueryRequest(BaseModel):
    question: str
    role: Literal["volunteer", "security", "medic", "supervisor"]
    venue_id: str

class StaffQueryResponse(BaseModel):
    answer: str
    confidence: Optional[str] = "high"
    escalation_needed: Optional[bool] = False

class IncidentReportRequest(BaseModel):
    description: str
    location: str
    severity: int = Field(..., ge=1, le=5)
    venue_id: Optional[str] = None

class IncidentReportResponse(BaseModel):
    report_text: str

def extract_keywords(message: str) -> list:
    """
    Extracts alphanumeric tokens in lowercase from the user message.
    """
    return re.findall(r'\b\w+\b', message.lower())

@router.post("/query", response_model=StaffQueryResponse)
async def staff_query_endpoint(payload: StaffQueryRequest):
    """
    POST /staff/query
    
    1. Resolve the venue_id resiliently
    2. Extract keywords and query RAG context
    3. Generate response using Gemini with specific staff copilot prompt
    """
    target_id = payload.venue_id
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    venue = VENUES_CACHE.get(target_id)
    venue_name = venue.get("name", "Unknown Venue") if venue else "Unknown Venue"
    
    keywords = extract_keywords(payload.question)
    context = get_venue_context(target_id, query_keywords=keywords)
    
    system_prompt = f"""You are a stadium operations assistant for a {payload.role}.
Answer this question clearly and actionably in English.
Max 3 sentences. Suggest escalation if needed.
NO markdown, NO headers, NO bullets. Just plain text.

Venue info: {context}"""
    
    try:
        from ai_service.response_formatter import format_staff_response, strip_markdown
        
        reply = await ask_gemini(payload.question, system_prompt=system_prompt, output_format="clean_text")
        reply = strip_markdown(reply)
        
        formatted = format_staff_response("copilot", reply)
        return formatted
    except Exception as e:
        logger.error(f"Failed to query Gemini in staff_query_endpoint: {e}")
        # Default fallback response
        fallback_msg = (
            "Apologies, I am having trouble connecting to the AI service. "
            "If this is an emergency, please contact Security Control: ext 100 or Medical: ext 200 immediately."
        )
        return StaffQueryResponse(answer=fallback_msg, confidence="low", escalation_needed=True)

@router.post("/incident_report", response_model=IncidentReportResponse)
async def staff_incident_report_endpoint(payload: IncidentReportRequest):
    """
    POST /staff/incident_report
    
    Generate formal draft of incident report for staff copy-pasting.
    """
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    system_prompt = (
        "You are StadiumAI Staff Copilot for FIFA World Cup 2026.\n"
        "Your task is to auto-draft a formal incident report based on the provided details.\n"
        "The report must adhere to the following format exactly:\n"
        f"Date/Time: {current_time_str}\n" 
        f"Location: {payload.location}\n"
        f"Severity: {payload.severity}/5\n"
        f"Description: {payload.description}\n"
        "Recommended Action: [Provide a professional, clear recommendation for this type of incident]\n\n"
        "Only output the drafted card content. Keep it elegant, clear, and practical."
    )
    
    user_prompt = f"Draft an incident report. Location: {payload.location}, Severity: {payload.severity}, Description: {payload.description}"
    
    try:
        reply = await ask_gemini(user_prompt, system_prompt=system_prompt)
        return IncidentReportResponse(report_text=reply.strip())
    except Exception as e:
        logger.error(f"Failed to generate incident report: {e}")
        # Fallback generated text
        rec_action = "Investigate the location immediately and notify the supervisor."
        if payload.severity >= 4:
            rec_action = "Deploy team to the location immediately and notify Security Control at ext 100."
        elif payload.severity >= 3:
            rec_action = "Investigate the location and check for any safety hazards. Inform cleaning/maintenance/crowd managers."
            
        fallback_report = (
            f"Date/Time: {current_time_str}\n"
            f"Location: {payload.location}\n"
            f"Severity: {payload.severity}/5\n"
            f"Description: {payload.description}\n"
            f"Recommended Action: {rec_action}"
        )
        return IncidentReportResponse(report_text=fallback_report)
