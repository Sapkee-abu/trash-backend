from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image
import tensorflow as tf
import io

app = FastAPI()

# เปิด CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading model...")
model = tf.keras.models.load_model("trash_classifier.keras")
print("Model loaded!")

class_names = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# --- 1. แก้ไขคำแนะนำให้เหมาะสมขึ้น ---
trash_info = {
    "cardboard": {
        "bin": "ถังรีไซเคิล (กระดาษ/ลัง)",
        "advice": "พับให้แบนเพื่อประหยัดพื้นที่"
    },
    "glass": {
        "bin": "ถังขยะแก้ว (สีเขียว)",
        "advice": "ระวังแตก! แยกฝาขวดพลาสติกออกก่อนทิ้ง"
    },
    "metal": {
        "bin": "ถังรีไซเคิล (โลหะ/อลูมิเนียม)",
        "advice": "เทน้ำออกให้หมด บีบกระป๋องถ้าทำได้"
    },
    "paper": {
        "bin": "ถังรีไซเคิล (กระดาษ)",
        "advice": "ต้องแห้งสนิท ไม่เปื้อนน้ำมันหรือเศษอาหาร"
    },
    "plastic": {
        "bin": "ถังรีไซเคิล (พลาสติก)",
        "advice": "เทของเหลวออกให้หมด แยกฉลาก/ฝา ถ้าแยกได้"  # แก้จากบีบ เป็นเน้นความสะอาด
    },
    "trash": {
        "bin": "ถังขยะทั่วไป (สีแดง/ส้ม)",
        "advice": "ขยะเปื้อน ขยะกำพร้า หรือที่ไม่สามารถรีไซเคิลได้"
    }
}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Resize
        image = image.resize((224, 224))
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0)

        # --- 2. จุดเช็ค Preprocessing (สำคัญมาก) ---
        # ถ้าผลลัพธ์มั่วมาก ให้ลองเปิดบรรทัดข้างล่างนี้ (หาร 255) แล้วรันใหม่
        # img_array = img_array / 255.0  

        prediction = model.predict(img_array)[0]
        class_index = int(np.argmax(prediction))
        confidence = float(prediction[class_index]) * 100  # แปลงเป็น %

        print(f"Pred: {class_names[class_index]} ({confidence:.2f}%)") # Log ดูหลังบ้าน

        # --- 3. ระบบกันหน้าแตก (Threshold) ---
        # ถ้าความมั่นใจต่ำกว่า 60% ให้ตอบว่าไม่แน่ใจ
        if confidence < 60.0:
            return {
                "prediction": "Unknown",
                "confidence": round(confidence, 2),
                "bin": "ไม่แน่ใจ / ขยะทั่วไป",
                "advice": "ภาพไม่ชัด หรือเป็นขยะที่ไม่รู้จัก ลองถ่ายใหม่ หรือทิ้งถังทั่วไป",
                "top3": []
            }

        # ถ้า Index เกิน
        if class_index >= len(class_names):
            class_name = "trash"
        else:
            class_name = class_names[class_index]

        # สร้าง Top 3
        all_predictions = []
        for i, prob in enumerate(prediction):
            if i < len(class_names):
                all_predictions.append({
                    "class": class_names[i],
                    "confidence": round(float(prob * 100), 2)
                })
        
        top3 = sorted(all_predictions, key=lambda x: x["confidence"], reverse=True)[:3]

        return {
            "prediction": class_name,
            "confidence": round(confidence, 2),
            "bin": trash_info.get(class_name, {}).get("bin", "ไม่ระบุ"),
            "advice": trash_info.get(class_name, {}).get("advice", "-"),
            "top3": top3
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}