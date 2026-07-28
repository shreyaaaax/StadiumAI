import re

def detect_language(text: str) -> str:
    """
    Detects the language of a given text string.
    Returns: 'en', 'es', 'fr', or 'zh'.
    
    Strategy:
    1. Check for Chinese Unicode characters (\u4e00-\u9fff) -> 'zh'
    2. Check for Spanish marker words -> 'es'
    3. Check for French marker words -> 'fr'
    4. Default -> 'en'
    """
    if not text:
        return "en"

    # 1. Chinese characters detection
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"

    # Normalize text for easy matching
    normalized = text.lower()

    # 2. Spanish markers
    spanish_markers = ["dónde", "cómo", "qué", "gracias", "por favor"]
    for marker in spanish_markers:
        # Match as word boundaries to prevent false positives, but allow some variations
        if re.search(rf"\b{re.escape(marker)}\b", normalized):
            return "es"

    # 3. French markers
    french_markers = ["où", "comment", "qu", "merci", "s'il vous"]
    for marker in french_markers:
        # Match as word boundaries, but for 'qu' allow 'qu'' suffix
        if marker == "qu":
            if re.search(r"\bqu['\s]", normalized):
                return "fr"
        else:
            if re.search(rf"\b{re.escape(marker)}\b", normalized):
                return "fr"

    return "en"

if __name__ == "__main__":
    # Internal validation test
    tests = {
        "Where is the nearest exit?": "en",
        "¿Dónde está la puerta principal?": "es",
        "Où se trouve la sortie de secours s'il vous plaît?": "fr",
        "谢谢，请问洗手间在哪里？": "zh"
    }
    
    print("--- Executing Internal detect_language Tests ---")
    for phrase, expected in tests.items():
        detected = detect_language(phrase)
        status = "PASSED" if detected == expected else "FAILED"
        print(f"[{status}] Phrase: '{phrase}' | Expected: {expected} | Detected: {detected}")
