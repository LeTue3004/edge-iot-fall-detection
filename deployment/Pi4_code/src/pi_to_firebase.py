import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

import base64
from PIL import Image
import io
import os


# ============= 1. KHỞI TẠO FIREBASE =============

def init_firebase():
    cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://iotproject-c4618-default-rtdb.firebaseio.com/"
    })

    print("✅ Đã khởi tạo Firebase (Realtime Database)")


# ============= 2. HÀM MÃ HOÁ ẢNH THÀNH BASE64 =============

def encode_image_to_base64(image_path, max_width=320, quality=60):
    """
    Đọc ảnh từ image_path, resize nhỏ lại cho nhẹ, rồi encode base64.
    Trả về string base64 (utf-8).
    """
    if not os.path.exists(image_path):
        print(f"⚠️ Không tìm thấy file ảnh: {image_path}")
        return None

    img = Image.open(image_path)

    # Resize theo chiều rộng max_width để giảm dung lượng
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size)

    # Lưu ảnh vào bộ nhớ tạm kiểu JPEG
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    img_bytes = buffer.getvalue()

    # Encode base64 → string
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    return img_b64


# ============= 3. GỬI ALERT + ẢNH LÊN 'data' =============

def send_alert(alert_type, image_path=None):
    """
    Gửi 1 bản ghi cảnh báo lên Realtime Database.
    Nếu có image_path → gửi thêm field 'imageBase64'.
    """

    ref = db.reference("data1")

    payload = {
        "type": alert_type,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    if image_path is not None:
        img_b64 = encode_image_to_base64(image_path)
        if img_b64 is not None:
            payload["imageUrl"] = img_b64
        else:
            print("⚠️ Không gửi được ảnh, chỉ gửi dữ liệu text.")

    new_ref = ref.push(payload)
    print(f"✅ Đã gửi alert: key = {new_ref.key}")
    # print("Data gửi lên:", {k: (str(v)[:50] + '...' if k == 'imageBase64' else v)
    #                        for k, v in payload.items()})


# ============= 4. VÍ DỤ TEST =============

def test_fall_with_image():
    # Ảnh Pi chụp được, ví dụ đã lưu sẵn:
    image_path = "/home/pi/Desktop/camera_project/photo.jpg"
    send_alert("fall", image_path=image_path)


def test_person_no_image():
    send_alert("person", image_path=None)


if __name__ == "__main__":
    init_firebase()

    # Test: NGÃ kèm ảnh
    test_fall_with_image()
