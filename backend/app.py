import os
# ตั้งค่าลดการใช้ RAM และ CPU
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

# เปิดให้เว็บภายนอกเรียกใช้ได้ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# เตรียมตัวแปรโมเดล
model = None

print("⏳ กำลังโหลดโมเดล...")
try:
    # โหลดโมเดล (ใช้ compile=False เพื่อประหยัด RAM)
    model = tf.keras.models.load_model("trash_classifier.keras", compile=False)
    print("✅ โหลดโมเดลสำเร็จ!")
except Exception as e:
    print(f"❌ โหลดไม่สำเร็จ: {e}")

# รายชื่อขยะ 12 ประเภท
class_names = [
    "battery", "biological", "brown-glass", "cardboard", "clothes", 
    "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass"
]

def get_trash_info(class_name):
    # ฟังก์ชันเลือกสีถังและคำแนะนำ
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
    if class_name in ["shoes", "clothes"]:
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

        # =========================================================
        # 🎯 ระบบโฟกัสจุดเดียว (Center Crop)
        # ตัดภาพส่วนเกินออก ให้เหลือแค่สี่เหลี่ยมจัตุรัสตรงกลาง
        # =========================================================
        width, height = image.size
        new_dim = min(width, height) # หาด้านที่สั้นที่สุด

        left = (width - new_dim)/2
        top = (height - new_dim)/2
        right = (width + new_dim)/2
        bottom = (height + new_dim)/2

        image = image.crop((left, top, right, bottom))
        # =========================================================
        
        # 2. ย่อภาพให้เหลือ 224x224 (ตามที่ AI ต้องการ)
        image = image.resize((224, 224))
        
        # 3. แปลงเป็นตัวเลข (ส่งค่า 0-255 ไปเลย เพราะโมเดลใหม่มีตัวหารข้างในแล้ว)
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0)

        # 4. ให้ AI ทายผล
        prediction = model.predict(img_array, verbose=0)[0]
        class_index = int(np.argmax(prediction))
        confidence = float(prediction[class_index]) * 100
        class_name = class_names[class_index]

        # ถ้าความมั่นใจต่ำกว่า 50% (เพราะเราครอปภาพแล้ว ควรจะมั่นใจสูงขึ้น)
        if confidence < 50.0:
            return {
                "prediction": "Unknown",
                "bin": "ไม่แน่ใจ",
                "advice": "ภาพไม่ชัด หรือขยะไม่อยู่ตรงกลาง ลองถ่ายใหม่อีกครั้งครับ"
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