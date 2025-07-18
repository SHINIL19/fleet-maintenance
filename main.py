import paho.mqtt.client as mqtt  
import json
import time
import random

# List of fleet vehicle IDs
FLEET = ["truck_001", "truck_002", "truck_003"]

# MQTT broker details
BROKER = "test.mosquitto.org"
PORT = 1883

# Create MQTT client
client = mqtt.Client()
client.connect(BROKER, PORT, 60)

# Function to simulate 17 AI parameters
def generate_ai_data(vehicle_id):
    return {
        "vehicle_id": vehicle_id,
        "engine_temp": round(random.uniform(70, 120), 2),
        "battery_voltage": round(random.uniform(11.5, 14.8), 2),
        "speed_kmph": round(random.uniform(40, 100), 2),
        "tire_pressure": round(random.uniform(28, 36), 2),
        "fuel_level": round(random.uniform(10, 100), 2),
        "vibration": round(random.uniform(0.1, 2.0), 2),
        "mileage": round(random.uniform(30000, 120000), 1),
        "Packet_Rate": round(random.uniform(40, 90), 2),
        "Packet_Drop_Rate": round(random.uniform(0.1, 5.0), 3),
        "Packet_Duplication_Rate": round(random.uniform(0.0, 2.0), 3),
        "Data_Throughput": round(random.uniform(80, 150), 2),
        "Signal_Strength": round(random.uniform(-90, -30), 2),
        "SNR": round(random.uniform(5, 30), 2),
        "Energy_Consumption_Rate": round(random.uniform(1.0, 10.0), 3),
        "Number_of_Neighbors": random.randint(1, 10),
        "Error_Rate": round(random.uniform(0.0, 0.5), 3),
        "CPU_Usage": round(random.uniform(10, 90), 2)
    }

# Infinite publish loop
while True:
    for vehicle in FLEET:
        topic = f"fleet/{vehicle}/telemetry"
        payload = generate_ai_data(vehicle)
        client.publish(topic, json.dumps(payload))
        print(f"📡 Published to {topic} ➤ {payload}")
        time.sleep(2)
