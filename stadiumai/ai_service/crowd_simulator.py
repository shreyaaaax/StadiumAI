from typing import Dict, Any
from .rag_loader import VENUES_CACHE

def get_crowd_snapshot(venue_id: str, match_phase: str) -> Dict[str, int]:
    """
    Simulates crowd density per gate, section, food court, and general areas 
    for a given venue and match phase.
    
    Phases: 'pre_match', 'during_match', 'half_time', 'post_match'
    Returns a dictionary mapping zone names/IDs to their density percentile (0-100).
    """
    # Resilient key lookup for stadium IDs (e.g. mapping "metlife" to "venue-metlife")
    target_id = venue_id
    if target_id not in VENUES_CACHE:
        for key in VENUES_CACHE.keys():
            if target_id.lower() in key.lower() or key.lower() in target_id.lower():
                target_id = key
                break
                
    venue = VENUES_CACHE.get(target_id)
    if not venue:
        # Fallback structural map if ID is not resolved
        venue = {
            "name": "Generic Stadium",
            "gates": [{"name": "Gate A"}, {"name": "Gate B"}, {"name": "Gate C"}, {"name": "Gate D"}],
            "sections": [{"name": "Lower Tier"}, {"name": "Middle Tier"}, {"name": "Upper Tier"}],
            "facilities": {"food_courts": ["Main Food Court", "Sub Food Court"]}
        }
        
    snapshot = {}
    phase = match_phase.lower().strip()
    
    # Extract structural zones of the venue JSON
    gates_list = [g.get("name") if isinstance(g, dict) else g for g in venue.get("gates", [])]
    sections_list = [s.get("name") if isinstance(s, dict) else s for s in venue.get("sections", [])]
    
    facilities = venue.get("facilities", {})
    food_courts_list = []
    if isinstance(facilities, dict):
        food_courts_list = facilities.get("food_courts", [])

    # Deterministic simulation rates based on the state constraints
    if phase == "pre_match":
        # gates: 70-90% full, concourse: 60%, sections: 30%, food courts: 40%
        for idx, gate in enumerate(gates_list):
            snapshot[f"Gate: {gate}"] = 70 + (idx * 7) % 21  # 70-90%
        snapshot["General Concourse"] = 60
        for idx, fc in enumerate(food_courts_list):
            snapshot[f"Food Court: {fc}"] = 40 + (idx * 5) % 15
        for idx, sec in enumerate(sections_list):
            snapshot[f"Section: {sec}"] = 25 + (idx * 3) % 10
            
    elif phase == "during_match":
        # gates: 10%, concourse: 20%, sections: 95%, food courts: 15%
        for idx, gate in enumerate(gates_list):
            snapshot[f"Gate: {gate}"] = 10 + (idx * 2) % 5
        snapshot["General Concourse"] = 20
        for idx, fc in enumerate(food_courts_list):
            snapshot[f"Food Court: {fc}"] = 15 + (idx * 3) % 15
        for idx, sec in enumerate(sections_list):
            snapshot[f"Section: {sec}"] = 95 + (idx * 1) % 5  # 95-99%
            
    elif phase == "half_time":
        # concourse: 80%, food courts: 90%, gates: 15%, sections: 40%
        for idx, gate in enumerate(gates_list):
            snapshot[f"Gate: {gate}"] = 15 + (idx * 2) % 5
        snapshot["General Concourse"] = 80
        for idx, fc in enumerate(food_courts_list):
            snapshot[f"Food Court: {fc}"] = 90 + (idx * 2) % 9   # 90-98%
        for idx, sec in enumerate(sections_list):
            snapshot[f"Section: {sec}"] = 40 + (idx * 6) % 15
            
    elif phase == "post_match":
        # gates: 85-100%, concourse: 90%, sections: 10%, food courts: 20%
        for idx, gate in enumerate(gates_list):
            snapshot[f"Gate: {gate}"] = 85 + (idx * 5) % 16  # 85-100%
        snapshot["General Concourse"] = 90
        for idx, fc in enumerate(food_courts_list):
            snapshot[f"Food Court: {fc}"] = 20 + (idx * 4) % 15
        for idx, sec in enumerate(sections_list):
            snapshot[f"Section: {sec}"] = 10 + (idx * 2) % 8
            
    else:
        # Default snapshot stats fallback
        for idx, gate in enumerate(gates_list):
            snapshot[f"Gate: {gate}"] = 30
        snapshot["General Concourse"] = 35
        for idx, fc in enumerate(food_courts_list):
            snapshot[f"Food Court: {fc}"] = 25
        for idx, sec in enumerate(sections_list):
            snapshot[f"Section: {sec}"] = 40
            
    return snapshot

# CLI self-test execution
if __name__ == "__main__":
    print("Pre-match snapshot for venue-sofi:")
    print(get_crowd_snapshot("venue-sofi", "pre_match"))
    print("\nHalf-time snapshot for venue-sofi:")
    print(get_crowd_snapshot("venue-sofi", "half_time"))
