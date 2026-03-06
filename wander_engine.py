import json
import os
import urllib.request
import urllib.error

# ==========================================
# 🔑 API KEY CONFIGURATION
# ==========================================
import os as _os
API_KEY = _os.environ.get('GEMINI_API_KEY', '')
MODEL_NAME = "gemini-2.5-flash"

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "thinkingConfig": {"thinkingBudget": 0}  # Disable thinking = 5x faster, avoids Railway 60s timeout
        }
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=100) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        print(f"❌ Gemini HTTP Error {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"❌ Gemini API Error: {type(e).__name__}: {e}")
        return None

def normalize_city(city):
    """Normalize Nominatim output like '厦门市, 中国' → 'Xiamen, China'."""
    # Chinese city names → English
    CITY_MAP = {
        '北京': 'Beijing', '上海': 'Shanghai', '广州': 'Guangzhou', '深圳': 'Shenzhen',
        '成都': 'Chengdu', '重庆': 'Chongqing', '武汉': 'Wuhan', '西安': 'Xian',
        '杭州': 'Hangzhou', '南京': 'Nanjing', '苏州': 'Suzhou', '天津': 'Tianjin',
        '厦门': 'Xiamen', '青岛': 'Qingdao', '大连': 'Dalian', '哈尔滨': 'Harbin',
        '长沙': 'Changsha', '昆明': 'Kunming', '三亚': 'Sanya', '丽江': 'Lijiang',
        '香港': 'Hong Kong', '澳门': 'Macau', '台北': 'Taipei',
        '东京': 'Tokyo', '大阪': 'Osaka', '京都': 'Kyoto', '札幌': 'Sapporo',
        '名古屋': 'Nagoya', '福冈': 'Fukuoka', '神户': 'Kobe', '奈良': 'Nara',
        '首尔': 'Seoul', '釜山': 'Busan', '济州': 'Jeju',
        '悉尼': 'Sydney', '墨尔本': 'Melbourne', '布里斯班': 'Brisbane',
        '奥克兰': 'Auckland', '惠灵顿': 'Wellington', '皇后镇': 'Queenstown',
        '巴黎': 'Paris', '里昂': 'Lyon', '尼斯': 'Nice', '马赛': 'Marseille',
        '伦敦': 'London', '曼彻斯特': 'Manchester', '爱丁堡': 'Edinburgh',
        '罗马': 'Rome', '米兰': 'Milan', '威尼斯': 'Venice', '佛罗伦萨': 'Florence',
        '那不勒斯': 'Naples', '都灵': 'Turin',
        '巴塞罗那': 'Barcelona', '马德里': 'Madrid', '塞维利亚': 'Seville',
        '里斯本': 'Lisbon', '波尔图': 'Porto',
        '阿姆斯特丹': 'Amsterdam', '鹿特丹': 'Rotterdam',
        '柏林': 'Berlin', '慕尼黑': 'Munich', '汉堡': 'Hamburg', '法兰克福': 'Frankfurt',
        '苏黎世': 'Zurich', '日内瓦': 'Geneva', '伯尔尼': 'Bern',
        '维也纳': 'Vienna', '萨尔茨堡': 'Salzburg',
        '布鲁塞尔': 'Brussels', '布鲁日': 'Bruges',
        '布拉格': 'Prague', '布达佩斯': 'Budapest', '华沙': 'Warsaw', '克拉科夫': 'Krakow',
        '雅典': 'Athens', '圣托里尼': 'Santorini', '米科诺斯': 'Mykonos',
        '伊斯坦布尔': 'Istanbul', '安卡拉': 'Ankara',
        '迪拜': 'Dubai', '阿布扎比': 'Abu Dhabi', '多哈': 'Doha',
        '新加坡': 'Singapore', '吉隆坡': 'Kuala Lumpur',
        '曼谷': 'Bangkok', '普吉': 'Phuket', '清迈': 'Chiang Mai', '芭提雅': 'Pattaya',
        '河内': 'Hanoi', '胡志明市': 'Ho Chi Minh City', '岘港': 'Da Nang',
        '巴厘岛': 'Bali', '雅加达': 'Jakarta', '日惹': 'Yogyakarta',
        '马尼拉': 'Manila', '宿务': 'Cebu', '长滩岛': 'Boracay',
        '孟买': 'Mumbai', '新德里': 'Delhi', '班加罗尔': 'Bangalore',
        '纽约': 'New York', '洛杉矶': 'Los Angeles', '芝加哥': 'Chicago',
        '旧金山': 'San Francisco', '迈阿密': 'Miami', '拉斯维加斯': 'Las Vegas',
        '西雅图': 'Seattle', '波士顿': 'Boston', '华盛顿': 'Washington DC',
        '多伦多': 'Toronto', '温哥华': 'Vancouver', '蒙特利尔': 'Montreal',
        '墨西哥城': 'Mexico City', '坎昆': 'Cancun',
        '里约热内卢': 'Rio de Janeiro', '圣保罗': 'Sao Paulo', '布宜诺斯艾利斯': 'Buenos Aires',
        '开罗': 'Cairo', '马拉喀什': 'Marrakech', '内罗毕': 'Nairobi',
        '约翰内斯堡': 'Johannesburg', '开普敦': 'Cape Town',
        '雷克雅未克': 'Reykjavik', '赫尔辛基': 'Helsinki',
        '哥本哈根': 'Copenhagen', '斯德哥尔摩': 'Stockholm', '奥斯陆': 'Oslo',
    }
    # Chinese country/region names → English
    COUNTRY_MAP = {
        '中国': 'China', '美国': 'USA', '日本': 'Japan', '韩国': 'South Korea',
        '法国': 'France', '英国': 'UK', '德国': 'Germany', '意大利': 'Italy',
        '西班牙': 'Spain', '泰国': 'Thailand', '澳大利亚': 'Australia', '加拿大': 'Canada',
        '新西兰': 'New Zealand', '新加坡': 'Singapore', '印度': 'India',
        '越南': 'Vietnam', '印度尼西亚': 'Indonesia', '菲律宾': 'Philippines',
        '马来西亚': 'Malaysia', '阿联酋': 'UAE', '土耳其': 'Turkey',
        '希腊': 'Greece', '葡萄牙': 'Portugal', '荷兰': 'Netherlands',
        '瑞士': 'Switzerland', '奥地利': 'Austria', '比利时': 'Belgium',
        '捷克': 'Czechia', '匈牙利': 'Hungary', '波兰': 'Poland',
        '巴西': 'Brazil', '阿根廷': 'Argentina', '墨西哥': 'Mexico',
        '摩洛哥': 'Morocco', '南非': 'South Africa', '埃及': 'Egypt',
        '冰岛': 'Iceland', '挪威': 'Norway', '瑞典': 'Sweden', '芬兰': 'Finland',
        # Australian states & common regions
        '新南威尔士': 'New South Wales', '维多利亚': 'Victoria',
        '昆士兰': 'Queensland', '西澳大利亚': 'Western Australia',
        # Japanese prefectures
        '东京都': 'Tokyo', '大阪府': 'Osaka', '京都府': 'Kyoto',
        # US states
        '加利福尼亚': 'California', '纽约州': 'New York State',
        '佛罗里达': 'Florida', '德克萨斯': 'Texas',
    }
    # Handle multi-city routes (contains →)
    if '→' in city:
        parts = city.split('→')
        return ' → '.join(normalize_city(p.strip()) for p in parts)
    # Replace Chinese city names first
    for zh, en in CITY_MAP.items():
        city = city.replace(zh, en)
    # Replace Chinese country names
    for zh, en in COUNTRY_MAP.items():
        city = city.replace(zh, en)
    # Strip Chinese admin suffixes
    for suffix in ['市', '省', '自治区', '特别行政区', '州', '都', '道', '府', '县']:
        city = city.replace(suffix, '')
    # Clean up
    parts = [p.strip() for p in city.split(',') if p.strip()]
    return ', '.join(parts)

def generate_itinerary(profile, request_data):
    dest = normalize_city(request_data.get('destination', 'Paris'))
    days_count = request_data.get('duration', 7) 
    budget = request_data.get('budget', '5000')
    language = request_data.get('language', 'English')
    currency = request_data.get('currency', 'USD')
    
    print(f"🧠 Engine Thinking... Target: {dest}, {days_count} Days, Budget: {currency}{budget}, Lang: {language}")

    transport_pref = profile.get('transport', 'transit')
    budget_level = profile.get('budget', 'standard')
    user_style = profile.get('style', 'chill')
    user_tags = ', '.join(profile.get('tags', [])) or 'General sightseeing'
    user_sports = ', '.join(profile.get('sports', [])) or 'None'
    confirmed_flight = request_data.get('confirmed_flight')
    flight_note = f"\n    - CONFIRMED FLIGHT (user already booked): {confirmed_flight}" if confirmed_flight else ""

    prompt = f"""
    You are 'Wander', the world's most attentive luxury travel concierge. You plan trips like a helicopter mom who has done 100+ trips to this destination personally. Every recommendation is SPECIFIC, VERIFIED (in your knowledge), and ACTIONABLE.

    USER PROFILE:
    - Origin: {profile.get('location', 'Toronto, Canada')}
    - Travel Vibe: {user_style} (chill=relaxed pace, rush=pack in as much as possible)
    - Shopping Interests: {user_tags}
    - Active Interests: {user_sports}
    - Transport Preference: {transport_pref}
    - Budget Level: {budget_level}

    TRIP REQUEST:
    - Destination: {dest}{'  ← MULTI-CITY ROUTE: plan each city segment in order, include inter-city transit day(s)' if '→' in dest else ''}
    - Duration: {days_count} Days
    - Total Budget: {budget} {currency}
    - Preferred Currency for costs: {currency}
    - Start Date: {request_data.get('start_date', 'Flexible')}{flight_note}

    OUTPUT LANGUAGE: {language}
    (Generate ALL text in {language}. Place names may stay in local script or romanized.)

    ═══════════════════════════════════════
    CONCIERGE STANDARDS — NON-NEGOTIABLE:
    ═══════════════════════════════════════

    1. VENUE SPECIFICITY: Always name the EXACT venue. Never say "a local café" — say "Café de Flore (172 Bd Saint-Germain)". Always include the address.

    2. WHAT TO DO/ORDER: For restaurants → specify exactly what to order and approx cost per item. For shops → name 2-3 must-see items/brands. For attractions → name the specific exhibit, viewpoint, or experience.

    3. BOOKING INFO: State clearly: "Reservation required — book via [method]" or "Walk-in only, arrive by [time] to avoid queues."

    4. TRANSIT (step-by-step): Don't say "take the metro". Say: "Exit the restaurant, turn LEFT on Rue de Rivoli → take Metro Line 1 (Direction: La Défense) from Châtelet, 4 stops to Charles de Gaulle-Étoile, exit 2 → 3 min walk north on Ave Kléber. Total: ~18 min."

    5. DURATION: State exactly how long to spend: "Allow 45 min here."

    6. PHOTO SPOT: Name 1 specific Instagram-worthy spot within each venue (e.g., "Best photo: stand at the top of the staircase facing east at golden hour").

    7. STORE SELECTION PHILOSOPHY (no ads — pure quality):
       - Prioritize LOCAL LEGENDS loved by residents, not tourists
       - Avoid chains unless truly exceptional for the destination
       - Mix 1-2 hidden gems with 1-2 famous icons per day
       - Match selections to user's stated shopping/sport interests
       - Note if a place is "Tourist Trap ⚠️" so user can decide

    8. TIMING INTELLIGENCE:
       - Schedule museums on weekday mornings (fewer crowds)
       - Schedule markets on their actual open days
       - Leave buffer time after heavy meals
       - If user is "chill" style: max 4-5 activities/day, include 1 "rest" slot
       - If user is "rush" style: 6-8 activities/day, optimized by geography

    9. COORDINATES: Provide accurate lat/lng (decimal degrees) for EVERY activity.

    10. COST FORMAT: Use {currency}. Integers only. Dot as decimal separator. No comma-thousands separators. Realistic local prices.

    11. INTER-CITY TRANSIT (for multi-city routes): For each city transition, include a dedicated transit activity:
        - title: "✈ / 🚄 / 🚌 [City A] → [City B]"
        - desc: Exact train/bus/flight name, departure station, arrival station, booking platform
        - cost: Realistic transport cost in {currency}
        - duration: Door-to-door time including check-in/boarding
        - transit tip: "Book 2+ weeks ahead for best prices on [platform]"
        Include this transit cost in budget_summary.transport.

    12. TRANSPORT BUDGET IN CITY: Include a daily transport estimate activity at start of each city's days:
        - e.g., "🚇 Daily Transport Budget — Tokyo" with cost = realistic daily metro/bus spend

    OUTPUT JSON FORMAT (return ONLY valid JSON, nothing else):
    {{
        "destination": "{dest}",
        "bg_image": "https://source.unsplash.com/1600x900/?{dest},travel",
        "flight": {{
            "airline": "Air Canada",
            "flight_num": "AC870",
            "route": "YYZ → CDG",
            "duration": "7h 20m",
            "price": "1245",
            "class": "Economy",
            "booking_tip": "Book 6-8 weeks ahead. Seat 31A has extra legroom."
        }},
        "hotel": {{
            "name": "The Hoxton, Paris",
            "address": "30-32 Rue du Sentier, 75002 Paris",
            "price_per_night": "280",
            "total_stay": "1960",
            "rating": "4.7/5",
            "why": "Boutique feel, central Marais location, roof terrace for sunset drinks.",
            "check_in_tip": "Request a room above floor 3 for quieter sleep."
        }},
        "budget_summary": {{
            "flight": "1245",
            "stay": "1960",
            "food_drink": "700",
            "transport": "150",
            "activities": "200",
            "shopping_buffer": "745",
            "total": "5000"
        }},
        "days": [
            {{
                "day": "Day 01",
                "theme": "Arrive & Breathe — Le Marais",
                "activities": [
                    {{
                        "time": "02:00 PM",
                        "tag": "Arrival",
                        "color": "text-blue-400",
                        "title": "Check-in: The Hoxton, Paris",
                        "address": "30-32 Rue du Sentier, 75002 Paris",
                        "desc": "Drop your bags. Ask for a room upgrade (mention it's a special trip). The lobby bar does excellent espresso — grab one before you head out.",
                        "what_to_do": "Ask concierge for their current neighborhood recommendations — they're always better than Google.",
                        "duration": "45 min",
                        "cost": "0",
                        "lat": 48.8672,
                        "lng": 2.3492,
                        "transit": "From CDG: Take RER B to Châtelet–Les Halles (35 min, €11.80), then walk 10 min east on Rue Rambuteau. Skip taxis — traffic is brutal.",
                        "pro_tip": "Leave your passport photocopy at front desk. Keep original in room safe.",
                        "photo_spot": "The neon-lit entrance at dusk — always a great first Paris shot.",
                        "nav_link": "https://www.google.com/maps/search/?api=1&query=The+Hoxton+Paris+30+Rue+du+Sentier"
                    }}
                ]
            }}
        ]
    }}
    """

    print(f"📡 Calling {MODEL_NAME}...")
    ai_response = call_gemini(prompt)
    
    if ai_response:
        try:
            clean_json = ai_response.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            print("❌ Failed to parse AI JSON.")
    
    # Fallback to Mock if API fails
    return mock_generator(dest, int(days_count), profile)

def adjust_itinerary(itinerary, user_request, language='English'):
    """Surgically modify an existing itinerary based on user's natural language request."""
    dest = itinerary.get('destination', 'Unknown')
    days = itinerary.get('days', [])

    # Build a compact day overview for context
    day_overview = '\n'.join([
        f"  Day {i} (index {i}): {d.get('day','')} — {d.get('theme','')} — {len(d.get('activities',[]))} activities"
        for i, d in enumerate(days)
    ])

    # Compact the itinerary (remove heavy fields to save tokens)
    compact_days = []
    for d in days:
        compact_acts = []
        for a in d.get('activities', []):
            compact_acts.append({
                'time': a.get('time'), 'tag': a.get('tag'), 'title': a.get('title'),
                'address': a.get('address'), 'cost': a.get('cost'), 'desc': a.get('desc')
            })
        compact_days.append({'day': d.get('day'), 'theme': d.get('theme'), 'activities': compact_acts})

    itinerary_compact = json.dumps({'destination': dest, 'days': compact_days}, ensure_ascii=False)

    prompt = f"""
You are Wander AI, modifying an existing itinerary for {dest}.

DAYS OVERVIEW:
{day_overview}

CURRENT ITINERARY (compact):
{itinerary_compact}

USER REQUEST: "{user_request}"

OUTPUT LANGUAGE: {language}

INSTRUCTIONS:
1. Identify which day(s) need to change (use 0-based index).
2. Make ONLY the changes the user requested — keep everything else identical.
3. For modified activities: apply full concierge quality (specific venue, address, exact cost in same currency, step-by-step transit, pro_tip, photo_spot, what_to_do, duration, lat/lng).
4. If user asks for something impossible (e.g., a museum that's closed that day), explain and offer the best alternative.

RETURN FORMAT — ONLY valid JSON, nothing else:
{{
    "changed_days": [0, 2],
    "days": [
        {{
            "day": "Day 01",
            "theme": "Updated theme if relevant",
            "activities": [
                {{
                    "time": "10:00 AM",
                    "tag": "Category",
                    "color": "text-neutral-400",
                    "title": "Specific Venue Name",
                    "address": "Full street address",
                    "desc": "Detailed description of what to do/experience.",
                    "what_to_do": "Exactly what to order, see, or do here.",
                    "duration": "X hours",
                    "cost": "25",
                    "lat": 48.8584,
                    "lng": 2.2945,
                    "transit": "Step-by-step directions from previous stop.",
                    "pro_tip": "Insider tip.",
                    "photo_spot": "Best photo location here.",
                    "nav_link": "https://www.google.com/maps/search/?api=1&query=Venue+Name+City"
                }}
            ]
        }}
    ],
    "change_summary": "One-line summary of what changed (e.g., Swapped dinner for Le Comptoir du Relais, a legendary Paris bistro)",
    "detail": "Optional extra info or a tip about the change."
}}

IMPORTANT: Include in "days" array ONLY the days that were modified, in the same order as "changed_days".
"""

    print(f"📡 Calling {MODEL_NAME} for itinerary adjustment...")
    ai_response = call_gemini(prompt)

    if ai_response:
        try:
            clean = ai_response.replace('```json', '').replace('```', '').strip()
            return json.loads(clean)
        except json.JSONDecodeError as e:
            print(f"❌ Adjust JSON parse error: {e}")
            return {"error": "AI returned invalid JSON. Please try again."}

    return {"error": "AI service unavailable. Is your API key valid?"}


def mock_generator(city, days, profile):
    # Mock fallback remains same as safety net
    return {
        "destination": city, 
        "bg_image": "https://source.unsplash.com/1600x900/?travel",
        "days": []
    }
