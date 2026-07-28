import asyncio
import sys
from pathlib import Path

# Add project root to sys.path so we can import ai_service
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from ai_service.rate_guard import (
    calls_this_minute,
    add_to_rate_guard_cache,
    find_cached_response,
    check_rate_limit,
    BUSY_MESSAGES
)

async def test_rate_guard():
    print("=== Testing RateGuard Functionality ===")
    
    # 1. Test Cache Insertion and Fuzzy Keyword Retrieval
    print("\n1. Testing Cache & Fuzzy Match...")
    venue_id = "venue-sofi"
    message = "Where can I find wheelchair-accessible toilets?"
    reply = "Wheelchair toilets are situated near section 120."
    
    add_to_rate_guard_cache(venue_id, message, reply)
    print("[SUCCESS] Added response to cache.")
    
    # Matching query containing similar words
    matching_query = "accessible toilets please"
    cached_hit = find_cached_response(venue_id, matching_query)
    print(f"Query: '{matching_query}' | Cached Hit: '{cached_hit}'")
    assert cached_hit == reply, f"Expected cache match, got: {cached_hit}"
    
    # Non-matching query (different keywords)
    non_matching = "Wi-Fi password"
    cached_miss = find_cached_response(venue_id, non_matching)
    print(f"Query: '{non_matching}' | Cached Hit: '{cached_miss}'")
    assert cached_miss is None, "Expected cache miss."
    
    # 2. Testing Rate Limit Threshold Triggers
    print("\n2. Testing Rate Limit In-Memory Multi-Call Counter...")
    import ai_service.rate_guard as rg
    
    # Reset count manually for clean simulation
    rg.calls_this_minute = 0
    
    # Make 7 calls (should allow them, returning None)
    for i in range(1, 8):
        res = check_rate_limit("Tell me about parking.", "venue-sofi")
        print(f"Call {i} Check → {res}")
        assert res is None, f"Expected None on call {i}"
        
    # Call number 8 (must trigger rate limit since calls_this_minute >= 8)
    res_8 = check_rate_limit("Where is Gate 1?", "venue-sofi")
    print(f"Call 8 Check (Rate Limit Active) → '{res_8}'")
    
    # Since "Gate 1" (word "gate") matches no cache, it should return a "busy" message in English
    assert res_8 == BUSY_MESSAGES["en"], f"Expected busy message, got: {res_8}"
    
    # Call number 9 with matching keyword (should trigger cache hit fallback instead of busy message!)
    res_9 = check_rate_limit("accessible toilets info", "venue-sofi")
    print(f"Call 9 Check (Similar Query Cached Fallback) → '{res_9}'")
    assert res_9 == reply, f"Expected cached replay fallback, got: {res_9}"
    
    # 3. Testing Language-Specific Busy Messages
    print("\n3. Testing Localized Limit Exceptions...")
    rg.calls_this_minute = 10 # force limit
    
    spanish_query = "¿Dónde obtener ayuda?"
    french_query = "Où est le taxi s'il vous plaît?"
    chinese_query = "谢谢，怎么去二楼？"
    
    res_es = check_rate_limit(spanish_query, "venue-sofi")
    res_fr = check_rate_limit(french_query, "venue-sofi")
    res_zh = check_rate_limit(chinese_query, "venue-sofi")
    
    print(f"Spanish trigger -> '{res_es}'")
    print(f"French trigger -> '{res_fr}'")
    print(f"Chinese trigger -> '{res_zh}'")
    
    assert res_es == BUSY_MESSAGES["es"]
    assert res_fr == BUSY_MESSAGES["fr"]
    assert res_zh == BUSY_MESSAGES["zh"]
    
    print("\n=== ALL RateGuard UNIT TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(test_rate_guard())
