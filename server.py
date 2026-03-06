"""
Wander Backend — Flask Edition
Replaces Python http.server (single-thread) with Flask (multi-thread, production-ready)
"""
from flask import Flask, request, jsonify, send_from_directory, abort
import json
import os
import time
import sqlite3
import secrets
import requests as req_lib
import threading
import time as time_module

# ==========================================
# 💾 TRIP SHARE DATABASE (SQLite)
# ==========================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wander_trips.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, data TEXT, created_at INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT, data TEXT, error TEXT, created_at INTEGER)')
    conn.commit()
    conn.close()

def save_job_db(job_id, status, data=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?)',
                 (job_id, status, json.dumps(data) if data else None, error, int(time_module.time())))
    conn.commit()
    conn.close()

def get_job_db(job_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT status, data, error FROM jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    if not row: return None
    return {'status': row[0], 'data': json.loads(row[1]) if row[1] else None, 'error': row[2]}

def save_trip_db(trip_id, data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT OR REPLACE INTO trips VALUES (?, ?, ?)', (trip_id, json.dumps(data), int(time.time())))
    conn.commit()
    conn.close()

def get_trip_db(trip_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT data FROM trips WHERE id = ?', (trip_id,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

init_db()

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

def city_to_iata(city_name, token=None):
    clean = city_name.lower().split(',')[0].strip()
    # 1. Try static lookup first
    if clean in CITY_IATA:
        return CITY_IATA[clean]
    # 2. Try Amadeus location search API
    if token:
        try:
            r = req_lib.get(f'{AMADEUS_BASE}/v1/reference-data/locations',
                headers={'Authorization': f'Bearer {token}'},
                params={'keyword': clean, 'subType': 'CITY,AIRPORT', 'page[limit]': 1},
                timeout=5)
            data = r.json()
            if data.get('data'):
                return data['data'][0]['iataCode']
        except Exception as e:
            print(f'⚠️ IATA lookup failed for {city_name}: {e}')
    # 3. Fallback: first 3 letters uppercased
    return clean[:3].upper()

# ==========================================
# 🌐 ROUTES
# ==========================================
@app.route('/api/save-trip', methods=['POST'])
def api_save_trip():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    trip_id = secrets.token_urlsafe(5)  # ~7 char URL-safe ID
    save_trip_db(trip_id, data)
    return jsonify({"id": trip_id})

@app.route('/api/trip/<trip_id>')
def api_get_trip(trip_id):
    trip = get_trip_db(trip_id)
    if not trip:
        return jsonify({"error": "Trip not found or expired"}), 404
    return jsonify(trip)

@app.route('/trip/<trip_id>')
def trip_page(trip_id):
    # Serve the SPA — JS will fetch /api/trip/<id> on load
    return send_from_directory(DIRECTORY, 'prototype.html')

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

    origin_iata = city_to_iata(origin_city, token)
    dest_iata   = city_to_iata(dest_city, token)
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
        if not flights:
            return jsonify({"flights": [], "origin": origin_iata, "dest": dest_iata,
                            "hint": f"No flights found for {origin_iata}→{dest_iata} on {date}. Try a different date (must be future, within 1 year)."}), 200
        return jsonify({"flights": flights, "origin": origin_iata, "dest": dest_iata})

    except Exception as e:
        print(f'❌ Amadeus search error: {e}')
        return jsonify({"error": str(e)}), 500

# In-memory cache (fast access) + SQLite persistence (survives restarts)
_jobs = {}

def _cleanup_jobs():
    cutoff = time_module.time() - 900
    old = [k for k, v in _jobs.items() if v.get('created', 0) < cutoff]
    for k in old:
        _jobs.pop(k, None)

# POST: Generate new itinerary (async job queue — avoids Railway 60s timeout)
@app.route('/api/plan', methods=['POST'])
def plan_trip():
    if not wander_engine:
        return jsonify({"error": "AI engine unavailable"}), 503

    req_data = request.json
    job_id = secrets.token_urlsafe(5)[:8]
    _jobs[job_id] = {'status': 'pending', 'created': time_module.time()}
    save_job_db(job_id, 'pending')
    _cleanup_jobs()

    def run_job():
        try:
            profile = req_data.get('profile', {})
            req = req_data.get('request', {})
            print(f"🧠 Generating trip → {req.get('destination', '?')}, {req.get('duration', '?')} days")
            result = wander_engine.generate_itinerary(profile, req)
            result['id'] = int(time.time())
            result['created_at'] = time.strftime("%Y-%m-%d %H:%M")
            result['summary'] = {
                "city": req.get('destination'),
                "date": req.get('start_date') or "Anytime",
                "duration": req.get('duration')
            }
            print(f"✅ Trip generated (id={result['id']})")
            _jobs[job_id] = {'status': 'done', 'data': result, 'created': _jobs.get(job_id, {}).get('created', 0)}
            save_job_db(job_id, 'done', data=result)
        except Exception as e:
            print(f"❌ Job {job_id} failed: {e}")
            _jobs[job_id]['status'] = 'error'
            _jobs[job_id]['error'] = str(e)
            save_job_db(job_id, 'error', error=str(e))

    t = threading.Thread(target=run_job, daemon=True)
    t.start()
    return jsonify({'job_id': job_id})

@app.route('/api/plan-status/<job_id>', methods=['GET'])
def plan_status(job_id):
    # Check in-memory cache first (fast), fall back to SQLite (survives restarts)
    job = _jobs.get(job_id)
    if not job:
        job = get_job_db(job_id)
        if job:
            _jobs[job_id] = {**job, 'created': time_module.time()}  # restore to cache
    if not job:
        return jsonify({'status': 'not_found'}), 404
    resp = {'status': job['status']}
    if job['status'] == 'done':
        resp['data'] = job['data']
    elif job['status'] == 'error':
        resp['error'] = job.get('error', 'Unknown error')
    return jsonify(resp)

# POST: Generate packing list
@app.route('/api/packing-list', methods=['POST'])
def api_packing_list():
    if not wander_engine:
        return jsonify({"error": "AI unavailable"}), 503
    data = request.get_json()
    result = wander_engine.generate_packing_list(
        data.get('destination',''),
        data.get('duration', 7),
        data.get('weather_hint',''),
        data.get('profile', {}),
        data.get('language', 'English')
    )
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
