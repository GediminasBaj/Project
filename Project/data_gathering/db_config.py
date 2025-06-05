# Tai duomenų bazės nustatymų failas
# pakeiskite savo duomenimis
# patartina naudoti saugų slaptažodį
#   
#  Naudokite šiuos kintamuosius: 
# - DB_HOST (default: localhost)
# - DB_USER (default: nordpool_db_admin)
# - DB_PASSWORD (default: 1234)  # geriau naudoti saugesnį
# - DB_NAME (default: nordpool_prices)
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "nordpool_db_admin"),
    "password": os.getenv("DB_PASSWORD", "1234"),  # slaptažodis testavimui, sistemos panaudojimui naudoti saugensį!
    "database": os.getenv("DB_NAME", "nordpool_prices")
}

