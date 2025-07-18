import streamlit as st
import os
import pandas as pd
import paho.mqtt.client as mqtt
import json
import joblib
import datetime
import queue
import requests
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from   geopy.distance import geodesic


# 🔐 User login credentials (for demo)
USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    },
    "driver001": {
        "password": "drive123",
        "role": "driver",
        "vehicle": "truck_001"
    },
    "manager": {
        "password": "manage123",
        "role": "manager"
    }
}


# 📂 Step 2: Load Model and CSV
MODEL_FILE = "fleet_model.joblib"
CSV_FILE = "fleet_data.csv"
model = joblib.load(MODEL_FILE)

# 📊 Fields used for training
required_fields = [
    "engine_temp", "battery_voltage", "speed_kmph", "tire_pressure",
    "fuel_level", "vibration", "mileage", "Packet_Rate", "Packet_Drop_Rate",
    "Packet_Duplication_Rate", "Data_Throughput", "Signal_Strength", "SNR",
    "Energy_Consumption_Rate", "Number_of_Neighbors", "Error_Rate", "CPU_Usage"
]

# 🔁 Step 3: Queue for MQTT ↔️ Streamlit
@st.cache_resource
def get_mqtt_queue():
    return queue.Queue()

mqtt_queue = get_mqtt_queue()

import requests  # already imported

# Telegram Config
TELEGRAM_TOKEN = "7557310804:AAGmvyNE0ikYV7TDFCzJPFpbPG3oET4DcjM"
CHAT_ID = "1177215273"

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, data=payload)
        if r.status_code != 200:
            print("❌ Telegram failed:", r.text)
    except Exception as e:
        print("❌ Telegram Error:", e)


# 🌐 MQTT Setup
def on_connect(client, userdata, flags, rc):
    print("✅ Connected to broker")
    client.subscribe("fleet/+/telemetry")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        vehicle_id = msg.topic.split("/")[1]
        data = [payload.get(k) for k in required_fields]

        if None in data:
            print("❌ Missing fields in payload:", payload)
            return

        X = pd.DataFrame([data], columns=required_fields)
        prediction = model.predict(X)[0]
        status = "Anomaly" if prediction == -1 else "OK"

        row = {
            "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Vehicle": vehicle_id,
            "Status": status
        }
        for i, field in enumerate(required_fields):
            row[field] = data[i]

        mqtt_queue.put(row)

        # Save to CSV
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, "a") as f:
            if not file_exists:
                f.write("Time,Vehicle,Status," + ",".join(required_fields) + "\n")
            f.write(",".join(str(row[k]) for k in row) + "\n")

        if status == "Anomaly":
            msg = (
                f"🚨 *Anomaly Detected!*\n"
                f"🚚 *Vehicle:* {vehicle_id}\n"
                f"🔥 *Engine Temp:* {payload['engine_temp']}°C\n"
                f"⚡ *Battery:* {payload['battery_voltage']}V\n"
                f"📡 *Speed:* {payload['speed_kmph']} km/h\n"
                f"🕒 Time: {row['Time']}"
            )
            send_telegram_message(msg)

        print("✅ Processed:", row)

    except Exception as e:
        print("❌ Error:", e)


# 📌 Predefined expected GPS coordinates per truck
DESTINATIONS = {
    "truck_001": (10.002, 76.282),
    "truck_002": (9.955, 76.275),
    "truck_003": (9.980, 76.220),
    # Add more trucks here
}

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        vehicle_id = msg.topic.split("/")[1]
        data = [payload.get(k) for k in required_fields]

        if None in data:
            print("❌ Missing fields in payload:", payload)
            return

        X = pd.DataFrame([data], columns=required_fields)
        prediction = model.predict(X)[0]
        status = "Anomaly" if prediction == -1 else "OK"

        row = {
            "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Vehicle": vehicle_id,
            "Status": status
        }

        for i, field in enumerate(required_fields):
            row[field] = data[i]

        mqtt_queue.put(row)

        # ✅ Save to CSV
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, "a") as f:
            if not file_exists:
                f.write("Time,Vehicle,Status," + ",".join(required_fields) + "\n")
            f.write(",".join(str(row[k]) for k in row) + "\n")

        # 🚨 Over-Speed Alert
        if payload["speed_kmph"] > 100:
            send_telegram_message(
                f"🚨 *Over-Speed Alert!*\n"
                f"🚚 *Vehicle:* {vehicle_id}\n"
                f"💨 *Speed:* {payload['speed_kmph']} km/h\n"
                f"🕒 Time: {row['Time']}"
            )

        # ⛽ Low Fuel Warning
        if payload["fuel_level"] < 15:
            send_telegram_message(
                f"⛽ *Low Fuel Warning!*\n"
                f"🚚 *Vehicle:* {vehicle_id}\n"
                f"🔋 *Fuel:* {payload['fuel_level']}%\n"
                f"🕒 Time: {row['Time']}"
            )

        # 📍 Location Deviation Alert
        if "latitude" in payload and "longitude" in payload:
            actual_location = (payload["latitude"], payload["longitude"])
            expected_location = DESTINATIONS.get(vehicle_id)

            if expected_location:
                deviation_km = geodesic(expected_location, actual_location).km
                if deviation_km > 1.0:
                    send_telegram_message(
                        f"📍 *Route Deviation Alert!*\n"
                        f"🚚 *Vehicle:* {vehicle_id}\n"
                        f"📏 *Deviation:* {deviation_km:.2f} km\n"
                        f"🕒 Time: {row['Time']}"
                    )

        # 🔁 AI Anomaly Alert
        if status == "Anomaly":
            msg = (
                f"🚨 *Anomaly Detected!*\n"
                f"🚚 *Vehicle:* {vehicle_id}\n"
                f"🔥 *Engine Temp:* {payload['engine_temp']}°C\n"
                f"⚡ *Battery:* {payload['battery_voltage']}V\n"
                f"📡 *Speed:* {payload['speed_kmph']} km/h\n"
                f"🕒 Time: {row['Time']}"
            )
            send_telegram_message(msg)

        print("✅ Processed:", row)

    except Exception as e:
        print("❌ Error:", e)         

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("test.mosquitto.org", 1883, 60)
client.loop_start()

# 🖥️ Streamlit Setup
st.set_page_config(page_title="Fleet AI Dashboard", layout="wide")
st.title("🚚 Fleet Monitoring & Predictive Maintenance")

# ⏳ Initialize session
if "fleet_history" not in st.session_state:
    st.session_state.fleet_history = pd.DataFrame(columns=["Time", "Vehicle", "Status"] + required_fields)

while not mqtt_queue.empty():
    new = mqtt_queue.get()
    st.session_state.fleet_history = pd.concat(
        [st.session_state.fleet_history, pd.DataFrame([new])],
        ignore_index=True
    )

# Session login state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Fleet Dashboard Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.vehicle = user.get("vehicle", None)
            st.success(f"✅ Logged in as {username} ({user['role']})")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()  # ⛔ Stop here unless logged in

with st.sidebar:
    st.markdown(f"👤 **User:** {st.session_state.username}")
    st.markdown(f"🔐 **Role:** {st.session_state.role}")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()




# User database
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "driver001": {"password": "drive123", "role": "driver", "vehicle": "truck_001"},
    "manager": {"password": "manage123", "role": "manager"},
}



# 🧭 Tabs
tab1, tab2, tab3, tab4 ,tab5 = st.tabs(["📡 Live Status", "📜 History", "📊 Summary", "📈 Visualizations",  "🗺️ Live GPS Map"])


role = st.session_state.role

if role == "admin":
    # show tab1, tab2, tab3 - full dashboard
    with tab1:
        ...  # Your existing real-time telemetry
    with tab2:
        ...  # History log
    with tab3:
        ...  # Live GPS map

elif role == "driver":
    with tab1:
        st.subheader("🚚 Driver View")
        df = st.session_state.fleet_history
        vehicle = st.session_state.vehicle
        df = df[df["Vehicle"] == vehicle]
        st.line_chart(df[["engine_temp", "speed_kmph", "fuel_level"]].tail(20))
        st.dataframe(df.tail(20))

elif role == "manager":
    with tab1:
        st.subheader("📊 Manager Overview")
        df = st.session_state.fleet_history.copy()
        anomaly_count = df[df["Status"] == "Anomaly"]["Vehicle"].nunique()
        st.metric("🚨 Active Anomalies", anomaly_count)
        st.dataframe(df.tail(30), use_container_width=True)


# ✅ Tab 1: Live Status
with tab1:
    st.subheader("🧠 AI Status")
    if st.session_state.fleet_history.empty:
        st.info("Waiting for data...")
    else:
        last = st.session_state.fleet_history.iloc[-1]
        if last["Status"] == "OK":
            st.success(f"✅ {last['Vehicle']} is healthy")
        else:
            st.error(f"🚨 {last['Vehicle']} anomaly detected!")

        st.line_chart(st.session_state.fleet_history[["engine_temp", "battery_voltage", "speed_kmph"]].tail(20))

    with st.sidebar:
      st.markdown("### 📲 Telegram Alert Tester")
    if st.button("Send Test Alert"):
        test_message = (
            "🚨 *Test Alert from Fleet Dashboard!*\n"
            "✅ This is a manual test to verify Telegram alerts.\n"
            f"🕒 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_telegram_message(test_message)
        st.success("Test alert sent to Telegram ✅")
    

# ✅ Tab 2: Log
with tab2:
    st.subheader("📜 Logs")
    df = st.session_state.fleet_history.copy()

    v_filter = st.selectbox("Filter by Vehicle", ["All"] + sorted(df["Vehicle"].unique()))
    if v_filter != "All":
        df = df[df["Vehicle"] == v_filter]

    s_filter = st.selectbox("Filter by Status", ["All", "OK", "Anomaly"])
    if s_filter != "All":
        df = df[df["Status"] == s_filter]

    st.dataframe(df.tail(50), use_container_width=True)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False), "fleet_log.csv")

# ✅ Tab 3: Summary Heatmap
with tab3:
    st.subheader("🔥 Anomaly Heatmap")
    df = st.session_state.fleet_history.copy()

    if df.empty:
        st.info("Waiting for data...")
    else:
        df["Time"] = pd.to_datetime(df["Time"])
        df["Hour"] = df["Time"].dt.hour
        heat_df = df[df["Status"] == "Anomaly"]

        if heat_df.empty:
            st.info("No anomalies yet.")
        else:
            pivot = heat_df.pivot_table(
                index="Vehicle", columns="Hour", values="Status",
                aggfunc="count", fill_value=0
            )
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.heatmap(pivot, annot=True, cmap="Reds", fmt=".0f", ax=ax)
            st.pyplot(fig)

# ✅ Tab 4: Visual Trends
with tab4:
    st.subheader("📈 Vehicle Trends")
    df = st.session_state.fleet_history.copy()

    if df.empty:
        st.warning("No telemetry data available yet.")
    else:
        vehicle_list = df["Vehicle"].unique().tolist()
        vehicle = st.selectbox("Select vehicle", vehicle_list)
        df = df[df["Vehicle"] == vehicle]
        df["Time"] = pd.to_datetime(df["Time"])

        fig1 = px.line(df, x="Time", y="engine_temp", title="Engine Temp Over Time")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("📊 Avg Metrics (last 20)")
        avg = df.tail(20)[["engine_temp", "battery_voltage", "speed_kmph", "fuel_level"]].mean()
        fig2 = px.bar(avg, labels={"value": "Avg", "index": "Metric"}, title="Avg Stats")
        st.plotly_chart(fig2, use_container_width=True)


with tab5:
    st.subheader("🗺️ Live Vehicle GPS Map")

    gps_df = st.session_state.fleet_history.copy()
    if "latitude" in gps_df.columns and "longitude" in gps_df.columns:
        gps_df = gps_df.dropna(subset=["latitude", "longitude"])

    else:
        st.warning("⚠️ No GPS data available to render map.")
        gps_df = pd.DataFrame(columns=["latitude", "longitude"])


    st.write("📌 Available columns in gps_df:", gps_df.columns.tolist())

    if "Time" not in gps_df.columns:
      if "timestamp" in gps_df.columns:
        gps_df["Time"] = gps_df["timestamp"]  # Rename if timestamp is present
      else:
         st.warning("⚠️ No 'Time' or 'timestamp' column in telemetry data.")
         st.stop()

         gps_df["Time"] = pd.to_datetime(gps_df["Time"], errors="coerce")
         latest_locations = gps_df.sort_values("Time").groupby("Vehicle").tail(1)


    latest_locations = gps_df.sort_values("Time").groupby("Vehicle").tail(1)
    

    if latest_locations.empty:
        st.warning("No GPS data yet.")
    else:
        latest_locations["status_color"] = latest_locations["Status"].apply(
            lambda x: "green" if x == "OK" else "red"
        )

        st.map(
            latest_locations.rename(columns={"latitude": "lat", "longitude": "lon"}),
            zoom=10
        )

        # Optional: Show data under the map
        st.dataframe(latest_locations[["Vehicle", "Time", "lat", "lon", "Status"]], use_container_width=True)
