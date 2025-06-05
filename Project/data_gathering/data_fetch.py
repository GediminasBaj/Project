import pandas as pd
import mysql.connector
import json
from datetime import datetime
from data_gathering import db_config

def fetch_prices_from_db():
    try:
        connection = mysql.connector.connect(**db_config.DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        today = datetime.now().date()
        cursor.execute("SELECT date, prices FROM dayahead_prices WHERE date < %s ORDER BY date ASC", (today,))
        records = cursor.fetchall()
        
        all_data = []
        for row in records:
            date = row["date"]
            prices = json.loads(row["prices"])
            for hour, price in prices.items():
                start_hour = hour.split(" - ")[0]
                timestamp = f"{date} {start_hour}"
                all_data.append({"timestamp": timestamp, "Price": price})        

        df = pd.DataFrame(all_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M", errors='coerce')
        return df.sort_values("timestamp")

    except mysql.connector.Error as err:
        print("Klaida jungiantis prie DB:", err)
        return pd.DataFrame()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_tomorrow_actual_prices():
    try:
        connection = mysql.connector.connect(**db_config.DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        tomorrow = datetime.now().date() + pd.Timedelta(days=1)
        cursor.execute("SELECT date, prices FROM dayahead_prices WHERE date = %s", (tomorrow,))
        records = cursor.fetchall()

        data = []
        for row in records:
            date = row["date"]
            prices = json.loads(row["prices"])
            for hour, price in prices.items():
                start_hour = hour.split(" - ")[0]
                timestamp = f"{date} {start_hour}"
                data.append({"timestamp": timestamp, "Price": price})
        
        if not data:
            print("Rytojaus duomenų dar nėra duomenų bazėje.")
            return pd.DataFrame(columns=["timestamp", "Price"])

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M", errors='coerce')
        return df.sort_values("timestamp")

    except mysql.connector.Error as err:
        print("Klaida imant rytojaus duomenis:", err)
        return pd.DataFrame()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# functions for RESTful API
def get_prices_between_dates(start_date=None, end_date=None):
    try:
        connection = mysql.connector.connect(**db_config.DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        if start_date and end_date:
            query = "SELECT date, prices FROM dayahead_prices WHERE date BETWEEN %s AND %s ORDER BY date ASC"
            cursor.execute(query, (start_date, end_date))
        else:
            query = "SELECT date, prices FROM dayahead_prices ORDER BY date DESC"
            cursor.execute(query)

        results = cursor.fetchall()
        return results

    except mysql.connector.Error as err:
        print("Klaida gaunant duomenis:", err)
        return []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_all_prices():
    try:
        connection = mysql.connector.connect(**db_config.DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT date, prices FROM dayahead_prices ORDER BY date DESC")
        return cursor.fetchall()

    except mysql.connector.Error as err:
        print("Klaida imant visus duomenis:", err)
        return []

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_to_database(date, region, prices):
    try:
        connection = mysql.connector.connect(**db_config.DB_CONFIG)
        cursor = connection.cursor()

        prices_json = json.dumps(prices)

        insert_query = """
        INSERT INTO dayahead_prices (date, region, prices) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE prices = VALUES(prices);
        """
        
        cursor.execute(insert_query, (date, region, prices_json))
        connection.commit()

    except mysql.connector.Error as err:
        print(f"Duomenų bazės klaida: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()