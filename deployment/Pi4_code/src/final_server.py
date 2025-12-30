#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==================================================
# STANDARD LIB
# ==================================================
import os
import io
import time
import threading
from datetime import datetime
import base64

# ==================================================
# THIRD-PARTY
# ==================================================
from flask import Flask, request, Response
from PIL import Image
import numpy as np
import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db
import tflite_runtime.interpreter as tflite

# ==================================================
# CONFIG
# ==================================================
MODEL_PATH = "/home/pi/Desktop/camera_project/model/mobilenetv2_qat_int8 copy.tflite"
SERVICE_ACCOUNT = "/home/pi/Desktop/camera_project/serviceAccountKey.json"
DATABASE_URL = "https://iotproject-c4618-default-rtdb.firebaseio.com/"

IMAGE_SAVE_PATH = "photo_rotate.jpg"

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "fall_detection/status"

THRESHOLD = 0.5

# ==================================================
# INIT FLASK
# ==================================================
app = Flask(__name__)

# ==================================================
# INIT MQTT (ROBUST)
# ==================================================
mqtt_client = mqtt.Client(client_id="pi4_fall_publisher", clean_session=True)

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with rc={rc}")

def on_publish(client, userdata, mid):
    print(f"[MQTT] Message published (mid={mid})")

mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish
mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

def mqtt_loop():
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()
print("[SYSTEM] MQTT loop started")

# ==================================================
# INIT FIREBASE
# ==================================================
cred = credentials.Certificate(SERVICE_ACCOUNT)
firebase_admin.initialize_app(cred, {
    "databaseURL": DATABASE_URL
})
print("[SYSTEM] Firebase initialized")

# ==================================================
# LOAD TFLITE MODEL
# ==================================================
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("[SYSTEM] TFLite model loaded")

# ==================================================
# UTILS
# ==================================================
def encode_image_to_base64(img: Image.Image, max_width=320, quality=60):
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# ==================================================
# MQTT ALERT
# ==================================================
def send_mqtt_alert(result: str):
    payload = "1" if result == "fall" else "0"
    mqtt_client.publish(MQTT_TOPIC, payload, qos=1)
    print(f"[MQTT] Alert sent: {payload}")

# ==================================================
# FIREBASE ALERT
# ==================================================
def send_firebase_alert(result: str, img: Image.Image):
    ref = db.reference("data1")
    payload = {
        "type": result,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "imageUrl": encode_image_to_base64(img)
    }
    ref.push(payload)
    print("[FIREBASE] Alert pushed")

# ==================================================
# PREDICTION
# ==================================================
def predict(img: Image.Image) -> str:
    input_shape = input_details[0]["shape"]  # [1, H, W, C]
    img = img.resize((input_shape[2], input_shape[1]))
    input_data = np.array(img)

    dtype = input_details[0]["dtype"]
    scale, zero_point = input_details[0]["quantization"]

    if dtype in (np.uint8, np.int8):
        input_data = input_data / 255.0
        input_data = input_data / scale + zero_point
        input_data = input_data.astype(dtype)
    else:
        input_data = input_data.astype(np.float32) / 255.0

    input_data = np.expand_dims(input_data, axis=0)

    start = time.time()
    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]["index"])
    infer_time = (time.time() - start) * 1000

    out_scale, out_zero = output_details[0]["quantization"]
    prob = (output.astype(np.float32) - out_zero) * out_scale
    prob = float(prob[0][0])

    result = "fall" if prob > THRESHOLD else "not fall"

    print(f"[AI] prob={prob:.4f} | result={result} | {infer_time:.2f} ms")
    return result

# ==================================================
# ASYNC ALERT HANDLER
# ==================================================
def async_alert(result, img):
    send_firebase_alert(result, img)
    send_mqtt_alert(result)

# ==================================================
# API ENDPOINT
# ==================================================
@app.route("/upload", methods=["POST"])
def upload():
    try:
        img = Image.open(io.BytesIO(request.data)).convert("RGB")

        # Rotate 180°
        img = img.rotate(180, expand=True)

        # Optional: save for debug
        img.save(IMAGE_SAVE_PATH)

        result = predict(img)

        threading.Thread(
            target=async_alert,
            args=(result, img),
            daemon=True
        ).start()

        return Response("OK", status=200)

    except Exception as e:
        print("[ERROR]", e)
        return Response("ERROR", status=500)

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    print("[SYSTEM] Server started on port 5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)
