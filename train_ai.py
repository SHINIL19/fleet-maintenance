import pandas as pd # type: ignore
from sklearn.covariance import EllipticEnvelope # type: ignore
import joblib # type: ignore

# 1. Load the fleet data
CSV_FILE = "fleet_data.csv"
print("📄 Loading fleet telemetry data...")
df = pd.read_csv(CSV_FILE)

# 2. Select the exact features used for training
features = [
    "engine_temp", "battery_voltage", "speed_kmph", "tire_pressure",
    "fuel_level", "vibration", "mileage",
    "Packet_Rate", "Packet_Drop_Rate", "Packet_Duplication_Rate",
    "Data_Throughput", "Signal_Strength", "SNR",
    "Energy_Consumption_Rate", "Number_of_Neighbors",
    "Error_Rate", "CPU_Usage"
]

# 3. Extract features for training
X = df[features]

# 4. Train the model
print("🧠 Training Elliptic Envelope model...")
model = EllipticEnvelope(contamination=0.10, random_state=42)
model.fit(X)

# 5. Save the model
joblib.dump(model, "fleet_model.joblib")
print("✅ Model trained and saved as 'fleet_model.joblib'")
