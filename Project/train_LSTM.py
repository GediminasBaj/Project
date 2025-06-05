import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import os
from data_gathering import data_fetch  

# getting data 
electricity_prices = data_fetch.fetch_prices_from_db()
meteo_data = pd.read_csv('lt_meteo_data.csv', parse_dates=['DateTime'])
meteo_data.rename(columns={'DateTime': 'timestamp'}, inplace=True)

# weather and electricity prices data joining
electricity_prices['timestamp'] = electricity_prices['timestamp'].dt.floor('h')
meteo_data['timestamp'] = meteo_data['timestamp'].dt.floor('h')
data = pd.merge(electricity_prices, meteo_data, on='timestamp', how='inner')

# Time-based features to better capture cycles and seasonality
data['day_of_year'] = data['timestamp'].dt.dayofyear
data['month'] = data['timestamp'].dt.month
data['weekday'] = data['timestamp'].dt.weekday
data['hour'] = data['timestamp'].dt.hour
data['day_sin'] = np.sin(2 * np.pi * data['day_of_year'] / 365)
data['day_cos'] = np.cos(2 * np.pi * data['day_of_year'] / 365)
data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24)
data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24)

#  Normalization 
features = [col for col in data.columns if col not in ['timestamp', 'Price']]
scaler = MinMaxScaler()
data[features] = scaler.fit_transform(data[features])

price_scaler = MinMaxScaler()
data['Price'] = price_scaler.fit_transform(data[['Price']])

# Sequence creation 
def create_sequences(data, target_column, seq_length, forecast_horizon=24):
    X, y = [], []
    for i in range(len(data) - seq_length - forecast_horizon + 1):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length:i+seq_length+forecast_horizon, target_column])
    return np.array(X), np.array(y)

seq_length = 24 * 28
forecast_horizon = 24
X, y = create_sequences(data[features + ['Price']].values, -1, seq_length, forecast_horizon)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# LSTM model
model_path = 'lstm_model.keras'
if os.path.exists(model_path):
    print("Įkeliamas egzistuojantis modelis.")
    model = load_model(model_path)
else:
    print("Apmokomas naujas modelis")
    model = Sequential([
        LSTM(256, return_sequences=True, input_shape=(seq_length, X.shape[2])),
        Dropout(0.3),
        LSTM(256),
        Dropout(0.3),
        Dense(128, activation='relu'),
        Dense(64, activation='relu'),
        Dense(forecast_horizon)
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0003), loss='mean_squared_error')
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=50, batch_size=32,
              callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)])
    model.save(model_path)
    print("Modelis išsaugotas.")

# test 
predictions = model.predict(X_test)
predictions = price_scaler.inverse_transform(predictions.reshape(-1, 1))
actual = price_scaler.inverse_transform(y_test.reshape(-1, 1))

mae = mean_absolute_error(actual, predictions)
rmse = np.sqrt(mean_squared_error(actual, predictions))
smape = lambda a, p: np.mean(2 * np.abs(a - p) / (np.abs(a) + np.abs(p) + 1e-8)) * 100
print(f"\nTikslumas:\n MAE={mae:.2f},\n RMSE={rmse:.2f},\n SMAPE={smape(actual, predictions):.2f}%")

# next day prediction 
latest_data = np.array([data[features + ['Price']].values[-seq_length:]])
tomorrow_pred = model.predict(latest_data)
tomorrow_prices = price_scaler.inverse_transform(tomorrow_pred.reshape(-1, 1)).flatten()

# diagrams 
plt.figure(figsize=(12, 6))
plt.plot(actual, label='Tikros kainos', linewidth=2, color='blue')
plt.plot(predictions, label='Prognozės', linestyle='dashed', linewidth=2, color='orange')
plt.title("Testavimo laikotarpio tikros vs prognozuotos kainos")
plt.xlabel("Laikas (valandomis)")
plt.ylabel("Kaina (€)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# comparing actual prices with prediction
plt.figure(figsize=(10, 5))
plt.plot(range(24), tomorrow_prices, marker='x', linestyle='dashed', label='Prognozė', color='orange')
tomorrows_price = data_fetch.fetch_tomorrow_actual_prices()
if not tomorrows_price.empty:
    tomorrow_actual_prices = tomorrows_price['Price'].values
    plt.plot(range(24), tomorrow_actual_prices, marker='o', label='Faktinė kaina', color='blue')

    # results
    mae_tomorrow = mean_absolute_error(tomorrow_actual_prices, tomorrow_prices)
    rmse_tomorrow = np.sqrt(mean_squared_error(tomorrow_actual_prices, tomorrow_prices))
    smape_tomorrow = smape(tomorrow_actual_prices, tomorrow_prices)

    print(f"\nRytojaus palyginimo rezultatai:")
    print(f"MAE: {mae_tomorrow:.2f}")
    print(f"RMSE: {rmse_tomorrow:.2f}")
    print(f"SMAPE: {smape_tomorrow:.2f}%")
else:
    print("Rytojaus kainos nerastos duomenų bazėje.")

plt.title("Rytojaus kainų palyginimas: Faktas vs Prognozė")
plt.xlabel("Valanda")
plt.ylabel("Kaina (€)")
plt.xticks(range(24), [f"{h}:00" for h in range(24)], rotation=45)
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()