import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dots, setDots] = useState([]);
  const wrapperRef = useRef(null);
  
  // State สำหรับ Popup
  const [showCredits, setShowCredits] = useState(false);
  const [showGuide, setShowGuide] = useState(false);

  useEffect(() => {
    if (!loading) {
      setDots([]);
      return;
    }

    const interval = setInterval(() => {
      const wrapperWidth = wrapperRef.current?.offsetWidth || 1000;
      const batch = [];
      for (let i = 0; i < 25; i++) {
        const size = wrapperWidth * 0.0008 + Math.random() * wrapperWidth * 0.0008;
        batch.push({
          id: Math.random(),
          top: Math.random() * 100,
          left: Math.random() * 100,
          size,
          duration: 2000 + Math.random() * 2000
        });
      }
      setDots(prev => [...prev, ...batch]);
      batch.forEach(dot => {
        setTimeout(() => {
          setDots(prev => prev.filter(d => d.id !== dot.id));
        }, dot.duration);
      });
    }, 16);

    return () => clearInterval(interval);
  }, [loading]);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setResult(null);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
  };

  const triggerFileInput = (e) => {
    e.stopPropagation();
    if (!loading) fileInputRef.current.click();
  };

  const triggerCameraInput = (e) => {
    e.stopPropagation();
    if (!loading) cameraInputRef.current.click();
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
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
        {/* --- Left Panel --- */}
        <div className="left-panel">
          {preview ? (
            <div ref={wrapperRef} className={`image-wrapper ${loading ? "scanning" : ""}`}>
              <img src={preview} alt="Upload" className="uploaded-image" />
              {loading && (
                <div className="dot-layer">
                  {dots.map(dot => (
                    <span
                      key={dot.id}
                      className="magic-dot"
                      style={{
                        top: `${dot.top}%`,
                        left: `${dot.left}%`,
                        width: `${dot.size}px`,
                        height: `${dot.size}px`,
                        animationDuration: `${dot.duration}ms`
                      }}
                    />
                  ))}
                </div>
              )}
              {!loading && (
                <div className="image-overlay">
                  <button onClick={triggerFileInput} className="overlay-btn">📂 เปลี่ยนรูป</button>
                  <button onClick={triggerCameraInput} className="overlay-btn">📸 ถ่ายใหม่</button>
                </div>
              )}
            </div>
          ) : (
            <div className="upload-placeholder">
              <h3>เลือกวิธีการสแกน</h3>
              <div className="upload-options">
                <div className="option-card" onClick={triggerFileInput}>
                  <div className="icon-circle">📂</div>
                  <p>อัลบั้ม</p>
                </div>
                <div className="option-card" onClick={triggerCameraInput}>
                  <div className="icon-circle">📸</div>
                  <p>ถ่ายรูป</p>
                </div>
              </div>
              <p style={{marginTop: '20px', fontSize: '0.9rem'}}>คลิกเพื่อเริ่มใช้งาน</p>
            </div>
          )}
          <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" style={{ display: "none" }} />
          <input type="file" ref={cameraInputRef} onChange={handleFileChange} accept="image/*" capture="environment" style={{ display: "none" }} />
        </div>

        {/* --- Right Panel --- */}
        <div className="right-panel">
          <div className="header-row">
            <div className="header-text">
              <h1>Trash AI ♻️</h1>
              <p>ระบบแยกขยะอัจฉริยะ</p>
            </div>
            <div className="top-icons">
               <button className="icon-btn guide-btn" onClick={() => setShowGuide(true)} title="คู่มือการแยกขยะ ">
                 📖
               </button>
               <button className="icon-btn info-btn" onClick={() => setShowCredits(true)} title="ผู้จัดทำ">
                 ℹ️
               </button>
            </div>
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
                    <span className="bin-color-dot" style={{ backgroundColor: getBinColor(result.bin) }}></span>
                    <strong>{result.bin}</strong>
                  </div>
                </div>
                <div className="advice-box">
                  <small>คำแนะนำ:</small>
                  <p>{result.advice}</p>
                  <p>EfficientNet-B3 Model</p>
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
          <p className="model-tag">🚀 AI Model: EfficientNet-B3</p>
        </div>
      </div>

      {/* Modal: Credits */}
      {showCredits && (
        <div className="modal-overlay" onClick={() => setShowCredits(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>👨‍💻 คณะผู้จัดทำ</h3>
              <button className="close-btn" onClick={() => setShowCredits(false)}>×</button>
            </div>
            <ul className="member-list">
              <li>
                <span className="id">67100511</span>
                <span className="name">ทรัพย์กีร์ อาบู</span>
              </li>
              <li>
                <span className="id">67115873</span>
                <span className="name">อนุสรณ์ สมาน</span>
              </li>
              <li>
                <span className="id">67129007</span>
                <span className="name">สิรวิชญ์ เพชรจำรัส</span>
              </li>
              <li>
                <span className="id">67116228 </span>
                <span className="name">ชนินทร เพ็งจิตร</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Modal: Guide */}
      {showGuide && (
        <div className="modal-overlay" onClick={() => setShowGuide(false)}>
          <div className="modal-content guide-modal" onClick={e => e.stopPropagation()}>
             <div className="modal-header">
              <h3>📖 คู่มือการแยกขยะ </h3>
              <button className="close-btn" onClick={() => setShowGuide(false)}>×</button>
            </div>
            <div className="guide-grid">
              <div className="guide-item yellow">
                <span className="guide-icon">🟡</span>
                <h4>ถังเหลือง (รีไซเคิล)</h4>
                <p>ขวดพลาสติก, แก้ว, กระดาษ, โลหะ (ล้างก่อนทิ้ง)</p>
              </div>
              <div className="guide-item green">
                <span className="guide-icon">🟢</span>
                <h4>ถังเขียว (ขยะเปียก)</h4>
                <p>เศษอาหาร, เปลือกผลไม้, ใบไม้ (ย่อยสลายได้)</p>
              </div>
              <div className="guide-item red">
                <span className="guide-icon">🔴</span>
                <h4>ถังแดง (อันตราย)</h4>
                <p>ถ่านไฟฉาย, หลอดไฟ, กระป๋องสเปรย์, ยาหมดอายุ</p>
              </div>
              <div className="guide-item blue">
                <span className="guide-icon">🔵</span>
                <h4>ถังน้ำเงิน (ทั่วไป)</h4>
                <p>ถุงพลาสติกเปื้อน, โฟม, ทิชชู่ (รีไซเคิลไม่ได้)</p>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;