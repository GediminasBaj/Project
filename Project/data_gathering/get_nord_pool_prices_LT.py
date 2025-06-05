from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tabulate import tabulate
import datetime
from data_gathering import data_fetch

def get_nordpool_prices():
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode (no UI)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get('https://data.nordpoolgroup.com/auction/day-ahead/prices?deliveryDate=latest&currency=EUR&aggregation=DeliveryPeriod&deliveryAreas=LT')

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/app-root/div/div/div[2]/app-day-ahead-prices/div/grid-wrapper/div/div[1]/dx-data-grid/div/div[7]/div/div/div/div/table/tbody'))
        )

        # Getting LT region name
        region_xpath = "//table/tbody/tr[1]/td[2]"
        region_name = driver.find_element(By.XPATH, region_xpath).text.strip()
        region_name = region_name.replace(" (EUR)", "") 

        prices = {}  # Dictionary to store JSON data
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)  # Get tomorrow's date

        for i in range(1, 25):  
            try:
                time_xpath = f'/html/body/app-root/div/div/div[2]/app-day-ahead-prices/div/grid-wrapper/div/div[1]/dx-data-grid/div/div[7]/div/div/div/div/table/tbody/tr[{i}]/td[1]'
                price_xpath = f'/html/body/app-root/div/div/div[2]/app-day-ahead-prices/div/grid-wrapper/div/div[1]/dx-data-grid/div/div[7]/div/div/div/div/table/tbody/tr[{i}]/td[2]'

                time_period = driver.find_element(By.XPATH, time_xpath).text
                price = float(driver.find_element(By.XPATH, price_xpath).text.replace(',', '.'))

                prices[time_period] = price

            except Exception as e:
                print(f"Klaida gaunant informacija iš eilutės {i}: {e}")

        driver.quit()

        print(tabulate(prices.items(), headers=["Laikas", "Kaina"], tablefmt="grid"))

        # Save to MySQL
        data_fetch.save_to_database(tomorrow, region_name, prices)

    except Exception as e:
        print(f"Error: {e}")
        driver.quit()

# funckija tik kainų lyginimui ir neįrašimui į duomenų bazę
def get_nordpool_prices_dict():
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get('https://data.nordpoolgroup.com/auction/day-ahead/prices?deliveryDate=latest&currency=EUR&aggregation=DeliveryPeriod&deliveryAreas=LT')

    prices = {}
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/app-root/div/div/div[2]/app-day-ahead-prices/div/grid-wrapper/div/div[1]/dx-data-grid/div/div[7]/div/div/div/div/table/tbody'))
        )

        for i in range(1, 25):
            try:
                time_xpath = f'/html/body/app-root/div/div/div[2]/app-day-ahead-prices/div/grid-wrapper/div/div[1]/dx-data-grid/div/div[7]/div/div/div/div/table/tbody/tr[{i}]/td[1]'
                price_xpath = f'/html/body/app-root/div/div/div[2]/app-day-ahead-prices/div/grid-wrapper/div/div[1]/dx-data-grid/div/div[7]/div/div/div/div/table/tbody/tr[{i}]/td[2]'

                time_period = driver.find_element(By.XPATH, time_xpath).text
                price = float(driver.find_element(By.XPATH, price_xpath).text.replace(',', '.'))

                prices[time_period] = price
            except Exception as e:
                print(f"Klaida eilutėje {i}: {e}")

    except Exception as e:
        print(f"Klaida kraunant puslapį: {e}")
    finally:
        driver.quit()

    return prices

if __name__ == "__main__":
    get_nordpool_prices()
