from typing import Dict, Any

def get_sustainability_metrics(venue_id: str, phase: str = "during") -> Dict[str, Any]:
    """
    Returns mock sustainability metrics for a given venue and match phase.
    Phases: 'pre', 'during', 'post'
    
    Returned format:
    {
        "energy_kwh": int,
        "waste_kg": int,
        "recycled_pct": int,
        "water_liters": int,
        "carbon_kg": int,
        "vs_last_match": {
            "energy_change_pct": int,
            "waste_change_pct": int
        }
    }
    """
    p = phase.lower().strip()
    if p not in ("pre", "during", "post"):
        p = "during"
        
    v_id = venue_id.lower().replace("venue-", "")
    
    # Base values scaled by generic capacity groups
    if v_id in ("metlife", "azteca", "sofi"):
        base_energy = 9000
        base_waste = 1500
        base_water = 50000
        recycled_pct = 68
    else:
        base_energy = 5500
        base_waste = 900
        base_water = 32000
        recycled_pct = 58
        
    # Scale metrics by match phase
    if p == "pre":
        energy_kwh = int(base_energy * 0.75)
        waste_kg = int(base_waste * 0.25)
        water_liters = int(base_water * 0.45)
        recycled_pct = int(recycled_pct * 0.9)
    elif p == "during":
        energy_kwh = int(base_energy * 1.45)
        waste_kg = int(base_waste * 0.85)
        water_liters = int(base_water * 1.55)
        recycled_pct = int(recycled_pct * 1.05)
    else:  # post
        energy_kwh = int(base_energy * 0.35)
        waste_kg = int(base_waste * 1.4)
        water_liters = int(base_water * 0.35)
        recycled_pct = int(recycled_pct * 1.15)
        
    # Cap recycling percentage at 98%
    recycled_pct = min(recycled_pct, 98)
    
    # Carbon footprint translation
    carbon_kg = int(energy_kwh * 0.41 + waste_kg * 0.78)
    
    # Compare with last match mock metrics
    if v_id == "metlife":
        energy_change_pct = -6
        waste_change_pct = -11
    elif v_id == "azteca":
        energy_change_pct = 4
        waste_change_pct = -2
    elif v_id == "sofi":
        energy_change_pct = -10
        waste_change_pct = -15
    else:
        energy_change_pct = -2
        waste_change_pct = 4
        
    return {
        "energy_kwh": energy_kwh,
        "waste_kg": waste_kg,
        "recycled_pct": recycled_pct,
        "water_liters": water_liters,
        "carbon_kg": carbon_kg,
        "vs_last_match": {
            "energy_change_pct": energy_change_pct,
            "waste_change_pct": waste_change_pct
        }
    }

def calculate_eco_score(metrics: Dict[str, Any]) -> int:
    """
    Calculates a simple eco score from 0 to 100 based on recycling rate
    and percentage change from the previous match (lower consumption/waste is better).
    """
    recycled = metrics["recycled_pct"]
    energy_change = metrics["vs_last_match"]["energy_change_pct"]
    waste_change = metrics["vs_last_match"]["waste_change_pct"]
    
    score = recycled
    score -= int(energy_change * 0.5)
    score -= int(waste_change * 0.5)
    
    return max(min(score, 100), 1)
