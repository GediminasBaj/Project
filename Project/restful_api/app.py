# Code for RESTful API
import json
import sys
import os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, jsonify, request, g
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from api_keys_checker import verify_api_key
from data_gathering import data_fetch
from datetime import datetime

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

load_dotenv()
API_KEY_HASH = os.getenv("API_KEY_HASH")

app = Flask(__name__)

def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def get_verified_username():
    auth_header = request.headers.get("Authorization")
    username = verify_api_key(auth_header)
    g.username = username 
    return username or get_remote_address()

# Limit
limiter = Limiter(
    key_func=get_verified_username,
    app=app,
    default_limits=["100 per hour"]
)

@app.route('/api/prices', methods=['GET'])
def get_prices():
    username = getattr(g, "username", None)
    if not username:
        return jsonify({"klaida": "Nepatvirtintas prisijungimas. Neteisingas API RAKTAS"}), 401

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if (start_date and not validate_date(start_date)) or (end_date and not validate_date(end_date)):
        return jsonify({"klaida": "Neteisingas datos formatas. Naudokite YYYY-MM-DD"}), 400

    try:
        if start_date and end_date:
            results = data_fetch.get_prices_between_dates(start_date, end_date)
        else:
            results = data_fetch.get_all_prices()

        if results:
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "date": result["date"],
                    "prices": json.loads(result["prices"])
                })
            return jsonify(formatted_results)
        else:
            return jsonify({"klaida": "Duomenų nėra"}), 404

    except Exception as err:
        return jsonify({"klaida": str(err)}), 500

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)

