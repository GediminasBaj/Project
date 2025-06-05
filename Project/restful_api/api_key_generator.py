import bcrypt
import json

def generate_and_save_key(username, raw_api_key):
    hashed = bcrypt.hashpw(raw_api_key.encode(), bcrypt.gensalt()).decode()

    try:
        with open("users_keys.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    data[username] = hashed

    with open("users_keys.json", "w") as file:
        json.dump(data, file, indent=4)

    print(f"Raktas sukurtas naudotojui {username}. Saugojamas hash.")