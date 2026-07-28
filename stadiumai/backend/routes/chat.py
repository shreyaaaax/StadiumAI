import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

# Setup router logging
logger = logging.getLogger(__name__)

# Step 4.1: Import get_venue_context from ai_service.rag_loader and detect_language from ai_service.detect_language
from ai_service.rag_loader import get_venue_context
from ai_service.detect_language import detect_language
from ai_service import ask_gemini

router = APIRouter(tags=["Chat"])

# Language name lookup mapping
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "zh": "Chinese (Simplified)"
}

# Error fallback message catalog
FALLBACK_MESSAGES = {
    "en": "Sorry, I am having trouble connecting to the AI service right now. Please try again soon.",
    "es": "Lo siento, tengo dificultades para conectarme con el servicio de IA en este momento. Por favor, inténtelo de nuevo pronto.",
    "fr": "Désolé, j'ai des difficultés à me connecter au service d'IA pour le moment. Veuillez réessayer bientôt.",
    "zh": "抱歉，我目前连接 AI 服务时遇到问题。请稍后再试。"
}

class ChatRequest(BaseModel):
    message: str
    venue_id: Optional[str] = None
    language: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    language: str
    venue_id: str

# Step 4.2: Keyword extraction function supporting multilingual queries
def extract_keywords(message: str) -> list:
    """
    Checks for keyword groups in English, Spanish, French, and Chinese,
    returning standard English category names as keys: gate, food, restroom, transport, emergency.
    """
    message_lower = message.lower().strip()
    matched = []
    
    # Gate keywords
    if any(kw in message_lower for kw in ["gate", "entrance", "enter", "door", "puerta", "entrada", "acceso", "ingresar", "porte", "entree", "entrer", "门", "入口", "进"]):
        matched.append("gate")
        
    # Food keywords
    if any(kw in message_lower for kw in ["food", "eat", "restaurant", "hungry", "cafe", "snack", "comida", "comer", "restaurante", "hambre", "cafeteria", "nourrit", "manger", "faim", "吃", "饭", "餐厅", "饿", "咖啡", "小吃", "食品"]):
        matched.append("food")
        
    # Restrooms
    if any(kw in message_lower for kw in ["restroom", "toilet", "bathroom", "wc", "baño", "servicio", "sanitario", "aseo", "toile", "bain", "cabinet", "厕", "洗手间", "卫生间", "化妆室"]):
        matched.append("restroom")
        
    # Transport
    if any(kw in message_lower for kw in ["transport", "bus", "metro", "train", "taxi", "ride", "transporte", "autobus", "metro", "tren", "taxi", "viaje", "trajet", "交", "车", "地铁", "火车", "的士", "出租车", "乘"]):
        matched.append("transport")
        
    # Emergency
    if any(kw in message_lower for kw in ["emergency", "help", "medical", "doctor", "exit", "emergencia", "ayuda", "medico", "doctor", "salida", "urgence", "aide", "medecin", "sortie", "急", "帮", "医", "医生", "出"]):
        matched.append("emergency")
        
    return matched if matched else ["general"]

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    POST /api/chat/ endpoint
    """
    # 1. Resolve venue_id and language
    venue_id = payload.venue_id or "metlife"
    
    lang = payload.language
    if not lang:
        lang = detect_language(payload.message)
    # Clamp language to supported list
    if lang not in FALLBACK_MESSAGES:
        lang = "en"

    # 2. Extract context keywords
    keywords = extract_keywords(payload.message)
    
    # 3. Get venue context from RAG loader
    context = get_venue_context(venue_id, query_keywords=keywords)
    
    # Debug print: Print target venue_id, extracted keywords, and length of returned context
    print(f"[CHAT DEBUG] Venue: '{venue_id}', Keywords: {keywords}, Context Length: {len(context)}")
    
    # 4. Translate language code to full language name
    lang_name = LANGUAGE_MAP.get(lang, "English")
    
    # 5. Formulate system instructions block
    system_prompt = (
        "You are StadiumAI, a helpful FIFA World Cup 2026 stadium assistant.\n"
        f"ALWAYS respond in {lang_name}.\n"
        "You must answer ONLY using the VENUE DATA block provided below. Do not use external or outside knowledge.\n"
        "Keep answers to a maximum of 3 sentences.\n"
        "If the specific fact truly isn't present in the provided venue data, say so honestly (do not say the venue itself is missing, since the venue database is loaded).\n\n"
        f"VENUE DATA:\n{context}"
    )
    
    try:
        from ai_service.response_formatter import strip_markdown
        reply = await ask_gemini(payload.message, system_prompt=system_prompt, output_format="clean_text")
        reply = strip_markdown(reply)
        return ChatResponse(
            reply=reply,
            language=lang,
            venue_id=venue_id
        )
    except Exception as e:
        logger.error(f"Failed to query Gemini client from chat endpoint: {e}")
        fallback = FALLBACK_MESSAGES.get(lang, FALLBACK_MESSAGES["en"])
        return ChatResponse(
            reply=fallback,
            language=lang,
            venue_id=venue_id
        )
