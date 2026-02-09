import os
# ตั้งค่าให้ TensorFlow ใช้ทรัพยากรน้อยที่สุด (ป้องกัน RAM เต็ม)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
os.environ['TF_NUM_INTEROP_THREADS'] = '1'

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image
import tensorflow as tf
import io

app = FastAPI()

# เปิดให้หน้าเว็บภายนอกเชื่อมต่อได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตัวแปรโมเดล
model = None

print("⏳ กำลังโหลดโมเดล...")
try:
    # โหลดโมเดล (ใช้ compile=False เพื่อความเร็วและประหยัด RAM)
    model = tf.keras.models.load_model("trash_classifier.keras", compile=False)
    print("✅ โหลดโมเดลสำเร็จ!")
except Exception as e:
    print(f"❌ โหลดไม่สำเร็จ: {e}")

# ชื่อคลาส 12 ประเภท (เรียงตามตัวอักษรตามที่ Colab บอก)
class_names = [
    "battery", "biological", "brown-glass", "cardboard", "clothes", 
    "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass"
]

def get_trash_info(class_name):
    if "glass" in class_name:
        return {"bin": "ถังสีเขียว (แยกแก้ว)", "advice": "🍾 ขวดแก้ว: เทน้ำออก ล้างให้สะอาด ระวังแตก"}
    if class_name in ["cardboard", "paper"]:
        return {"bin": "ถังสีเหลือง (รีไซเคิล)", "advice": "📦 กระดาษ: พับให้แบน อย่าให้เปียกน้ำ"}
    if class_name in ["metal", "plastic"]:
        return {"bin": "ถังสีเหลือง (รีไซเคิล)", "advice": "♻️ รีไซเคิล: เทเศษอาหารออก (ซองขนมทิ้งรวมได้)"}
    if class_name == "battery":
        return {"bin": "ถังสีแดง (ขยะอันตราย)", "advice": "⛔ อันตราย: แยกใส่ถุงแดงหรือทิ้งจุดรับขยะพิษ"}
    if class_name == "biological":
        return {"bin": "ถังสีเขียว (ขยะเปียก)", "advice": "🍂 ขยะเปียก: แยกทิ้งถังขยะเปียกหรือหมักปุ๋ย"}
    if class_name == "shoes" or class_name == "clothes":
        return {"bin": "ถังสีน้ำเงิน (ทั่วไป)", "advice": "👕 เสื้อผ้า/รองเท้า: บริจาคได้ถ้าสภาพดี หรือทิ้งถังทั่วไป"}
    return {"bin": "ถังสีน้ำเงิน (ทั่วไป)", "advice": "🗑️ ขยะทั่วไป: หากสภาพดีบริจาคได้ หรือทิ้งถังทั่วไป"}

@app.get("/")
def health():
    return {"status": "Running", "model_loaded": model is not None}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded. Try restarting the space."}
    
    try:
        # 1. อ่านรูปภาพ
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 2. ปรับขนาดให้เป็น 224x224
        image = image.resize((224, 224))
        
        # 3. แปลงเป็นตัวเลข (เอา / 255.0 ออกแล้ว เพราะโมเดลมีชั้น Rescaling แล้ว)
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0) # เพิ่มมิติเป็น (1, 224, 224, 3)

        # 4. ทำนายผล
        prediction = model.predict(img_array, verbose=0)[0]
        class_index = int(np.argmax(prediction))
        confidence = float(prediction[class_index]) * 100
        class_name = class_names[class_index]

        # ถ้าความมั่นใจต่ำกว่า 40% ให้บอกว่าไม่แน่ใจ
        if confidence < 40.0:
            return {
                "prediction": "Unknown",
                "bin": "ไม่แน่ใจ",
                "advice": "ภาพไม่ชัด ลองถ่ายใหม่อีกครั้งครับ"
            }

        info = get_trash_info(class_name)
        return {
            "prediction": class_name,
            "confidence": round(confidence, 2),
            "bin": info["bin"],
            "advice": info["advice"]
        }
    except Exception as e:
        return {"error": str(e)}
