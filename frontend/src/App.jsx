import { useState, useRef } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // สร้าง Ref แยก 2 อัน (อัลบั้ม vs กล้อง)
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // 1. ฟังก์ชันเลือกไฟล์ (ใช้ร่วมกัน)
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setResult(null);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
  };

  // 2.1 กดปุ่มอัลบั้ม
  const triggerFileInput = (e) => {
    e.stopPropagation();
    if (!loading) fileInputRef.current.click();
  };

  // 2.2 กดปุ่มกล้อง (จะเปิดกล้องเลยใน Android/iOS)
  const triggerCameraInput = (e) => {
    e.stopPropagation();
    if (!loading) cameraInputRef.current.click();
  };

  // 3. อัปโหลดไป Backend
  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // หน่วงเวลาหลอกๆ 2.5 วิ ให้เห็นอนิเมชั่นสวยๆ
      const [apiResponse] = await Promise.all([
        axios.post("https://riost123-trash-api-backend.hf.space/predict", formData),
        new Promise(resolve => setTimeout(resolve, 2500))
      ]);

      console.log("Response:", apiResponse.data);

      if (apiResponse.data.error) {
        alert("Server Error: " + apiResponse.data.error);
      } else {
        setResult(apiResponse.data);
      }

    } catch (error) {
      console.error(error);
      alert("เชื่อมต่อ Server ไม่สำเร็จ (เช็ค Backend หรือเน็ต)");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = (e) => {
    e.stopPropagation();
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  // เลือกสีตามผลลัพธ์
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
        
        {/* --- Left Panel (ส่วนรูปภาพ) --- */}
        <div className="left-panel">
          
          {preview ? (
            <div className={`image-wrapper ${loading ? "scanning" : ""}`}>
              <img src={preview} alt="Upload" className="uploaded-image" />
              {!loading && (
                <div className="image-overlay">
                  <button onClick={triggerFileInput} className="overlay-btn">📂 เปลี่ยนรูป</button>
                  <button onClick={triggerCameraInput} className="overlay-btn">📸 ถ่ายใหม่</button>
                </div>
              )}
            </div>
          ) : (
            // หน้าจอเลือกวิธีอัปโหลด (แสดง 2 ปุ่ม)
            <div className="upload-placeholder">
              <h3>เลือกวิธีการสแกน</h3>
              <div className="upload-options">
                
                {/* ปุ่ม 1: อัลบั้ม */}
                <div className="option-card" onClick={triggerFileInput}>
                  <div className="icon-circle">📂</div>
                  <p>อัลบั้ม</p>
                </div>

                {/* ปุ่ม 2: กล้อง */}
                <div className="option-card" onClick={triggerCameraInput}>
                  <div className="icon-circle">📸</div>
                  <p>ถ่ายรูป</p>
                </div>

              </div>
              <p style={{marginTop: '20px', fontSize: '0.9rem'}}>คลิกเพื่อเริ่มใช้งาน</p>
            </div>
          )}

          {/* Input ซ่อน 1: อัลบั้ม */}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            style={{ display: "none" }} 
          />

          {/* Input ซ่อน 2: กล้อง (capture="environment") */}
          <input 
            type="file" 
            ref={cameraInputRef} 
            onChange={handleFileChange} 
            accept="image/*"
            capture="environment" 
            style={{ display: "none" }} 
          />
        </div>

        {/* --- Right Panel (ส่วนผลลัพธ์) --- */}
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
                <p> เลือกวิธีอัปโหลด </p>
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