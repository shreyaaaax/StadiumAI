import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# 1. Use pathlib.Path(__file__).parent.parent / "data" to build an absolute path to the data folder
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Module-level dictionary cache
venue_cache: Dict[str, Any] = {}
VENUES_CACHE = venue_cache

def load_venues() -> Dict[str, Any]:
    """
    Finds all files matching "venue_*.json" in the data folder, parses them, 
    and caches them by their lowercase 'id' field value.
    """
    global venue_cache
    venue_cache.clear()
    
    if not DATA_DIR.exists():
        print(f"Error: Data directory does not exist at {DATA_DIR}")
        return venue_cache

    json_files = list(DATA_DIR.glob("venue_*.json"))
    if not json_files:
        print(f"Error: No venue files found in data folder at {DATA_DIR}")
        return venue_cache

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "id" in data:
                    venue_id = str(data["id"]).strip().lower()
                    venue_cache[venue_id] = data
                    print(f"Successfully loaded venue: {data.get('name')} (id: {venue_id})")
                else:
                    print(f"Error parse JSON file {file_path.name}: Root JSON is not a dictionary or lacks 'id'")
        except Exception as e:
            print(f"Error parsing JSON file {file_path.name}: {e}")

    return venue_cache

# 2. On import, automatically call load_venues()
load_venues()

def list_venues() -> List[Dict[str, Any]]:
    """
    Returns basic venue details. Inits cache if empty.
    """
    global venue_cache
    if not venue_cache:
        load_venues()
        
    return [
        {
            "id": venue.get("id"),
            "name": venue.get("name"),
            "city": venue.get("city")
        }
        for venue in venue_cache.values()
    ]

def get_venue_context(venue_id: str, query_keywords: Optional[List[str]] = None) -> str:
    """
    Standardizes lookups and extracts conditional context sections.
    """
    global venue_cache
    
    # Lowercase and strip target id
    target_id = str(venue_id).strip().lower()
    
    # If cache empty, load
    if not venue_cache:
        load_venues()
        
    if target_id not in venue_cache:
        # Warning listing keys
        available_keys = list(venue_cache.keys())
        print(f"Warning: Venue ID '{target_id}' not found. Available keys: {available_keys}")
        return f"Error: Venue with ID '{venue_id}' not found in database."

    venue = venue_cache[target_id]
    
    # Form base details
    name = venue.get("name", "Unknown Venue")
    city = venue.get("city", "Unknown City")
    capacity = venue.get("capacity", "Unknown Capacity")
    address = venue.get("address", "Unknown Address")
    
    sections = [
        f"Venue Name: {name}",
        f"City: {city}",
        f"Capacity: {capacity}",
        f"Address: {address}"
    ]

    # Keyword check
    keywords = [str(kw).strip().lower() for kw in (query_keywords or [])]

    # Keyword mappings
    include_gate = any(kw in keywords for kw in ["gate", "entrance", "enter", "door"])
    include_food = any(kw in keywords for kw in ["food", "eat", "restaurant", "hungry", "cafe", "snack"])
    include_restroom = any(kw in keywords for kw in ["restroom", "toilet", "bathroom", "wc"])
    include_transport = any(kw in keywords for kw in ["transport", "bus", "metro", "train", "taxi", "ride"])
    include_emergency = any(kw in keywords for kw in ["emergency", "help", "medical", "doctor", "exit"])

    # 1. Gates
    if include_gate:
        gates_list = venue.get("gates", [])
        gates_text = []
        for g in gates_list:
            if isinstance(g, dict):
                g_name = g.get("name", "Unknown Gate")
                g_loc = g.get("location", "Unknown Location")
                g_acc = "Accessible" if g.get("accessible") else "Standard access only"
                gates_text.append(f"- {g_name} ({g_loc}, {g_acc})")
            else:
                gates_text.append(f"- {g}")
        if gates_text:
            sections.append("Gates & Entrances:\n" + "\n".join(gates_text))
        else:
            sections.append("Gates & Entrances: Information not available.")

    # 2. Food Courts
    if include_food:
        facilities = venue.get("facilities", {})
        food_list = facilities.get("food_courts", []) if isinstance(facilities, dict) else []
        food_text = []
        for f in food_list:
            if isinstance(f, dict):
                f_name = f.get("name", "Food Plaza")
                f_loc = f.get("location", "Concourse")
                f_hrs = f.get("hours", "Match day hours")
                f_vendors = ", ".join(f.get("vendors", []))
                food_text.append(f"- {f_name} at {f_loc} (Hours: {f_hrs}, Vendors: {f_vendors})")
            else:
                food_text.append(f"- {f}")
        if food_text:
            sections.append("Food Courts & Dining:\n" + "\n".join(food_text))
        else:
            sections.append("Food Courts & Dining: Information not available.")

    # 3. Restrooms
    if include_restroom:
        facilities = venue.get("facilities", {})
        restroom_list = facilities.get("restrooms", []) if isinstance(facilities, dict) else []
        restroom_text = []
        for r in restroom_list:
            if isinstance(r, dict):
                r_name = r.get("name", "Restrooms")
                r_loc = r.get("location", "Concourse")
                r_acc = "Accessible" if r.get("accessible") else "Standard only"
                r_units = f"{r.get('count', '?')} units"
                restroom_text.append(f"- {r_name} at {r_loc} ({r_acc}, {r_units})")
            else:
                restroom_text.append(f"- {r}")
        if restroom_text:
            sections.append("Restrooms:\n" + "\n".join(restroom_text))
        else:
            sections.append("Restrooms: Information not available.")

    # 4. Transport Info
    if include_transport:
        transport = venue.get("transport", {})
        transport_text = []
        if isinstance(transport, dict):
            # Metro lines
            for m in transport.get("metro_lines", []):
                if isinstance(m, dict):
                    transport_text.append(f"- Metro/Bus: {m.get('name')} via {m.get('route')} ({m.get('frequency')}, Fare: {m.get('fare')})")
                else:
                    transport_text.append(f"- Metro: {m}")
            # Shuttle stops
            for s in transport.get("shuttle_stops", []):
                if isinstance(s, dict):
                    routes_str = ", ".join(s.get("routes", []))
                    transport_text.append(f"- Shuttle: {s.get('name')} at {s.get('location')} (Routes: {routes_str})")
                else:
                    transport_text.append(f"- Shuttle: {s}")
            # Parking zones
            for p in transport.get("parking_zones", []):
                if isinstance(p, dict):
                    transport_text.append(f"- Parking: {p.get('zone')} (Capacity: {p.get('capacity')}, Cost: {p.get('cost')}, Accessibility: {p.get('accessibility')})")
                else:
                    transport_text.append(f"- Parking: {p}")
        if transport_text:
            sections.append("Transportation & Transit:\n" + "\n".join(transport_text))
        else:
            sections.append("Transportation & Transit: Information not available.")

    # 5. Emergency Exits & Medical
    if include_emergency:
        emergency_text = []
        # Emergency exits
        exits = venue.get("emergency_exits", [])
        if exits:
            emergency_text.append("Emergency Exits:\n" + "\n".join(f"- {ex}" for ex in exits))
        # Medical
        facilities = venue.get("facilities", {})
        med_list = facilities.get("medical", []) if isinstance(facilities, dict) else []
        for m in med_list:
            if isinstance(m, dict):
                m_name = m.get("name", "Medical Station")
                m_loc = m.get("location", "Concourse")
                m_staff = m.get("staff", "EMTs")
                m_hrs = m.get("hours", "Match day hours")
                emergency_text.append(f"- First Aid: {m_name} at {m_loc} (Staff: {m_staff}, Hours: {m_hrs})")
            else:
                emergency_text.append(f"- Medical: {m}")
        if emergency_text:
            sections.append("Emergency & Medical Info:\n" + "\n".join(emergency_text))
        else:
            sections.append("Emergency & Medical Info: Information not available.")

    # Fallback to general sections overview if no keyword triggered
    if not (include_gate or include_food or include_restroom or include_transport or include_emergency):
        sections_str = []
        for s in venue.get("sections", []):
            if isinstance(s, dict):
                s_name = s.get("name", "Section")
                s_gates = ", ".join(s.get("gates", []))
                sections_str.append(f"- {s_name} (Level {s.get('level')}): accessible via gates {s_gates}")
            else:
                sections_str.append(f"- {s}")
        if sections_str:
            sections.append("Sections Overview:\n" + "\n".join(sections_str))

    return "\n\n".join(sections)

# 7. Add __main__ block
if __name__ == "__main__":
    print("\n--- Testing list_venues ---")
    print(list_venues())
    print("\n--- Testing get_venue_context for metlife with food ---")
    print(get_venue_context("metlife", ["food"]))
