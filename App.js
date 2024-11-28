// Frontend: React App for Visualization
import React, { useState } from 'react';
import './App.css';

function App() {
  const [code, setCode] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [explanations, setExplanations] = useState(null);

  const analyzeCode = async () => {
    try {
      const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });
      const data = await response.json();
      setAnalysis(data.analysis);
      setExplanations(data.explanations);
    } catch (error) {
      console.error('Error analyzing code:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FLEX: Fault Localization & Explanations</h1>
        <textarea
          rows="10"
          cols="50"
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
        {explanations && (
          <div>
            <h2>Explanations</h2>
            <p>{explanations}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
