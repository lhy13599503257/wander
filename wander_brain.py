import json
from datetime import datetime, timedelta

# ==========================================
# 1. 定义数据结构 (The Schema)
# ==========================================
# 这就是 Wander App 能读懂的“语言”

EXAMPLE_PROFILE = {
    "home": "Toronto, Canada",
    "vibe": "Chill & Relax",
    "transport": "Taxi / Uber",
    "budget": "Luxury ($$$$)",
    "interests": ["Gym", "Swimming", "Streetwear", "Vintage", "Watches"]
}

EXAMPLE_REQUEST = {
    "destination": "Paris, France",
    "start_date": "2026-05-01",
    "duration": 5
}

# ==========================================
# 2. 提示词工程 (Prompt Engineering)
# ==========================================
# 这一步是核心！教 AI 怎么当好一个“私人管家”

def construct_prompt(profile, request):
    prompt = f"""
    You are Wander AI, a luxury travel concierge for an Urban Nomad.
    
    USER PROFILE:
    - Origin: {profile['home']}
    - Style: {profile['vibe']} (Vital! Adjust pace accordingly)
    - Transport Preference: {profile['transport']}
    - Budget Level: {profile['budget']}
    - Key Interests: {', '.join(profile['interests'])}
    
    TRIP REQUEST:
    - Destination: {request['destination']}
    - Date: {request['start_date']}
    - Duration: {request['duration']} Days
    
    TASK:
    Generate a highly personalized itinerary.
    Since the user likes {profile['interests'][0]} (Sports), ensure the hotel has a top-tier gym or schedule a morning activity.
    Since the user likes {profile['interests'][2]} (Shopping), include specific flagship stores or hidden gems, not generic malls.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "trip_title": "The Paris Escape",
        "meta": "Spring 2026 • 5 Days",
        "days": [
            {{
                "day_num": 1,
                "date": "2026-05-01",
                "theme": "Arrival & First Fits",
                "activities": [
                    {{
                        "time": "10:00 AM",
                        "type": "coffee", 
                        "name": "Cafe Kitsuné",
                        "desc": "Start with a matcha latte. Near the Palais Royal."
                    }},
                    {{
                        "time": "02:00 PM",
                        "type": "shopping",
                        "name": "Kith Paris",
                        "desc": "Check out the exclusive Paris box logo tee."
                    }}
                ]
            }}
        ]
    }}
    """
    return prompt

# ==========================================
# 3. 模拟生成 (Mock Generator)
# ==========================================
# 在没接真实 LLM API 之前，我们先用代码生成一个假数据来测试

def generate_mock_itinerary():
    # 假设这是 AI 返回的 JSON
    mock_data = {
        "destination": "Paris",
        "bg_image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?q=80&w=2073&auto=format&fit=crop",
        "days": [
            {
                "day": "Day 01",
                "activities": [
                    {"time": "10:00 AM", "tag": "RELAX", "color": "text-orange-500", "title": "Check-in @ Cheval Blanc", "desc": "Luxury hotel with Dior Spa. Unpack and hit the gym."},
                    {"time": "01:00 PM", "tag": "LUNCH", "color": "text-blue-400", "title": "L'Avenue", "desc": "The spot to be seen. Order the spicy tuna tartare."},
                    {"time": "03:00 PM", "tag": "SHOPPING", "color": "text-purple-400", "title": "Kith Paris", "desc": "Historic building turned streetwear temple. Brunch & Sadelle's inside."},
                    {"time": "07:00 PM", "tag": "DINNER", "color": "text-red-400", "title": "Girafe", "desc": "Best view of the Eiffel Tower. Seafood platter is a must."}
                ]
            },
            {
                "day": "Day 02",
                "activities": [
                    {"time": "09:00 AM", "tag": "ACTIVE", "color": "text-green-400", "title": "Run @ Tuileries Garden", "desc": "5km scenic run. Watch the city wake up."},
                    {"time": "11:00 AM", "tag": "VINTAGE", "color": "text-purple-400", "title": "Thanx God I'm a VIP", "desc": "High-end vintage. Curated selection, no digging required."},
                    {"time": "08:00 PM", "tag": "NIGHT", "color": "text-red-400", "title": "Hotel Costes", "desc": "Iconic vibe. Dark corners, great music, beautiful people."}
                ]
            }
        ]
    }
    return json.dumps(mock_data, indent=2)

if __name__ == "__main__":
    print("🧠 Wander Brain v0.1 Initialized...")
    print("-" * 40)
    print("Generating itinerary for: Paris (Luxury + Streetwear)")
    print("-" * 40)
    print(generate_mock_itinerary())
