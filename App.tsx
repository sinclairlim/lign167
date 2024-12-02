import React, { useState, useEffect } from "react";
import "./App.css";

interface AnalysisEntry {
  code: string;
  analysis: string[];
  hints: string[];
}

function App() {
  const [code, setCode] = useState<string>("");
  const [analysis, setAnalysis] = useState<string[] | null>(null);
  const [hints, setHints] = useState<string[] | null>(null);
  const [history, setHistory] = useState<AnalysisEntry[]>([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch("http://localhost:5000/history");
      const data: AnalysisEntry[] = await response.json();
      setHistory(data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const analyzeCode = async () => {
    try {
      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });
      const data = await response.json();
      setAnalysis(data.analysis);
      setHints(data.hints);
      fetchHistory(); // Refresh history after analysis
    } catch (error) {
      console.error("Error analyzing code:", error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FLEX: Fault Localization & Explanations</h1>
        <textarea
          rows={10}
          cols={50}
          placeholder="Enter your Python code here..."
          value={code}
          onChange={(e) => setCode(e.target.value)}
        ></textarea>
        <button onClick={analyzeCode}>Analyze</button>
        {analysis && (
          <div>
            <h2>Analysis</h2>
            <ul>
              {analysis.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        {hints && (
          <div>
            <h2>Related Hints</h2>
            <ul>
              {hints.map((hint, index) => (
                <li key={index}>{hint}</li>
              ))}
            </ul>
          </div>
        )}
        <div>
          <h2>History</h2>
          <ul>
            {history.map((entry, index) => (
              <li key={index}>
                <strong>Code:</strong> {entry.code} <br />
                <strong>Analysis:</strong> {entry.analysis.join(", ")} <br />
                <strong>Hints:</strong> {entry.hints.join(", ")}
              </li>
            ))}
          </ul>
        </div>
      </header>
    </div>
  );
}

export default App;
