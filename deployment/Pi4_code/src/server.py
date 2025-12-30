from flask import Flask, request
import tflite_runtime.interpreter as tflite
import numpy as np
from PIL import Image
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

app = Flask(__name__)

# Load model
interpreter = tflite.Interpreter(model_path="/home/pi/Desktop/camera_project/model/mobilenetv2_qat_int8.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def send_email(result, image_path):
    sender_email = "levantue30042004@gmail.com"
    receiver_email = "letue30042004@gmail.com"
    password = "ehxg xvfx qzwl hgco"  # dùng App Password, không dùng mật khẩu thường

    subject = "Fall Detection Alert"
    body = f"Kết quả dự đoán: {result}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Nội dung text
    msg.attach(MIMEText(body, "plain"))

    # Đính kèm ảnh
    with open(image_path, "rb") as f:
        img_data = f.read()
    image = MIMEImage(img_data, name="photo.jpg")
    msg.attach(image)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email đã được gửi thành công!")
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")

# Hàm dự đoán
def predict(image_path):
    img = Image.open(image_path).convert("RGB")

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

    # Thêm batch dimension
    input_data = np.expand_dims(input_data, axis=0)

    # Inference và đo thời gian
    start_time = time.time()
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
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

    classes = ["No Fall", "Fall"]

    print(f"Output raw (quantized): {output}")
    print(f"Dequantized probability: {prob:.4f}")
    print(f"Threshold: {THRESHOLD}")
    print(f"Predicted class: {classes[pred_class]}")
    print(f"Inference time: {(end_time-start_time)*1000:.2f} ms")


    # # Gửi email thông báo
    # send_email(result, image_path)

# Test với ảnh có sẵn
image_path = "/home/pi/Desktop/camera_project/not_fall.jpg"
predict(image_path)

@app.route('/upload', methods=['POST'])
def upload():
    with open("photo.jpg", "wb") as f:
        f.write(request.data)
    predict("photo.jpg")   # chạy dự đoán ngay và gửi mail
    return "OK"

app.run(host="0.0.0.0", port=5000)
