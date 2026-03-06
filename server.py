"""
Wander Backend — Flask Edition
Replaces Python http.server (single-thread) with Flask (multi-thread, production-ready)
"""
from flask import Flask, request, jsonify, send_from_directory, abort
import json
import os
import time
import requests as req_lib

try:
    import wander_engine
except ImportError:
    print("⚠️  wander_engine not found. AI features disabled.")
    wander_engine = None

# ==========================================
# 🔧 CONFIGURATION
# ==========================================
PORT = int(os.environ.get('PORT', 8000))          # Railway sets PORT automatically
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Amadeus API (free dev tier: https://developers.amadeus.com)
AMADEUS_CLIENT_ID     = os.environ.get('AMADEUS_CLIENT_ID', '')
AMADEUS_CLIENT_SECRET = os.environ.get('AMADEUS_CLIENT_SECRET', '')
AMADEUS_BASE          = 'https://test.api.amadeus.com'   # switch to api.amadeus.com for prod

# Simple city → IATA lookup (covers most popular destinations)
CITY_IATA = {
    'toronto':'YYZ','vancouver':'YVR','montreal':'YUL','calgary':'YYC',
    'new york':'JFK','los angeles':'LAX','chicago':'ORD','miami':'MIA',
    'san francisco':'SFO','seattle':'SEA','boston':'BOS','las vegas':'LAS',
    'london':'LHR','paris':'CDG','rome':'FCO','milan':'MXP','barcelona':'BCN',
    'madrid':'MAD','amsterdam':'AMS','berlin':'BER','munich':'MUC',
    'zurich':'ZRH','vienna':'VIE','prague':'PRG','lisbon':'LIS',
    'tokyo':'NRT','osaka':'KIX','seoul':'ICN','beijing':'PEK','shanghai':'PVG',
    'hong kong':'HKG','singapore':'SIN','bangkok':'BKK','bali':'DPS',
    'dubai':'DXB','istanbul':'IST','sydney':'SYD','melbourne':'MEL',
    'auckland':'AKL','mexico city':'MEX','cancun':'CUN','rio de janeiro':'GIG',
    'sao paulo':'GRU','buenos aires':'EZE',
}

app = Flask(__name__, static_folder=DIRECTORY)

# ==========================================
# ✈️ AMADEUS HELPERS
# ==========================================
_amadeus_token = {'value': None, 'expires': 0}

def get_amadeus_token():
    if not AMADEUS_CLIENT_ID:
        return None
    if time.time() < _amadeus_token['expires']:
        return _amadeus_token['value']
    try:
        r = req_lib.post(f'{AMADEUS_BASE}/v1/security/oauth2/token',
            data={'grant_type':'client_credentials',
                  'client_id': AMADEUS_CLIENT_ID,
                  'client_secret': AMADEUS_CLIENT_SECRET},
            timeout=8)
        data = r.json()
        _amadeus_token['value'] = data.get('access_token')
        _amadeus_token['expires'] = time.time() + data.get('expires_in', 1799) - 30
        return _amadeus_token['value']
    except Exception as e:
        print(f'⚠️  Amadeus token error: {e}')
        return None

def city_to_iata(city_name):
    clean = city_name.lower().split(',')[0].strip()
    return CITY_IATA.get(clean, clean[:3].upper())

# ==========================================
# 🌐 ROUTES
# ==========================================
@app.route('/')
def index():
    return send_from_directory(DIRECTORY, 'prototype.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(DIRECTORY, 'manifest.json')

@app.route('/sw.js')
def service_worker():
    from flask import Response
    sw_content = open(os.path.join(DIRECTORY, 'sw.js')).read()
    return Response(sw_content, mimetype='application/javascript')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(DIRECTORY, filename)

# GET: Health check
@app.route('/api/health')
def api_health():
    return jsonify({"status": "ok", "amadeus": bool(AMADEUS_CLIENT_ID)})

# GET: Search real flights via Amadeus
@app.route('/api/flights')
def api_flights():
    origin_city = request.args.get('from', '')
    dest_city   = request.args.get('to', '')
    date        = request.args.get('date', '')
    adults      = request.args.get('adults', '1')

    if not origin_city or not dest_city or not date:
        return jsonify({"error": "Missing from/to/date params"}), 400

    token = get_amadeus_token()
    if not token:
        return jsonify({"error": "Amadeus not configured", "hint": "Add AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET env vars"}), 503

    origin_iata = city_to_iata(origin_city)
    dest_iata   = city_to_iata(dest_city)
    print(f"✈️  Flight search: {origin_iata} → {dest_iata} on {date}")

    try:
        r = req_lib.get(f'{AMADEUS_BASE}/v2/shopping/flight-offers',
            headers={'Authorization': f'Bearer {token}'},
            params={
                'originLocationCode': origin_iata,
                'destinationLocationCode': dest_iata,
                'departureDate': date,
                'adults': adults,
                'max': 5,
                'currencyCode': 'USD',
            }, timeout=10)
        raw = r.json()

        # Normalize to a clean format for the frontend
        flights = []
        for offer in raw.get('data', []):
            seg = offer['itineraries'][0]['segments'][0]
            price = offer['price']['total']
            dep = seg['departure']
            arr = seg['arrival']
            flights.append({
                'airline': seg.get('carrierCode',''),
                'flight_num': seg.get('carrierCode','') + seg.get('number',''),
                'from': dep['iataCode'],
                'to': arr['iataCode'],
                'depart': dep['at'],
                'arrive': arr['at'],
                'duration': offer['itineraries'][0]['duration'].replace('PT','').replace('H','h ').replace('M','m').strip(),
                'stops': len(offer['itineraries'][0]['segments']) - 1,
                'price': f"${price}",
                'class': offer['travelerPricings'][0]['fareDetailsBySegment'][0].get('cabin','ECONOMY').title(),
            })
        return jsonify({"flights": flights, "origin": origin_iata, "dest": dest_iata})

    except Exception as e:
        print(f'❌ Amadeus search error: {e}')
        return jsonify({"error": str(e)}), 500

# POST: Generate new itinerary
@app.route('/api/plan', methods=['POST'])
def api_plan():
    if not wander_engine:
        return jsonify({"error": "AI engine unavailable"}), 503

    payload = request.get_json()
    profile = payload.get('profile', {})
    req = payload.get('request', {})

    print(f"🧠 Generating trip → {req.get('destination', '?')}, {req.get('duration', '?')} days")

    result = wander_engine.generate_itinerary(profile, req)

    # Attach metadata
    result['id'] = int(time.time())
    result['created_at'] = time.strftime("%Y-%m-%d %H:%M")
    result['summary'] = {
        "city": req.get('destination'),
        "date": req.get('start_date') or "Anytime",
        "duration": req.get('duration')
    }
    # Trips are saved in browser localStorage — no DB needed
    print(f"✅ Trip generated (id={result['id']})")
    return jsonify(result)

# POST: AI adjust itinerary
@app.route('/api/adjust', methods=['POST'])
def api_adjust():
    if not wander_engine:
        return jsonify({"error": "AI engine unavailable"}), 503

    payload = request.get_json()
    itinerary = payload.get('itinerary', {})
    user_request = payload.get('request', '')
    language = payload.get('language', 'English')

    print(f"🤖 Adjusting: '{user_request[:60]}' for {itinerary.get('destination', '?')}")
    result = wander_engine.adjust_itinerary(itinerary, user_request, language)
    return jsonify(result)



# ==========================================
# 🚀 START
# ==========================================
if __name__ == '__main__':
    print(f"🚀 Wander Server (Flask) → http://localhost:{PORT}")
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        threaded=True   # Handle multiple requests concurrently
    )
