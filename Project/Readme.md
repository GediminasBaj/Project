Reikia naudoti Python 3.10 versiją, kad būtų užtikrintas LSTM modelio kodo veikimas

Šitie veiksmai nėra privalomi, bet rekomenduojami:
1. Sukurti virtualią aplinką (rekomenduojama Python 3.10)
python -m venv venv
2. Aktyvuokite(windows) - vs code terminale - project\Scripts\activate

Privalomi veiksmai:
1. Isirašykite MySQL serverį, tai galite padaryti parsisiųsdami instaliaciją iš jų puslapio - https://www.mysql.com/
2. Įsirašant MySQL serverį jūsų prašys sukurti DB_USER(duomenų bazęs vartotojo) ir password(duomenų bazės slaptažodi).
3. Sukurkite duomenų bazę, CREATE DATABASE database_name;
4. Atnaujinkite db_config savo duomenimis:
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "jūsų_vartotojas"),
        "password": os.getenv("DB_PASSWORD", "jūsų_slaptažodis"), 
        "database": os.getenv("DB_NAME", "database_name") 
    }
5. Tada sukurtoje duomenų bazėje sukurkite lentelę
    CREATE TABLE table_name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    region VARCHAR(10) NOT NULL,
    prices JSON NOT NULL,
    UNIQUE KEY unique_date_region (date, region)
);

6. Įsirašyti visas bibliotekas galite su komanda:
    pip install -r requirements.txt

7. sistema paleidžiama per main.py - ir visas valdymas vyksta tik per ten

8. Jei norite ištestuoti LSTM Modelį reikia:
    1. Oro duomenų - yra pateikiami su "lt_meteo_data.csv"
    2. Duomenų bazėje turi būti nors ~1 mėnesio elektros kainos 

Arba galite iš naujo apmokyti modelį pašalindami lstm_model.keras

<!-- Eng instruction -->
Recommended (but not mandatory) steps:
python -m venv venv

Activate the virtual environment (Windows, in VS Code terminal):
.\venv\Scripts\activate

Mandatory steps:
Install MySQL Server
1. Download the installer from the official website:
https://www.mysql.com/

2. During installation, you will be asked to create:

DB_USER (database user)

password (database password)

3. Create a database by running the following SQL:
CREATE DATABASE database_name;

4. Update db_config with your credentials:
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "your_username"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "database_name")  
}

5. Create the required table in the database:

CREATE TABLE table_name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    region VARCHAR(10) NOT NULL,
    prices JSON NOT NULL,
    UNIQUE KEY unique_date_region (date, region)
);

6. Install required Python packages:
pip install -r requirements.txt

7. Run the system using:
python main.py  - All control and functionality starts from main.py.

To test the LSTM model:

1. Weather data is required
2. Electricity prices – the database must contain at least ~1 month of day-ahead prices. 

Or you can retrain model just by renaming or removing lstm_model_keras
