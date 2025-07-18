# 🚛 AI-Powered Fleet Monitoring & Predictive Maintenance System

Welcome to a next-gen Fleet Monitoring Dashboard built with **Python**, **Streamlit**, **MQTT**, and **AI** — a full-stack real-time system that tracks, analyzes, and predicts the health of logistics vehicles 🚚 in the field using live telemetry, anomaly detection, Telegram alerts, and more!

---

## 🔧 Technologies Used

- **Python** 🐍
- **Streamlit** (for interactive dashboards)
- **paho-mqtt** (real-time MQTT messaging)
- **Scikit-learn** (AI model - Elliptic Envelope)
- **Joblib** (model serialization)
- **Pandas / NumPy / Seaborn / Plotly** (data handling and visualization)
- **Geopy** (distance-based route deviation detection)
- **Telegram Bot API** (alerts)
- **Mosquitto Public Broker** (MQTT over `test.mosquitto.org`)

---

## 📦 Project Modules

### ✅ 1. MQTT-Based Telemetry Simulator (`main.py`)
Simulates live data from multiple vehicles (e.g., `truck_001`, `truck_002`, etc.) and publishes structured telemetry JSON payloads to MQTT topics like:


## fleet/<vehicle_id>/telemetry
Published data includes:
- GPS location
- Speed
- Engine temp
- Battery voltage
- Tire pressure
- Fuel level
- Vibration
- Mileage

---

### ✅ 2. Streamlit Real-Time Dashboard (`fleet_dashboard.py`)
A full-featured interactive UI built in Streamlit that:
- Subscribes to MQTT topics
- Parses telemetry data
- Feeds data to an AI model
- Renders beautiful dashboards

**Tabs Include:**
- 📡 **Live Telemetry View**
- 📜 **Logs and History**
- 🔥 **Anomaly Heatmap**
- 📈 **Vehicle Trend Graphs**
- 🗺️ **Live Fleet GPS Map**

---

### ✅ 3. AI Anomaly Detection Model (`train_ai.py`)
Trains an **Elliptic Envelope** model using historical fleet data with the following fields:
- `engine_temp`, `battery_voltage`, `speed_kmph`, `fuel_level`, `vibration`, etc.

Generates: `fleet_model.joblib`

---

### ✅ 4. Telegram Bot Integration
Smart alerts pushed directly to Telegram on:
- 🚨 AI-detected anomalies
- ⚠️ Speed violations (>100 km/h)
- ⛽ Low fuel levels (<15%)
- 📍 Route deviations (>1km from target)

---

### ✅ 5. Role-Based Dashboard Login
Simple login screen built into Streamlit with hardcoded credentials:
```python
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "driver": {"password": "driver123", "role": "driver"},
}
