import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OMP_NUM_THREADS'] = '1'

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

# 1. โหลดโมเดล (EfficientNet-B3 Pro)
model = None
MODEL_FILENAME = "trash_classifier_b3_pro.keras" 

print(f"⏳ Loading {MODEL_FILENAME}...")
try:
    model = tf.keras.models.load_model(MODEL_FILENAME, compile=False)
    print("✅ Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")

# 2. รายชื่อ Class
raw_class_names = [
    "battery", "brown-glass", "cardboard", "carton-drink", "cigarette",
    "clothes", "e-waste", "food-waste", "glass", "green-glass",
    "metal-can", "paper", "plastic-bag", "plastic-bottle", "plastic-cup",
    "shoes", "spray-cans", "styrofoam", "trash-general", "white-glass"
]

# 3. ระบบ Bin-Only (บอกแค่ถัง)
def get_bin_info(label):
    
    # 🔴 ถังแดง (อันตราย)
    if label in ["battery", "e-waste", "spray-cans", "cigarette"]:
        return {
            "main_title": "🔴 ถังแดง (ขยะอันตราย)", 
            "sub_title": "Hazardous Waste",
            "advice": "อันตราย! ห้ามทิ้งรวมเด็ดขาด แยกใส่ถุงแดง/ขวดปิดฝา แล้วส่งจุดรับขยะพิษ"
        }

    # 🟡 ถังเหลือง (รีไซเคิล)
    elif label in ["plastic-bottle", "plastic-cup", 
                   "paper", "cardboard", "carton-drink",
                   "metal-can", "glass", "brown-glass", "green-glass", "white-glass"]:
        return {
            "main_title": "🟡 ถังเหลือง (รีไซเคิล)", 
            "sub_title": "Recyclable Waste",
            "advice": "เทของเหลวออก ล้างให้สะอาด ทำให้แห้ง/แบน ก่อนทิ้งลงถัง"
        }

    # 🟢 ถังเขียว (ขยะเปียก)
    elif label in ["food-waste"]:
        return {
            "main_title": "🟢 ถังเขียว (ขยะเปียก)",
            "sub_title": "Organic / Food Waste",
            "advice": "กรองน้ำแกงออกให้หมด ทิ้งเฉพาะเศษอาหาร (ถุงพลาสติกห้ามทิ้งถังนี้)"
        }

    # 🔵 ถังน้ำเงิน (ทั่วไป)
    else:
        return {
            "main_title": "🔵 ถังน้ำเงิน (ขยะทั่วไป)",
            "sub_title": "General Waste",
            "advice": "ขยะเปื้อน/ย่อยสลายยาก/รีไซเคิลไม่ได้ ให้ทิ้งถังนี้\n⚠️ ข้อควรระวัง: หากเป็น Power Bank/ถ่าน ให้ทิ้งถังแดง!"
        }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None: return {"error": "Model not loaded"}
    
    try:
        # Prepare Image
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        w, h = image.size
        dim = min(w, h)
        image = image.crop(((w-dim)/2, (h-dim)/2, (w+dim)/2, (h+dim)/2))
        img_arr = np.array(image.resize((300, 300)))
        img_arr = np.expand_dims(img_arr, axis=0)

        # Predict
        pred = model.predict(img_arr, verbose=0)[0]
        idx = int(np.argmax(pred))
        conf = float(pred[idx]) * 100
        raw_label = raw_class_names[idx]

        # 🔥 แก้ตรงนี้: ปรับเกณฑ์ลงเหลือ 50.0% (จากเดิม 60.0%)
        # เพื่อให้รูปยากๆ (เช่น กระดาษขยำที่ได้ 58%) ผ่านเข้ามาได้
        if conf < 50.0:
            return {
                "prediction_th": "❓ ไม่แน่ใจ (Try Again)",
                "confidence": round(conf, 2),
                "bin": "ลองถ่ายใหม่",
                "advice": "ภาพไม่ชัด หรือ AI ไม่รู้จัก ลองขยับกล้องเข้าใกล้ๆ ครับ"
            }

        info = get_bin_info(raw_label)

        return {
            "prediction": raw_label,
            "prediction_th": info["main_title"], 
            "confidence": round(conf, 2),
            "bin": info["sub_title"],
            "advice": info["advice"]
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def health(): return {"status": "Running", "mode": "Bin-Only (Threshold 50%)"}