import json
import bcrypt
import time

def verify_api_key(authorization_header):
    if not authorization_header:
        print("[ERROR] Authorization header nerastas")
        return None

    if not authorization_header.startswith("Bearer "):
        print("[ERROR] Authorization format turėtų prasidėti 'Bearer '")
        return None
    try:
        token = authorization_header[len("Bearer "):] 
        username, provided_key = token.split(":", 1)
    except ValueError:
        print("[ERROR] Authorization format turėtų būti: Bearer Vartotojas:APIraktas")
        return None

    with open("users_keys.json", "r") as file:
        keys = json.load(file)

    if username not in keys:
        print(f"[ERROR] Vartotojas '{username}' nerastas.")
        return None

    hashed_key = keys[username]

    start = time.time()
    if bcrypt.checkpw(provided_key.encode(), hashed_key.encode()):
        return username
    else:
        print(f"[FAIL] Raktas neteisingas vartotojui: {username}")
        return None



