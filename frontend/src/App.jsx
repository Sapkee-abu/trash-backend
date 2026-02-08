import { useState, useRef } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const fileInputRef = useRef(null);

  // 1. ฟังก์ชันเลือกไฟล์
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setResult(null);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
  };

  // 2. คลิกเพื่อเลือกรูป
  const triggerFileInput = () => {
    if (!loading) {
      fileInputRef.current.click();
    }
  };

  // 3. อัปโหลดและทำนายผล
  const handleUpload = async () => {
    if (!file) return;

    setLoading(true); // เริ่มอนิเมชั่น
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // หน่วงเวลา 2.5 วินาที ให้เห็นอนิเมชั่น
      const [apiResponse] = await Promise.all([
        axios.post("https://riost123-trash-api-backend.hf.space/predict", formData),
        new Promise(resolve => setTimeout(resolve, 2500))
      ]);

      console.log("Response:", apiResponse.data);

      if (apiResponse.data.error) {
        alert("แจ้งเตือนจาก Server: " + apiResponse.data.error);
      } else {
        setResult(apiResponse.data);
      }

    } catch (error) {
      console.error(error);
      alert("เชื่อมต่อ Server ไม่สำเร็จ (เช็คว่ารัน FastAPI หรือยัง)");
    } finally {
      setLoading(false); // หยุดอนิเมชั่น
    }
  };

  const handleReset = (e) => {
    e.stopPropagation();
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  // 4. เลือกสีจุดตามประเภทถังขยะ
  const getBinColor = (binText) => {
    if (!binText) return "#ccc";
    if (binText.includes("น้ำเงิน")) return "#0056b3";
    if (binText.includes("เขียว")) return "#28a745";
    if (binText.includes("เหลือง")) return "#ffc107";
    if (binText.includes("แดง") || binText.includes("ส้ม")) return "#dc3545";
    return "#6c757d";
  };

  return (
    <div className="main-container">
      <div className="glass-card">
        
        {/* --- Left Panel (รูปภาพ) --- */}
        <div className="left-panel" onClick={triggerFileInput}>
          {preview ? (
            // class 'scanning' จะเรียกอนิเมชั่นใหม่
            <div className={`image-wrapper ${loading ? "scanning" : ""}`}>
              <img src={preview} alt="Upload" className="uploaded-image" />
              {!loading && (
                <div className="image-overlay">
                  <span>แตะเพื่อเปลี่ยนรูป</span>
                </div>
              )}
            </div>
          ) : (
            <div className="upload-placeholder">
              <div className="icon-circle">📸</div>
              <h3>เลือกรูปภาพขยะ</h3>
              <p>คลิกบริเวณนี้เพื่ออัปโหลด</p>
            </div>
          )}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            capture="environment"
            style={{ display: "none" }} 
          />
        </div>

        {/* --- Right Panel (ผลลัพธ์) --- */}
        <div className="right-panel">
          <div className="header-text">
            <h1>Trash AI ♻️</h1>
            <p>ระบบแยกขยะอัจฉริยะ</p>
          </div>

          <div className="result-area">
            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div> 
                <h2>กำลังวิเคราะห์...</h2>
              </div>
            ) : result ? (
              <div className="result-card fade-in">
                <div className="prediction-badge">
                  {result.prediction || "Unknown"}
                </div>
                
                <div className="stat-row">
                  <span>ความมั่นใจ</span>
                  <strong>{result.confidence}%</strong>
                </div>
                
                <div className="stat-row">
                  <span>ถังขยะ</span>
                  <div className="bin-container">
                    <span 
                      className="bin-color-dot" 
                      style={{ backgroundColor: getBinColor(result.bin) }}
                    ></span>
                    <strong>{result.bin}</strong>
                  </div>
                </div>
                
                <div className="advice-box">
                  <small>คำแนะนำ:</small>
                  <p>{result.advice}</p>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>👈 เลือกรูปทางซ้าย</p>
                <p>เพื่อเริ่มใช้งาน</p>
              </div>
            )}
          </div>

          <div className="action-buttons">
            <button
              className="btn-primary"
              onClick={handleUpload}
              disabled={loading || !file}
            >
              {loading ? "กำลังสแกน..." : "🔍 ทำนายผล"}
            </button>
            
            {preview && !loading && (
              <button className="btn-secondary" onClick={handleReset}>
                เริ่มใหม่
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;