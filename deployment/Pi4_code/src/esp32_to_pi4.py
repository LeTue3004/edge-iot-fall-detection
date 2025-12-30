from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import base64
from PIL import Image
import io
import os
import numpy as np
import tflite_runtime.interpreter as tflite

# ---- FIREBASE ----
from datetime import datetime
import base64
import io
# MQTT
import paho.mqtt.client as mqtt
import time
# MQTT CONFIG
# ==================================================
MQTT_HOST = "localhost"     # hoặc IP Pi4
MQTT_PORT = 1883
MQTT_TOPIC = "fall_detection/status"

mqtt_client = mqtt.Client("pi4_fall_publisher")
mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
# mqtt_client.loop_start()
import threading

def mqtt_loop():
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

print("MQTT connected!")

# ==================================================
# 1. KHỞI TẠO FLASK
# ==================================================
app = Flask(__name__)

# ==================================================
# 2. KHỞI TẠO FIREBASE
# ==================================================
# Dùng file serviceAccountKey.json để xác thực
cred = credentials.Certificate("/home/pi/Desktop/camera_project/serviceAccountKey.json")
# kết nối tới Realtime Database
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://iotproject-c4618-default-rtdb.firebaseio.com/"
})

print("Firebase ready!")

# ==================================================
# 3. LOAD TFLITE MODEL
# ==================================================
interpreter = tflite.Interpreter(
    model_path="/home/pi/Desktop/camera_project/model/mobilenetv2_qat_int8 copy.tflite"
)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("Model loaded!")

# ==================================================
# MQTT ALERT
# ==================================================
def send_mqtt_alert(result):
    if result == "fall":
        mqtt_client.publish(MQTT_TOPIC, "1", qos=1)
        print("MQTT: ALERT ON (Fall)")
    else:
        mqtt_client.publish(MQTT_TOPIC, "0", qos=1)
        print("MQTT: ALERT OFF (No Fall)")


# ==================================================
# 4. HÀM MÃ HOÁ ẢNH BASE64
# ==================================================
def encode_image_to_base64(image_path, max_width=320, quality=60):
    if not os.path.exists(image_path):
        return None
    
    img = Image.open(image_path)

    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    img_bytes = buffer.getvalue()

    return base64.b64encode(img_bytes).decode("utf-8")


# ==================================================
# 5. GỬI ALERT LÊN FIREBASE
# ==================================================
def send_alert(result, image_path=None):
    ref = db.reference("data1")

    payload = {
        "type": result,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    if image_path is not None:
        img_b64 = encode_image_to_base64(image_path)
        if img_b64:
            payload["imageUrl"] = img_b64

    new_ref = ref.push(payload)
    print(f"Firebase push OK: key={new_ref.key}")


# ==================================================
# 6. HÀM DỰ ĐOÁN
# ==================================================
def predict(img):
    # img = Image.open(image_path).convert("RGB")

    # Resize theo input của mô hình
    input_shape = input_details[0]['shape']  # [1, H, W, C]
    img_resized = img.resize((input_shape[2], input_shape[1]))  # width, height

    # Chuyển sang numpy array
    input_data = np.array(img_resized)

    # Kiểm tra dtype của input
    input_dtype = input_details[0]['dtype']
    if input_dtype == np.int8 or input_dtype == np.uint8:
        scale, zero_point = input_details[0]['quantization']
        input_data = input_data / 255.0           # normalize 0..1
        input_data = input_data / scale + zero_point
        input_data = input_data.astype(input_dtype)
    else:
        input_data = input_data.astype(np.float32) / 255.0

    # Thêm batch dimension, thêm chiều batch
    input_data = np.expand_dims(input_data, axis=0)

    # Inference và đo thời gian
    start_time = time.time()
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke() # chạy inference
    output = interpreter.get_tensor(output_details[0]['index'])
    end_time = time.time()
    output_scale, output_zero_point = output_details[0]['quantization']

    if output_details[0]['dtype'] in (np.uint8, np.int8):
        prob = (output.astype(np.float32) - output_zero_point) * output_scale
        prob = float(prob[0][0])
    else:
        # Float model
        prob = float(output[0][0])

    # ==== Threshold (KHÔNG hard-code 0.5 cho INT8) ====
    THRESHOLD = 0.5   # bạn có thể tune: 0.25–0.4

    pred_class = 1 if prob > THRESHOLD else 0

    classes = ["not fall", "fall"]

    print(f"Output raw (quantized): {output}")
    print(f"Dequantized probability: {prob:.4f}")
    print(f"Threshold: {THRESHOLD}")
    print(f"Predicted class: {classes[pred_class]}")
    print(f"Inference time: {(end_time-start_time)*1000:.2f} ms")
    return classes[pred_class]

# ==================================================
# 7. ENDPOINT NHẬN ẢNH
# ==================================================
@app.route("/upload", methods=["POST"])
def upload():
    print("Receiving image...")
    # Đọc bytes ảnh từ ESP32
    image_bytes = request.data
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # ===== XOAY 180 ĐỘ =====
    img = img.rotate(180, expand=True)
    # Lưu ảnh đã xoay
    img.save("photo_rotate.jpg", format="JPEG")

    print("📸 Photo saved!")

    # Dự đoán
    result = predict(img)

    # Gửi lên Firebase
    send_alert(result, "photo_rotate.jpg")

    # Gửi MQTT alert
    send_mqtt_alert(result)
    return "OK"


# ==================================================
# 8. RUN SERVER
# ==================================================
app.run(host="0.0.0.0", port=5000)
