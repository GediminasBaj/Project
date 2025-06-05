import subprocess
import threading
import time
import datetime, json
import pytz
import sys # for running scripts through virtual env
from data_gathering import data_fetch
import pandas as pd
TEST = False
TEST_INTERVAL = 0.5

def fetch_and_compare():
    print("Pradedamas duomenų atnaujinimo tikrinimas.")

    from data_gathering.get_nord_pool_prices_LT import get_nordpool_prices_dict

    price_dict = get_nordpool_prices_dict()
    if not price_dict:
        print("Nepavyko gauti naujų kainų.")
        return

    price_date = datetime.date.today() + datetime.timedelta(days=1)

    existing_prices = data_fetch.fetch_tomorrow_actual_prices()

    # converting to DataFrame
    new_prices = pd.DataFrame([
        {
            "timestamp": datetime.datetime.strptime(f"{price_date} {hour.split(' - ')[0]}", "%Y-%m-%d %H:%M"),
            "Price": price
        }
        for hour, price in price_dict.items()
    ])

    if existing_prices.empty:
        print("Prieš tai nebuvo jokių duomenų – įrašoma naujos kainos.")
        data_fetch.save_to_database(price_date, "LT", price_dict)
        return

    # comparing
    new_prices = new_prices.sort_values("timestamp").reset_index(drop=True)
    existing_prices = existing_prices.sort_values("timestamp").reset_index(drop=True)

    if not existing_prices["Price"].equals(new_prices["Price"]):
        print("Skirtumas tarp kainų rastas – atnaujinami duomenys.")
        data_fetch.save_to_database(price_date, "LT", price_dict)
        print("Kainos atnaujintos.")
    else:
        print("Kainos atitinka – jokių pakeitimų nereikia.")

# Run NordPool electricity gathering continously
def run_nordpool():
    lithuania_time = pytz.timezone('Europe/Vilnius')
    MAX_RETRIES = 5
    RETRY_DELAY_MINUTES = 15

    while True:
        now = datetime.datetime.now(lithuania_time)
        if now.hour < 14:
            next_run = now.replace(hour=14, minute=0, second=0, microsecond=0)
            sleep_sec = (next_run - now).total_seconds()
            print(f"Surinkimas prasidės 14:00 ({now.strftime('%H:%M')}), laukiam iki {next_run.strftime('%H:%M')}")
            time.sleep(sleep_sec)
            continue

        print("\nTikrinama, ar duomenų bazėje yra rytojaus kainos")
        tomorrow_price = data_fetch.fetch_tomorrow_actual_prices()
        if not tomorrow_price.empty:
            print("Kainos jau yra – laukiame kitos dienos.")
        else:
            print("Kainų dar nėra, bandoma gauti.")
            for attempt in range(1, MAX_RETRIES + 1):
                print(f"[{attempt}/{MAX_RETRIES}] Bandoma paleisti kainų gavimo skriptą.")
                try:
                    subprocess.run([sys.executable, "data_gathering/get_nord_pool_prices_LT.py"], check=True)
                    time.sleep(10)

                    tomorrow_price = data_fetch.fetch_tomorrow_actual_prices()
                    if not tomorrow_price.empty:
                        print("Kainos įrašytos sėkmingai.")
                        break
                except subprocess.CalledProcessError as e:
                    print(f"Klaida paleidžiant skriptą: {e}")

                if attempt < MAX_RETRIES:
                    print(f"Laukiama {RETRY_DELAY_MINUTES} min iki kito bandymo.")
                    time.sleep(RETRY_DELAY_MINUTES * 60)
                else:
                    print("Nepavyko gauti kainų – bus bandoma vėliau.")

        if now.hour < 16:
            next_run = now.replace(hour=16, minute=0, second=0, microsecond=0)
            print("Laukiam iki 16:00 papildomam tikrinimui.")
        else:
            next_run = now.replace(hour=14, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            print(f"Kainų tikrinimas baigtas. Kitas bandymas: {next_run.strftime('%Y-%m-%d %H:%M')}")

        time.sleep((next_run - now).total_seconds())

        # comparing prices
        now = datetime.datetime.now(lithuania_time)
        if 14 <= now.hour < 17:
            try:
                fetch_and_compare()
            except Exception as e:
                print(f"Klaida atliekant tikrinimą: {e}")

def run_flask():
    print("Jungiamas API serveris")
    # flask_process = subprocess.run(["python", "app.py"])
    flask_process = subprocess.Popen([sys.executable, "restful_api/app.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return flask_process

# Get meteo when needed
def run_meteo():
    # subprocess.run(["python", "data_gathering/get_meteo_data.py"])
    subprocess.run([sys.executable, "data_gathering/get_meteo_data.py"])

def run_lstm_prediction():
    # subprocess.run(["python", "train_LSTM.py"])
    subprocess.run([sys.executable, "train_LSTM.py"])

def main():
    thread = threading.Thread(target=run_nordpool, daemon=True)
    thread.start()

    print("Įrašykite\n 'orai', kad gautumėt orų duomenis\n 'apmokyti' kad būtų apmokomas LSTM modelis\n 'prideti_rakta' - sugeneruoti naujam vartotojui priėjimo prie RESTful API raktą\n 'baigti', kad programa išsijugntų.")

    while True:
        user_input = input(">>>").strip().lower()
        if user_input == "orai":
            print("Gaunami meterologiniai duomenys...")
            run_meteo()
            print("Duomenis gauti.")
        elif user_input == "apmokyti":
            print("LSTM modelis įjungtas.")
            run_lstm_prediction()
            print("Rezultatai pateikti.")
        elif user_input == "baigti":
            print("Programa išjungta.")
            break
        elif user_input == "prideti_rakta":
            username = input("Įveskite vartotojo vardą: ")
            key = input("Įveskite vartotojo API raktą (arba paspauskite Enter, kad būtų sugeneruotas automatiškai): ")
            if not key:
                import secrets
                key = secrets.token_urlsafe(24)
                print(f"Generuotas raktas: {key}")
            from restful_api.api_key_generator import generate_and_save_key
            generate_and_save_key(username, key)
            print("Raktas pridėtas.")
        else:
            print("Įrašykite 'orai', kad gautumėt orų duomenis\n 'apmokyti' kad būtų apmokomas LSTM modelis\n prideti_rakta - sugeneruoti naujam vartotojui priėjimo prie RESTful API raktą\n 'baigti', kad programa išsijugntų.")

if __name__ == "__main__":
    run_flask()
    time.sleep(2)
    main()