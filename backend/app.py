import os
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
print("⏳ Loading model...")
try:
    model = tf.keras.models.load_model("trash_classifier.keras", compile=False)
    print("✅ Model loaded!")
except Exception as e:
    print(f"❌ Error loading model: {e}")

# ชื่อภาษาอังกฤษ (ต้องตรงกับตอนเทรน)
class_names = [
    "battery", "biological", "brown-glass", "cardboard", "clothes", 
    "green-glass", "metal", "paper", "plastic", "shoes", "trash", "white-glass"
]

# ข้อมูลภาษาไทยและคำแนะนำ
trash_data = {
    "battery":     {"th": "ถ่าน/แบตเตอรี่", "bin": "ถังแดง (ขยะอันตราย)", "advice": "แยกใส่ถุงแดง/ทิ้งจุดรับขยะพิษ"},
    "biological":  {"th": "ขยะเปียก/เศษอาหาร", "bin": "ถังเขียว (ขยะเปียก)", "advice": "เทน้ำออกแล้วทิ้งถังเปียก"},
    "brown-glass": {"th": "ขวดแก้วสีชา", "bin": "ถังเขียว/แยกแก้ว", "advice": "ล้างสะอาด ระวังแตก"},
    "cardboard":   {"th": "ลังกระดาษ", "bin": "ถังเหลือง (รีไซเคิล)", "advice": "พับให้แบนก่อนทิ้ง"},
    "clothes":     {"th": "เสื้อผ้า/ผ้า", "bin": "ถังน้ำเงิน (ทั่วไป)", "advice": "บริจาคได้ถ้าสภาพดี"},
    "green-glass": {"th": "ขวดแก้วสีเขียว", "bin": "ถังเขียว/แยกแก้ว", "advice": "ล้างสะอาด ระวังแตก"},
    "metal":       {"th": "โลหะ/กระป๋อง", "bin": "ถังเหลือง (รีไซเคิล)", "advice": "เทน้ำออก บีบให้แบน"},
    "paper":       {"th": "กระดาษ", "bin": "ถังเหลือง (รีไซเคิล)", "advice": "ห้ามเปียกน้ำ"},
    "plastic":     {"th": "พลาสติก", "bin": "ถังเหลือง (รีไซเคิล)", "advice": "เทน้ำออก บีบให้แบน"},
    "shoes":       {"th": "รองเท้า", "bin": "ถังน้ำเงิน (ทั่วไป)", "advice": "ทิ้งถังทั่วไป หรือบริจาค"},
    "trash":       {"th": "ขยะทั่วไป", "bin": "ถังน้ำเงิน (ทั่วไป)", "advice": "ทิ้งถังขยะทั่วไป"},
    "white-glass": {"th": "ขวดแก้วใส", "bin": "ถังเขียว/แยกแก้ว", "advice": "ล้างสะอาด ระวังแตก"}
}

@app.get("/")
def health():
    return {"status": "Running", "model_loaded": model is not None}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None: return {"error": "Model not loaded"}
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # --- Center Crop Logic (ช่วยให้แม่นขึ้น) ---
        width, height = image.size
        new_dim = min(width, height)
        left = (width - new_dim)/2
        top = (height - new_dim)/2
        right = (width + new_dim)/2
        bottom = (height + new_dim)/2
        image = image.crop((left, top, right, bottom))
        # ----------------------------------------

        image = image.resize((224, 224))
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0)

        # ทำนายผล
        prediction = model.predict(img_array, verbose=0)[0]
        class_index = int(np.argmax(prediction))
        confidence = float(prediction[class_index]) * 100
        class_name_en = class_names[class_index]
        
        # ดึงข้อมูลภาษาไทย
        info = trash_data.get(class_name_en, trash_data["trash"])

        # ถ้าไม่มั่นใจ
        if confidence < 50.0:
            return {
                "prediction": "Unknown",
                "prediction_th": "ไม่แน่ใจ",
                "bin": "ลองถ่ายใหม่",
                "advice": "ขยับกล้องเข้ามาใกล้ๆ อีกนิดครับ"
            }

        return {
            "prediction": class_name_en,      
            "prediction_th": info["th"],      
            "confidence": round(confidence, 2),
            "bin": info["bin"],
            "advice": info["advice"]
        }
    except Exception as e:
        return {"error": str(e)}