import re
import asyncio
import logging
import hashlib
import functools
from typing import Optional, List, Dict, Set, Callable, Any

from ai_service.detect_language import detect_language

logger = logging.getLogger(__name__)

# Fallback messages per language
BUSY_MESSAGES = {
    "en": "Our AI assistant is busy. Please try in a moment or visit the info desk.",
    "es": "Nuestro asistente está ocupado. Por favor intente en un momento.",
    "fr": "Notre assistant est occupé. Veuillez réessayer dans un moment.",
    "zh": "我们的助手正忙。请稍后再试。"
}

# --- Rate Limitation State ---
calls_this_minute = 0
_reset_task = None

# --- Cache State ---
# In-memory backing store for LRU cache
_cache_store: Dict[str, str] = {}

# Metadata registry to track venue_id and keywords for fuzzy matching
# Entries: {"venue_id": str, "keywords": Set[str], "prompt_hash": str}
_cache_metadata: List[Dict[str, Any]] = []

@functools.lru_cache(maxsize=20)
def get_cached_response_by_hash(prompt_hash: str) -> str:
    """
    Standard LRU cache retrieving response content based on unique prompt hash.
    Directly backed by _cache_store dictionary.
    """
    return _cache_store.get(prompt_hash, "")

# Common stop words to exclude from keyword index matching
STOP_WORDS = {"where", "what", "when", "from", "with", "find", "have", "please", "about", "your", "this", "that", "there", "here", "near", "want", "show", "tell", "need", "info"}

def add_to_rate_guard_cache(venue_id: str, message: str, response: str):
    """
    Saves a resolved response to the LRU cache.
    """
    global _cache_metadata, _cache_store
    
    # Compute unique MD5 representation of the prompt
    key_str = f"{venue_id.lower().strip()}:{message.lower().strip()}"
    prompt_hash = hashlib.md5(key_str.encode("utf-8")).hexdigest()
    
    # Save to backing store and load into lru_cache
    _cache_store[prompt_hash] = response
    get_cached_response_by_hash(prompt_hash)
    
    # Tokenize message to extract keywords, filtering against stop words
    words = {w for w in re.findall(r"\b\w{4,}\b", message.lower()) if w not in STOP_WORDS}
    
    # Filter out entries matching this hash to prevent duplicates
    _cache_metadata = [m for m in _cache_metadata if m["prompt_hash"] != prompt_hash]
    
    # Append new entry metadata
    _cache_metadata.append({
        "venue_id": venue_id.lower().strip(),
        "keywords": words,
        "prompt_hash": prompt_hash
    })
    
    # Enforce cache capacity cap of 20 elements
    if len(_cache_metadata) > 20:
        removed = _cache_metadata.pop(0)
        _cache_store.pop(removed["prompt_hash"], None)
        
        # Reset and repopulate lru_cache references
        get_cached_response_by_hash.cache_clear()
        for meta in _cache_metadata:
            get_cached_response_by_hash(meta["prompt_hash"])

def find_cached_response(venue_id: str, message: str) -> Optional[str]:
    """
    Fuzzy registry lookup. Checks if the requested venue_id and message keywords
    match a stored record, and returns the response from the LRU cache if found.
    """
    v_id = venue_id.lower().strip()
    words = {w for w in re.findall(r"\b\w{4,}\b", message.lower()) if w not in STOP_WORDS}
    
    # Traverse from most recent to oldest
    for meta in reversed(_cache_metadata):
        if meta["venue_id"] == v_id:
            # Match if both sets are empty, or if they share keywords
            if (not words and not meta["keywords"]) or (words & meta["keywords"]):
                prompt_hash = meta["prompt_hash"]
                cached_res = get_cached_response_by_hash(prompt_hash)
                if cached_res:
                    logger.info(f"RateGuard: Cache hit for venue: {venue_id} / similar words: {words}")
                    return cached_res
    return None

async def _reset_counter_loop():
    """
    Asynchronous loop that resets the rate limit counter every 60 seconds.
    """
    global calls_this_minute
    while True:
        await asyncio.sleep(60)
        calls_this_minute = 0
        logger.debug("RateGuard: reset call count to 0")

def start_reset_timer():
    """
    Hooks a background reset loop into the active asyncio event loop.
    Safe to trigger multiple times: configures the task only once.
    """
    global _reset_task
    if _reset_task is None:
        try:
            loop = asyncio.get_running_loop()
            _reset_task = loop.create_task(_reset_counter_loop())
            logger.info("RateGuard: reset loop started successfully.")
        except RuntimeError:
            # Ignored during tests or compilation if no loop is initialized
            pass

def check_rate_limit(prompt: str, system_prompt: str) -> Optional[str]:
    """
    Enforces the rate limit check.
    If the rate threshold (8 calls/min) has been exceeded, returns:
    1. A fuzzy cached response matching the query context if available.
    2. A polite language-specific "busy" message as secondary fallback.
    
    If the rate limit is not exceeded, returns None.
    """
    global calls_this_minute
    
    # Start loop timer
    start_reset_timer()
    
    # Increment counter
    calls_this_minute += 1
    
    if calls_this_minute >= 8:
        logger.warning(f"RateGuard limit hit! Threshold: 8/min. Current check: {calls_this_minute} calls.")
        
        # 1. Parsing venue association
        venue_match = re.search(r"\b(venue-\w+)\b", system_prompt + " " + prompt, re.IGNORECASE)
        venue_id = venue_match.group(1).lower() if venue_match else "general"
        
        # 2. Attempt fuzzy cache retrieval
        cached = find_cached_response(venue_id, prompt)
        if cached:
            return cached
            
        # 3. Fallback to busy message
        lang = detect_language(prompt)
        busy_msg = BUSY_MESSAGES.get(lang, BUSY_MESSAGES["en"])
        return busy_msg
        
    return None
