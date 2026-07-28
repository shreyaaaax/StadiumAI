import sys
import json
import httpx
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://127.0.0.1:8000"

async def test_all():
    results = {}
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. GET /health
        print("Testing GET /health...")
        try:
            r = await client.get(f"{BASE_URL}/health")
            print(f"Status: {r.status_code}, Body: {r.json()}")
            results["GET_health"] = {
                "url": "/health",
                "request_method": "GET",
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"GET /health Failed: {e}")

        # 2. GET /venues
        print("Testing GET /venues...")
        try:
            r = await client.get(f"{BASE_URL}/venues")
            print(f"Status: {r.status_code}, Total Venues: {len(r.json())}")
            results["GET_venues"] = {
                "url": "/venues",
                "request_method": "GET",
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"GET /venues Failed: {e}")

        # 3. POST /chat
        print("Testing POST /chat (with explicit language config)...")
        chat_payload = {"message": "Where is Gate B?", "venue_id": "metlife", "language": "es"}
        try:
            r = await client.post(f"{BASE_URL}/chat", json=chat_payload)
            print(f"Status: {r.status_code}, Reply: {r.json().get('reply')}")
            # Also test the secondary /api/chat path to ensure it maps correctly
            r_api = await client.post(f"{BASE_URL}/api/chat", json=chat_payload)
            print(f"Alias POST /api/chat mapping returned status: {r_api.status_code}")
            
            results["POST_chat"] = {
                "url": "/chat",
                "request_method": "POST",
                "payload": chat_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /chat Failed: {e}")

        # 3b. POST /chat (with auto-detected language)
        print("Testing POST /chat (with auto-detected Spanish)...")
        chat_auto_payload = {"message": "¿Dónde está la puerta principal, por favor?", "venue_id": "metlife"}
        try:
            r = await client.post(f"{BASE_URL}/chat", json=chat_auto_payload)
            print(f"Status: {r.status_code}, Detected Lang: {r.json().get('language')}, Reply: {r.json().get('reply')[:65]}...")
            
            results["POST_chat_auto"] = {
                "url": "/chat (auto-detect)",
                "request_method": "POST",
                "payload": chat_auto_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /chat auto-detect Failed: {e}")

        # 4. POST /navigation
        print("Testing POST /navigation...")
        nav_payload = {
            "from_location": "parking lot C",
            "to_location": "Section 214",
            "venue_id": "metlife",
            "language": "fr",
            "accessible": True
        }
        try:
            r = await client.post(f"{BASE_URL}/navigation", json=nav_payload)
            print(f"Status: {r.status_code}, Steps count: {len(r.json().get('steps', []))}")
            results["POST_navigation"] = {
                "url": "/navigation",
                "request_method": "POST",
                "payload": nav_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /navigation Failed: {e}")

        # 5. GET /crowd/metlife?phase=half_time
        print("Testing GET /crowd/metlife?phase=half_time...")
        try:
            r = await client.get(f"{BASE_URL}/crowd/metlife?phase=half_time")
            print(f"Status: {r.status_code}, Zones simulated: {len(r.json())}")
            # Also verify alias /api/crowd mapping
            r_api = await client.get(f"{BASE_URL}/api/crowd/metlife?phase=half_time")
            print(f"Alias GET /api/crowd/metlife returned status: {r_api.status_code}")
            
            results["GET_crowd"] = {
                "url": "/crowd/metlife?phase=half_time",
                "request_method": "GET",
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"GET /crowd Failed: {e}")

        # 6. POST /crowd/predict
        print("Testing POST /crowd/predict...")
        predict_payload = {
            "venue_id": "metlife",
            "current_phase": "half_time",
            "query": "Is there severe congestion at food courts during halftime?"
        }
        try:
            r = await client.post(f"{BASE_URL}/crowd/predict", json=predict_payload)
            print(f"Status: {r.status_code}, Short Recommendation: {r.json().get('recommendation')[:65]}...")
            results["POST_crowd_predict"] = {
                "url": "/crowd/predict",
                "request_method": "POST",
                "payload": predict_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /crowd/predict Failed: {e}")

        # 7. POST /transport/recommend
        print("Testing POST /transport/recommend...")
        transport_payload = {
            "venue_id": "metlife",
            "match_time_24h": "20:00",
            "current_time_24h": "18:30",
            "origin": "New York Penn Station",
            "language": "en"
        }
        try:
            r = await client.post(f"{BASE_URL}/transport/recommend", json=transport_payload)
            print(f"Status: {r.status_code}, Departure field: {r.json().get('suggested_departure')}")
            results["POST_transport_recommend"] = {
                "url": "/transport/recommend",
                "request_method": "POST",
                "payload": transport_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /transport/recommend Failed: {e}")

        # 8. POST /staff/query
        print("Testing POST /staff/query...")
        staff_query_payload = {
            "question": "What is my escalation protocol if standard security gate access is jammed?",
            "role": "security",
            "venue_id": "metlife"
        }
        try:
            r = await client.post(f"{BASE_URL}/staff/query", json=staff_query_payload)
            print(f"Status: {r.status_code}, Answer: {r.json().get('answer')[:65]}...")
            results["POST_staff_query"] = {
                "url": "/staff/query",
                "request_method": "POST",
                "payload": staff_query_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /staff/query Failed: {e}")

        # 9. POST /staff/incident_report
        print("Testing POST /staff/incident_report...")
        staff_incident_payload = {
            "description": "Minor spectator slip near Gate B due to wet floor.",
            "location": "Gate B concourse area",
            "severity": 2
        }
        try:
            r = await client.post(f"{BASE_URL}/staff/incident_report", json=staff_incident_payload)
            print(f"Status: {r.status_code}, Incident Report:\n{r.json().get('report_text')[:100]}...")
            results["POST_staff_incident_report"] = {
                "url": "/staff/incident_report",
                "request_method": "POST",
                "payload": staff_incident_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /staff/incident_report Failed: {e}")

        # 10. GET /sustainability/metlife?phase=during
        print("Testing GET /sustainability/metlife?phase=during...")
        try:
            r = await client.get(f"{BASE_URL}/sustainability/metlife?phase=during")
            print(f"Status: {r.status_code}, Energy: {r.json().get('energy_kwh')} kWh, Eco Score: {r.json().get('eco_score')}")
            # Also test the secondary /api/sustainability path mapping
            r_api = await client.get(f"{BASE_URL}/api/sustainability/metlife?phase=during")
            print(f"Alias GET /api/sustainability/metlife mapping returned status: {r_api.status_code}")
            
            results["GET_sustainability_metrics"] = {
                "url": "/sustainability/metlife?phase=during",
                "request_method": "GET",
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"GET /sustainability/metlife Failed: {e}")

        # 11. POST /sustainability/insight
        print("Testing POST /sustainability/insight...")
        sustainability_insight_payload = {
            "venue_id": "metlife",
            "question": "How can we cut energy usage by 15% and increase recycling during the match?",
            "phase": "during"
        }
        try:
            r = await client.post(f"{BASE_URL}/sustainability/insight", json=sustainability_insight_payload)
            print(f"Status: {r.status_code}, Insight: {r.json().get('insight')[:65]}...")
            results["POST_sustainability_insight"] = {
                "url": "/sustainability/insight",
                "request_method": "POST",
                "payload": sustainability_insight_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /sustainability/insight Failed: {e}")

        # 12. GET /sustainability/metlife/fan_score
        print("Testing GET /sustainability/metlife/fan_score...")
        try:
            r = await client.get(f"{BASE_URL}/sustainability/metlife/fan_score")
            print(f"Status: {r.status_code}, Fan message: {r.json().get('message')}")
            results["GET_sustainability_fan_score"] = {
                "url": "/sustainability/metlife/fan_score",
                "request_method": "GET",
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"GET /sustainability/metlife/fan_score Failed: {e}")

        # 13. POST /accessibility/assist
        print("Testing POST /accessibility/assist...")
        assist_payload = {
            "query": "Where can I find wheelchair-accessible toilets?",
            "venue_id": "sofi",
            "language": "en",
            "need": "mobility"
        }
        try:
            r = await client.post(f"{BASE_URL}/accessibility/assist", json=assist_payload)
            print(f"Status: {r.status_code}, Response: {r.json().get('response')}, Items: {len(r.json().get('accessible_features_nearby', []))}")
            # Also test the secondary /api/accessibility mapping
            r_api = await client.post(f"{BASE_URL}/api/accessibility/assist", json=assist_payload)
            print(f"Alias POST /api/accessibility/assist mapping returned status: {r_api.status_code}")
            
            results["POST_accessibility_assist"] = {
                "url": "/accessibility/assist",
                "request_method": "POST",
                "payload": assist_payload,
                "status_code": r.status_code,
                "response_body": r.json()
            }
        except Exception as e:
            print(f"POST /accessibility/assist Failed: {e}")

    # Write results to data/api_responses_example.json
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "api_responses_example.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccessfully stored capture responses to: {out_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_all())
