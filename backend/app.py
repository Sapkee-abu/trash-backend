from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image
import tensorflow as tf
import io

app = FastAPI()

# ==========================
# เปิด CORS
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ตอน deploy จริงควรใส่ domain frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# โหลดโมเดล
# ==========================
print("Loading model...")
model = tf.keras.models.load_model("trash_classifier.keras")
print("Model loaded!")

# ==========================
# คลาส (ต้องเรียงตามตอน train)
# ==========================
class_names = ["cardboard", "glass", "metal", "paper", "plastic"]

# ==========================
# ข้อมูลถังขยะ
# ==========================
trash_info = {
    "cardboard": {
        "bin": "ถังสีน้ำเงิน",
        "advice": "พับให้แบนก่อนทิ้ง และต้องแห้ง"
    },
    "glass": {
        "bin": "ถังสีเขียว",
        "advice": "ระวังแตกก่อนทิ้ง"
    },
    "metal": {
        "bin": "ถังสีเหลือง",
        "advice": "ควรล้างก่อนรีไซเคิล"
    },
    "paper": {
        "bin": "ถังสีน้ำเงิน",
        "advice": "ห้ามเปียกน้ำก่อนทิ้ง"
    },
    "plastic": {
        "bin": "ถังสีเหลือง",
        "advice": "ล้างให้สะอาดก่อนทิ้ง"
    }
}

# ==========================
# Health Check (สำคัญตอน deploy)
# ==========================
@app.get("/")
def health():
    return {"status": "API is running"}

# ==========================
# Predict Endpoint
# ==========================
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = image.resize((224, 224))

        img_array = np.array(image) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)[0]

        # confidence สูงสุด
        class_index = int(np.argmax(prediction))
        class_name = class_names[class_index]
        confidence = float(prediction[class_index])

        # สร้างเปอร์เซ็นทุกคลาส
        all_predictions = []
        for i, prob in enumerate(prediction):
            all_predictions.append({
                "class": class_names[i],
                "confidence": round(float(prob * 100), 2)
            })

        # เรียง top 3
        top3 = sorted(all_predictions, key=lambda x: x["confidence"], reverse=True)[:3]

        return {
            "prediction": class_name,
            "confidence": round(confidence * 100, 2),
            "bin": trash_info[class_name]["bin"],
            "advice": trash_info[class_name]["advice"],
            "top3": top3,
            "all_predictions": all_predictions
        }

    except Exception as e:
        return {
            "error": str(e)
        }
