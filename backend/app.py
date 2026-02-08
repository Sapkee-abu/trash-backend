from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image
import tensorflow as tf
import io

app = FastAPI()

# ==========================
# 1. เปิด CORS
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# 2. โหลดโมเดล
# ==========================================
print("Loading model...")
# ตรวจสอบว่ามีไฟล์ trash_classifier.keras อยู่ในโฟลเดอร์เดียวกัน
model = tf.keras.models.load_model("trash_classifier.keras")
print("Model loaded!")

# ==========================
# 3. ชื่อคลาส (6 ประเภท)
# ==========================================
class_names = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# ==========================
# 4. ข้อมูลคำแนะนำ
# ==========================================
trash_info = {
    "cardboard": {
        "bin": "ถังสีน้ำเงิน (รีไซเคิล)",
        "advice": "พับกล่องให้แบน หลีกเลี่ยงความชื้น"
    },
    "glass": {
        "bin": "ถังสีเขียว (แก้ว)",
        "advice": "ระวังแตก แยกฝาขวดออกก่อนทิ้ง"
    },
    "metal": {
        "bin": "ถังสีเหลือง (รีไซเคิล)",
        "advice": "เทน้ำออกให้หมด และล้างให้สะอาด"
    },
    "paper": {
        "bin": "ถังสีน้ำเงิน (กระดาษ)",
        "advice": "ต้องแห้งสนิท ห้ามเปื้อนน้ำมันหรือเศษอาหาร"
    },
    "plastic": {
        "bin": "ถังสีเหลือง (พลาสติก)",
        "advice": "บีบให้แบนเพื่อประหยัดพื้นที่ และล้างสะอาด"
    },
    "trash": {
        "bin": "ถังสีแดง หรือ สีส้ม (ขยะทั่วไป/อันตราย)",
        "advice": "ขยะปนเปื้อน หรือขยะที่ไม่สามารถรีไซเคิลได้"
    }
}

@app.get("/")
def health():
    return {"status": "API is running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # อ่านไฟล์รูปภาพ
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # ปรับขนาดภาพให้เข้ากับโมเดล (224x224)
        image = image.resize((224, 224))

        # --- จุดแก้ไขสำคัญ (ไม่ต้องหาร 255.0) ---
        # แปลงเป็น Array (ค่าจะเป็น 0-255) ส่งไปให้โมเดลได้เลย
        # เพราะโมเดลเราใส่ Layer Preprocess ไว้ข้างในแล้ว
        img_array = np.array(image)
        
        # ขยายมิติให้เป็น batch (1, 224, 224, 3)
        img_array = np.expand_dims(img_array, axis=0)

        # ทำนายผล
        prediction = model.predict(img_array)[0]

        # หาค่าที่มั่นใจที่สุด (Index)
        class_index = int(np.argmax(prediction))
        
        # ป้องกัน Error ถ้า Index เกิน
        if class_index >= len(class_names):
            class_name = "trash"
        else:
            class_name = class_names[class_index]
            
        confidence = float(prediction[class_index])

        # สร้างรายการผลทำนาย Top 3
        all_predictions = []
        for i, prob in enumerate(prediction):
            if i < len(class_names):
                all_predictions.append({
                    "class": class_names[i],
                    "confidence": round(float(prob * 100), 2)
                })

        # เรียงลำดับความมั่นใจ
        top3 = sorted(all_predictions, key=lambda x: x["confidence"], reverse=True)[:3]

        return {
            "prediction": class_name,
            "confidence": round(confidence * 100, 2),
            "bin": trash_info.get(class_name, {}).get("bin", "ไม่ระบุ"),
            "advice": trash_info.get(class_name, {}).get("advice", "-"),
            "top3": top3,
            "all_predictions": all_predictions
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}