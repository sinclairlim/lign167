import React, { useState } from "react";
import MonacoEditor from "@monaco-editor/react"; // referencing monaco editor docs: https://github.com/suren-atoyan/monaco-react
import { analyzeCode } from "../services/api";
import FlowNodeComponent from "./FlowNodeComponent";
import { Tabs, Tab, Spinner } from 'react-bootstrap';
import { Node, Edge } from 'reactflow';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface HighLevelFeedback {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

const CodeEditor: React.FC = () => {
  // local states for code, intent, nodes, edges, feedback, etc.
  const [code, setCode] = useState("");
  const [intent, setIntent] = useState("");
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [highLevelFeedback, setHighLevelFeedback] = useState<HighLevelFeedback | null>(null);
  const [loading, setLoading] = useState(false);

  // this function calls analyzeCode (like a user hitting 'submit')
  const handleSubmit = async () => {
    setLoading(true);
    try {
      const data = await analyzeCode(code, intent);
  
      let feedback: HighLevelFeedback;
  
      if ("explanation" in data.high_level_feedback) {
        // if it's just an 'explanation' field, store it in summary
        feedback = {
          summary: data.high_level_feedback.explanation as string,
          strengths: [],
          weaknesses: [],
          recommendations: [],
        };
      } else {
        // otherwise assume it has multiple fields
        feedback = {
          summary: data.high_level_feedback.summary,
          strengths: data.high_level_feedback.strengths ?? [],
          weaknesses: data.high_level_feedback.weaknesses ?? [],
          recommendations: data.high_level_feedback.recommendations ?? [],
        };
      }
  
      setNodes(data.nodes);
      setEdges(data.edges);
      setHighLevelFeedback(feedback);
    } catch (error) {
      console.error("Error analyzing code:", error);
    } finally {
      setLoading(false);
    }
  };  

  return (
    <div className="container mt-4">
      <h2>Fault Localization & Explanation for Python</h2>
      <div className="row mt-3">
        <div className="col-md-6">
          <h4>Intent/Goal</h4>
          <textarea
            className="form-control"
            rows={3}
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="Describe the intent or goal of your code..."
          />
          <h4 className="mt-3">Code Editor</h4>
          <MonacoEditor
            height="400px"
            language="python"
            value={code}
            onChange={(value?: string) => setCode(value || "")}
            options={{
              minimap: { enabled: false },
              automaticLayout: true,
            }}
          />
          <button className="btn btn-primary mt-2" onClick={handleSubmit} disabled={loading}>
            {loading ? <Spinner animation="border" size="sm" /> : "Analyze Code"}
          </button>
        </div>
        <div className="col-md-6">
          {loading && <Spinner animation="border" />}
          {!loading && highLevelFeedback && (
            <Tabs defaultActiveKey="feedback" className="mt-4">
              <Tab eventKey="feedback" title="High-Level Feedback">
                <div className="mt-3">
                  <h5>Summary</h5>
                  {/* parse summary as markdown */}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {highLevelFeedback.summary}
                  </ReactMarkdown>

                  {highLevelFeedback.strengths.length > 0 && (
                    <>
                      <h5>Strengths</h5>
                      <ul>
                        {highLevelFeedback.strengths.map((strength, index) => (
                          <li key={index}>{strength}</li>
                        ))}
                      </ul>
                    </>
                  )}
                  {highLevelFeedback.weaknesses.length > 0 && (
                    <>
                      <h5>Weaknesses</h5>
                      <ul>
                        {highLevelFeedback.weaknesses.map((weakness, index) => (
                          <li key={index}>{weakness}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  {highLevelFeedback.recommendations.length > 0 && (
                    <>
                      <h5>Recommendations</h5>
                      <ul>
                        {highLevelFeedback.recommendations.map((rec, index) => (
                          <li key={index}>{rec}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </Tab>
              <Tab eventKey="visualization" title="Visualization">
                <div className="mt-3" style={{ height: '500px' }}>
                  <FlowNodeComponent nodes={nodes} edges={edges} />
                </div>
              </Tab>
            </Tabs>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;
