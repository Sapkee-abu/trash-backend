import { useState, useRef } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setResult(null);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://127.0.0.1:8000/predict", formData);
      setResult(res.data);
    } catch (error) {
      alert("เชื่อมต่อ AI ไม่สำเร็จ");
      console.error(error);
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

  return (
    <div className="main-container">
      <div className="glass-card">
        
        {/* --- LEFT PANEL --- */}
        <div className="left-panel" onClick={triggerFileInput}>
          {preview ? (
            <div className="image-wrapper">
              <img src={preview} alt="Upload" className="uploaded-image" />
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
            style={{ display: "none" }}
          />
        </div>

        {/* --- RIGHT PANEL --- */}
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
                <div className="prediction-badge">{result.prediction}</div>
                <div className="stat-row">
                  <span>ความมั่นใจ</span>
                  <strong>{result.confidence}%</strong>
                </div>
                <div className="stat-row">
                  <span>ถังขยะ</span>
                  <strong>{result.bin}</strong>
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
              {loading ? "กำลังทำงาน..." : "🔍 ทำนายผล"}
            </button>
            
            {preview && (
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