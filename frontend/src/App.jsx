import { useState, useRef, useCallback } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000/api";

function CircleGauge({ value, label, color }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 120 120" className="gauge-svg">
        <circle cx="60" cy="60" r={r} className="gauge-track" />
        <circle
          cx="60" cy="60" r={r}
          className="gauge-fill"
          stroke={color}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
        />
        <text x="60" y="55" textAnchor="middle" className="gauge-val">{Math.round(value)}%</text>
        <text x="60" y="72" textAnchor="middle" className="gauge-label">{label}</text>
      </svg>
    </div>
  );
}

function BatchResultCard({ item, index }) {
  const isReal = item.label === "REAL";
  return (
    <div className={`batch-card ${isReal ? "real" : "fake"}`} style={{ animationDelay: `${index * 0.06}s` }}>
      {item.error ? (
        <div className="batch-error">⚠ {item.error}</div>
      ) : (
        <>
          <div className="batch-filename">{item.filename}</div>
          <div className={`batch-verdict ${isReal ? "real" : "fake"}`}>{item.label}</div>
          <div className="batch-conf">{(item.confidence * 100).toFixed(1)}%</div>
          <div className="batch-scores">
            <span>M1: {(item.model1_score * 100).toFixed(1)}%</span>
            <span>M2: {(item.model2_score * 100).toFixed(1)}%</span>
          </div>
          {item.heatmap && (
            <div className="heatmap-section" style={{ marginTop: 10 }}>
              <p className="heatmap-title">GradCAM</p>
              <img src={`data:image/png;base64,${item.heatmap}`} alt="heatmap" className="heatmap-img" />
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState("single");
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchPreviews, setBatchPreviews] = useState([]);
  const [result, setResult] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [includeHeatmap, setIncludeHeatmap] = useState(false);
  const [includeBatchHeatmap, setIncludeBatchHeatmap] = useState(false);
  const fileRef = useRef();
  const batchRef = useRef();

  const handleFile = (f) => {
    setFile(f);
    setResult(null);
    setError(null);
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const handleBatchFiles = (files) => {
    const arr = Array.from(files);
    setBatchFiles(arr);
    setBatchPreviews(arr.map(f => URL.createObjectURL(f)));
    setBatchResult(null);
    setError(null);
  };

  const detect = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("include_heatmap", includeHeatmap);
      const res = await fetch(`${API_BASE}/detect`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Detection failed");
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const detectBatch = async () => {
    if (!batchFiles.length) return;
    setLoading(true);
    setError(null);
    setBatchResult(null);
    try {
      const fd = new FormData();
      batchFiles.forEach(f => fd.append("files", f));
      fd.append("include_heatmap", includeBatchHeatmap);
      const res = await fetch(`${API_BASE}/batch`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Batch failed");
      setBatchPreviews([]);
      setBatchResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const clearBatch = () => {
    setBatchFiles([]);
    setBatchPreviews([]);
    setBatchResult(null);
    setError(null);
  };

  const isReal = result?.label === "REAL";

  return (
    <div className="app">
      <div className="orb orb1" />
      <div className="orb orb2" />
      <div className="orb orb3" />

      <header className="header">
        <div className="logo-mark">
          <svg viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="18" stroke="url(#lg)" strokeWidth="2"/>
            <path d="M12 20 Q20 10 28 20 Q20 30 12 20Z" fill="url(#lg)" opacity="0.8"/>
            <defs>
              <linearGradient id="lg" x1="0" y1="0" x2="40" y2="40">
                <stop stopColor="#00ffe0"/>
                <stop offset="1" stopColor="#7b2fff"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div className="header-text">
          <h1 className="site-title">FORENSIQ</h1>
          <p className="site-sub">AI Image Detection Engine</p>
        </div>
        <div className="mode-toggle">
          <button className={mode === "single" ? "active" : ""} onClick={() => { setMode("single"); setResult(null); setError(null); }}>Single</button>
          <button className={mode === "batch" ? "active" : ""} onClick={() => { setMode("batch"); setBatchResult(null); setBatchPreviews([]); setBatchFiles([]); setError(null); }}>Batch</button>
        </div>
      </header>

      <main className="main">
        {mode === "single" && (
          <div className="single-layout">
            <div
              className={`drop-zone ${dragging ? "dragging" : ""} ${preview ? "has-preview" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current.click()}
            >
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={e => e.target.files[0] && handleFile(e.target.files[0])} />
              {preview ? (
                <div className="preview-wrap">
                  <img src={preview} alt="preview" className="preview-img" />
                  <div className="preview-overlay"><span>Change Image</span></div>
                </div>
              ) : (
                <div className="drop-inner">
                  <div className="drop-icon">
                    <svg viewBox="0 0 64 64" fill="none">
                      <rect x="8" y="16" width="48" height="36" rx="4" stroke="currentColor" strokeWidth="2"/>
                      <circle cx="24" cy="30" r="5" stroke="currentColor" strokeWidth="2"/>
                      <path d="M8 42 L22 28 L32 38 L40 30 L56 44" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
                      <path d="M32 8 L32 24 M26 14 L32 8 L38 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  </div>
                  <p className="drop-title">Drop your image here</p>
                  <p className="drop-sub">JPEG · PNG · WEBP</p>
                </div>
              )}
            </div>

            <div className="controls">
              <label className="heatmap-toggle">
                <input type="checkbox" checked={includeHeatmap} onChange={e => setIncludeHeatmap(e.target.checked)} />
                <span className="toggle-track"><span className="toggle-thumb" /></span>
                <span>Include GradCAM Heatmap</span>
              </label>
              <button className="analyze-btn" onClick={detect} disabled={!file || loading}>
                {loading ? <span className="btn-spinner" /> : null}
                {loading ? "Analyzing..." : "Analyze Image"}
              </button>
            </div>

            {error && <div className="error-box">⚠ {error}</div>}

            {result && (
              <div className={`result-panel ${isReal ? "real" : "fake"}`}>
                <div className="verdict-row">
                  <div className={`verdict-badge ${isReal ? "real" : "fake"}`}>
                    {isReal ? "✓ REAL" : "✗ FAKE"}
                  </div>
                  <div className="verdict-file">{result.filename}</div>
                </div>

                <div className="gauges-row">
                  <CircleGauge value={result.confidence * 100} label="Confidence" color={isReal ? "#00ffe0" : "#ff3d6e"} />
                  <CircleGauge value={result.model1_score * 100} label="Model 1" color="#7b2fff" />
                  <CircleGauge value={result.model2_score * 100} label="Model 2" color="#ff9500" />
                </div>

                <div className="score-bars">
                  {[
                    { label: "Confidence", val: result.confidence, color: isReal ? "#00ffe0" : "#ff3d6e" },
                    { label: "Model 1 Score", val: result.model1_score, color: "#7b2fff" },
                    { label: "Model 2 Score", val: result.model2_score, color: "#ff9500" },
                  ].map(s => (
                    <div key={s.label} className="score-bar-row">
                      <span className="score-bar-label">{s.label}</span>
                      <div className="score-bar-track">
                        <div className="score-bar-fill" style={{ width: `${s.val * 100}%`, background: s.color }} />
                      </div>
                      <span className="score-bar-val">{(s.val * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>

                {result.heatmap && (
                  <div className="heatmap-section">
                    <p className="heatmap-title">GradCAM Heatmap</p>
                    <img src={`data:image/png;base64,${result.heatmap}`} alt="heatmap" className="heatmap-img" />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {mode === "batch" && (
          <div className="batch-layout">
            <div
              className={`drop-zone batch-drop ${dragging ? "dragging" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => { e.preventDefault(); setDragging(false); handleBatchFiles(e.dataTransfer.files); }}
              onClick={() => batchRef.current.click()}
            >
              <input ref={batchRef} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden onChange={e => handleBatchFiles(e.target.files)} />
              <div className="drop-inner">
                <div className="drop-icon">
                  <svg viewBox="0 0 64 64" fill="none">
                    <rect x="4" y="20" width="40" height="32" rx="3" stroke="currentColor" strokeWidth="2"/>
                    <rect x="12" y="12" width="40" height="32" rx="3" stroke="currentColor" strokeWidth="2" strokeDasharray="4 2"/>
                    <path d="M24 36 L32 28 L40 36" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    <path d="M32 28 L32 44" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
                <p className="drop-title">{batchFiles.length ? `${batchFiles.length} image${batchFiles.length > 1 ? "s" : ""} selected` : "Drop multiple images"}</p>
                <p className="drop-sub">Hold Ctrl to select multiple files</p>
              </div>
            </div>

            {batchPreviews.length > 0 && (
              <div className="batch-preview-strip">
                {batchPreviews.slice(0, 8).map((src, i) => (
                  <img key={i} src={src} alt={batchFiles[i]?.name} className="batch-thumb" />
                ))}
                {batchPreviews.length > 8 && <div className="batch-more">+{batchPreviews.length - 8}</div>}
              </div>
            )}

            <div className="controls" style={{ marginBottom: 0 }}>
              <label className="heatmap-toggle">
                <input type="checkbox" checked={includeBatchHeatmap} onChange={e => setIncludeBatchHeatmap(e.target.checked)} />
                <span className="toggle-track"><span className="toggle-thumb" /></span>
                <span>Include GradCAM Heatmap</span>
              </label>
            </div>

            <button className="analyze-btn" onClick={detectBatch} disabled={!batchFiles.length || loading}>
              {loading ? <span className="btn-spinner" /> : null}
              {loading ? "Analyzing..." : `Analyze ${batchFiles.length || ""} Images`}
            </button>

            {error && <div className="error-box">⚠ {error}</div>}

            {batchResult && (
              <div className="batch-results">
                <div className="batch-results-header">
                  <span className="batch-results-title">Results</span>
                  <button className="clear-btn" onClick={clearBatch}>✕ Clear</button>
                </div>
                <div className="batch-summary">
                  <div className="summary-card">
                    <span className="summary-num">{batchResult.processed}</span>
                    <span className="summary-lbl">Processed</span>
                  </div>
                  <div className="summary-card real">
                    <span className="summary-num">{batchResult.real_count}</span>
                    <span className="summary-lbl">Real</span>
                  </div>
                  <div className="summary-card fake">
                    <span className="summary-num">{batchResult.ai_count}</span>
                    <span className="summary-lbl">AI-Generated</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-num">{(batchResult.avg_confidence * 100).toFixed(1)}%</span>
                    <span className="summary-lbl">Avg Confidence</span>
                  </div>
                </div>

                <div className="batch-grid">
                  {batchResult.results.map((item, i) => (
                    <BatchResultCard key={i} item={item} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        <span>FORENSIQ · AI Image Forensics Engine · Powered by EfficientNet</span>
      </footer>
    </div>
  );
}
