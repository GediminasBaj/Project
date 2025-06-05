import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
import time

stations = [
    "vilniaus-ams", "kauno-ams", "klaipedos-ams", "siauliu-ams", "panevezio-ams",
    "utenos-ams", "alytaus-ams", "marijampoles-ams", "taurages-ams", "telsiu-ams"
]

API_BASE_URL = "https://api.meteo.lt/v1/stations/{}/observations/{}"

print("Įrašykite keletos dienų oro duomenų reikia:")
how_many_days = int(input()) 

end_date = datetime.utcnow().date()

if how_many_days == 1:
    start_date = end_date
else:
    start_date = end_date - timedelta(days=how_many_days - 1)

MAX_RETRIES = 5
WAIT_TIME = 5 

def fetch_station_data(station, date):
    url = API_BASE_URL.format(station, date.strftime("%Y-%m-%d"))
    retries = 0
    while retries < MAX_RETRIES:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json().get("observations", [])
            if not data:
                print(f"API negrąžino duomenų iš {station} ({date})")
                return None
            records = []
            for obs in data:
                obs_time = obs.get("observationTimeUtc")
                if not obs_time:
                    continue
                dt = datetime.strptime(obs_time, "%Y-%m-%d %H:%M:%S")
                records.append({
                    "DateTime": dt,
                    "Station": station,
                    "Temperature": obs.get("airTemperature", np.nan),
                    "FeelsLike": obs.get("feelsLikeTemperature", np.nan),
                    "WindSpeed": obs.get("windSpeed", np.nan),
                    "WindGust": obs.get("windGust", np.nan),
                    "WindDirection": obs.get("windDirection", np.nan),
                    "CloudCover": obs.get("cloudCover", np.nan),
                    "Pressure": obs.get("seaLevelPressure", np.nan),
                    "Humidity": obs.get("relativeHumidity", np.nan),
                    "Precipitation": obs.get("precipitation", np.nan)
                })
            return records
        
        elif response.status_code == 429:
            retries += 1
            wait = WAIT_TIME * retries
            print(f" 429 (Per daug užklausų) iš {station} ({date})! Laukiame {wait} sek...")
            time.sleep(wait)
        
        else:
            print(f"Klaida gaunant duomenis iš {station} ({date}): {response.status_code}")
            return None

    print(f" Stotis {station} ({date}) po {MAX_RETRIES} bandymų nepasiekiama.")
    return None

# collecting data
all_data = []

for station in tqdm(stations, desc="📡 Gaunami duomenys iš stočių"):
    for single_date in tqdm(pd.date_range(start_date, end_date), desc=f"⏳ {station}", leave=False):
        station_data = fetch_station_data(station, single_date)
        if station_data:
            all_data.extend(station_data)

# check if there is any data
if not all_data:
    print("Klaida: API negrąžino jokios informacijos. Patikrinkite API prieinamumą!")
    exit()

df = pd.DataFrame(all_data)

if "DateTime" not in df.columns:
    print("Klaida: 'DateTime' stulpelis nerastas DataFrame. Patikrinkite API struktūrą!")
    exit()

df["DateTime"] = pd.to_datetime(df["DateTime"])
df.set_index("DateTime", inplace=True)

# Pašaliname nenaudingus stulpelius (pvz., 'Station')
df = df.select_dtypes(include=[np.number])

# # grouping by time and mean for every station
df_grouped = df.groupby("DateTime").mean()

df_grouped.to_csv("lt_meteo_data.csv")
print("Meteo duomenys sėkmingai išsaugoti į 'lt_meteo_data.csv'")
