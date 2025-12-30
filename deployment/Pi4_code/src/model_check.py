import tflite_runtime.interpreter as tflite
import numpy as np
from PIL import Image
import time

# =====================================================
# CONFIG
# =====================================================
MODEL_PATH = "/home/pi/Desktop/camera_project/model/mobilenetv2_qat_int8.tflite"
IMAGE_PATH = "/home/pi/Desktop/camera_project/not_fall_check1.jpg"

THRESHOLD = 0.50   # tune: 0.25 – 0.4

# =====================================================
# LOAD MODEL
# =====================================================
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("====== MODEL INFO ======")
print("Input details :", input_details)
print("Output details:", output_details)
print("========================\n")

# =====================================================
# PREPROCESS
# =====================================================
def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")

    _, height, width, _ = input_details[0]['shape']
    img = img.resize((width, height))

    input_data = np.array(img, dtype=np.float32) / 255.0

    scale, zero_point = input_details[0]['quantization']
    input_dtype = input_details[0]['dtype']

    if input_dtype == np.uint8:
        input_data = input_data / scale + zero_point
        input_data = np.clip(input_data, 0, 255)
        input_data = input_data.astype(np.uint8)

    elif input_dtype == np.int8:
        input_data = input_data / scale + zero_point
        input_data = np.clip(input_data, -128, 127)
        input_data = input_data.astype(np.int8)

    else:
        input_data = input_data.astype(np.float32)

    input_data = np.expand_dims(input_data, axis=0)

    print("Input dtype:", input_data.dtype)
    print("Input min/max:", input_data.min(), input_data.max())

    return input_data

# =====================================================
# INFERENCE
# =====================================================
input_data = preprocess_image(IMAGE_PATH)

start_time = time.time()
interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()
output = interpreter.get_tensor(output_details[0]['index'])
end_time = time.time()

# =====================================================
# DEQUANTIZE OUTPUT
# =====================================================
output_scale, output_zero_point = output_details[0]['quantization']
output_dtype = output_details[0]['dtype']

if output_dtype in (np.uint8, np.int8):
    prob = (output.astype(np.float32) - output_zero_point) * output_scale
    prob = float(prob[0][0])
else:
    prob = float(output[0][0])

# =====================================================
# DECISION
# =====================================================
pred_class = 1 if prob > THRESHOLD else 0
classes = ["No Fall", "Fall"]

# =====================================================
# LOG
# =====================================================
print("\n====== RESULT ======")
print("Raw output (quantized):", output)
print("Dequantized prob     :", f"{prob:.4f}")
print("Threshold            :", THRESHOLD)
print("Prediction           :", classes[pred_class])
print("Inference time       :", f"{(end_time - start_time)*1000:.2f} ms")
print("====================\n")
