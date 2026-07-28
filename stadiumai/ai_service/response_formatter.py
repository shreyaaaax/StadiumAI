import json
import re

def strip_markdown(text: str) -> str:
    """Remove all markdown formatting from text."""
    # Remove headers (###, ##, #)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Remove italics (*text* and _text_)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove bullet points and numbered lists
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove code blocks (```...```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove horizontal rules
    text = re.sub(r'^[\-\*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_json_from_response(text: str) -> dict:
    """Try to extract JSON object from a response that might have markdown around it."""
    # Look for JSON object pattern {...}
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None

def format_crowd_response(density_data: dict, ai_analysis: str) -> dict:
    """Format crowd intelligence response as clean JSON."""
    # Strip markdown from AI analysis
    clean_analysis = strip_markdown(ai_analysis)
    
    return {
        "zones": [
            {
                "name": zone.get("name"),
                "location": zone.get("location"),
                "density_percent": zone.get("density_percent"),
                "status": "critical" if zone.get("density_percent", 0) > 80 else "high" if zone.get("density_percent", 0) > 60 else "moderate"
            }
            for zone in density_data.get("zones", [])
        ],
        "summary": clean_analysis[:200],  # First 200 chars only, no markdown
        "recommendations": [
            line.strip() for line in clean_analysis.split('\n') 
            if line.strip() and len(line.strip()) > 10
        ][:3]  # Top 3 recommendations only
    }

def format_navigation_response(steps: list, ai_analysis: str) -> dict:
    """Format navigation response as clean JSON."""
    clean_analysis = strip_markdown(ai_analysis)
    
    return {
        "steps": steps,
        "summary": clean_analysis[:150],
        "accessible": True if "accessible" in clean_analysis.lower() else False,
        "estimated_minutes": extract_estimated_time(clean_analysis)
    }

def format_transport_response(recommendation: str) -> dict:
    """Format transport response as clean JSON."""
    clean_text = strip_markdown(recommendation)
    
    # Extract departure time if mentioned
    departure_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', clean_text)
    departure_time = f"{departure_match.group(1)}:{departure_match.group(2)} {departure_match.group(3)}" if departure_match else None
    
    return {
        "recommendation": clean_text[:200],
        "suggested_departure": departure_time,
        "options": extract_options(clean_text)
    }

def format_staff_response(response_type: str, content: str) -> dict:
    """Format staff endpoint responses."""
    clean_content = strip_markdown(content)
    
    if response_type == "copilot":
        return {
            "answer": clean_content,
            "confidence": "high" if len(clean_content) > 50 else "medium",
            "escalation_needed": "URGENT" in clean_content.upper()
        }
    elif response_type == "incident":
        return {
            "report": clean_content,
            "severity": extract_severity(clean_content),
            "ready_to_submit": True
        }
    elif response_type == "sustainability":
        return {
            "analysis": clean_content,
            "actionable_items": extract_bullets(clean_content)[:3]
        }

def extract_estimated_time(text: str) -> int:
    """Extract estimated time in minutes from text."""
    match = re.search(r'(\d+)\s*(min|minute)', text)
    return int(match.group(1)) if match else 0

def extract_options(text: str) -> list:
    """Extract bullet-pointed options from text."""
    lines = text.split('\n')
    options = []
    for line in lines:
        # Look for lines that look like options
        if line.strip() and len(line.strip()) > 10 and len(line.strip()) < 100:
            options.append(line.strip())
    return options[:5]  # Max 5 options

def extract_bullets(text: str) -> list:
    """Extract action items from text."""
    lines = text.split('\n')
    items = []
    for line in lines:
        clean = line.strip().lstrip('*-+ ').strip()
        if clean and len(clean) > 10 and len(clean) < 150:
            items.append(clean)
    return items

def extract_severity(text: str) -> str:
    """Extract severity level from incident report."""
    text_upper = text.upper()
    if any(word in text_upper for word in ['CRITICAL', 'SEVERE', 'EMERGENCY', 'URGENT']):
        return "critical"
    elif any(word in text_upper for word in ['HIGH', 'SERIOUS', 'SIGNIFICANT']):
        return "high"
    elif any(word in text_upper for word in ['MODERATE', 'MEDIUM']):
        return "medium"
    else:
        return "low"
