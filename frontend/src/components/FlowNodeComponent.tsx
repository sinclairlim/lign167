import React, { useState } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  Node,
  Edge,
  Position,
  NodeProps,
} from "reactflow";
import { getExplanation } from "../services/api";
import { Modal, Button } from 'react-bootstrap';

interface Explanation {
  description: string;
  concepts?: string[];
  issues?: string[];
  suggestions?: string[];
}

interface FlowNodeProps {
  nodes: Node[];
  edges: Edge[];
}

const FlowNodeComponent: React.FC<FlowNodeProps> = ({ nodes, edges }) => {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [showModal, setShowModal] = useState(false);

  const onNodeClick = async (_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setShowModal(true);

    const nodeInfo = node.data.label;

    if (nodeInfo) {
      try {
        const explanationResponse = await getExplanation(nodeInfo);
        setExplanation(explanationResponse.explanation);
      } catch (error) {
        setExplanation({ description: "Error fetching explanation." });
      }
    }
  };

  // Add custom node types to highlight errors
  const nodeTypes = {
    customNode: (props: NodeProps) => {
      const { data } = props;
      const hasError = data.error && data.error.length > 0;

      return (
        <div
          style={{
            padding: 10,
            border: '1px solid',
            borderColor: hasError ? 'red' : '#222',
            backgroundColor: hasError ? '#ffe6e6' : '#fff',
            borderRadius: 5,
            textAlign: 'center',
          }}
        >
          <strong>{data.label}</strong>
          {hasError && <div style={{ color: 'red' }}>{data.error}</div>}
        </div>
      );
    },
  };

  // Map nodes to include the custom node type
  const updatedNodes = nodes.map((node) => ({
    ...node,
    type: 'customNode',
  }));

  return (
    <>
      <div style={{ width: '100%', height: '500px' }}>
        <ReactFlow
          nodes={updatedNodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>
      <Modal
        show={showModal}
        onHide={() => setShowModal(false)}
        animation={false} // Add this line
      >
        <Modal.Header closeButton>
          <Modal.Title>Node Explanation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {explanation ? (
            <>
              <p><strong>Description:</strong> {explanation.description}</p>
              {explanation.concepts && (
                <>
                  <p><strong>Concepts:</strong></p>
                  <ul>
                    {explanation.concepts.map((concept, index) => (
                      <li key={index}>{concept}</li>
                    ))}
                  </ul>
                </>
              )}
              {explanation.issues && (
                <>
                  <p><strong>Issues:</strong></p>
                  <ul>
                    {explanation.issues.map((issue, index) => (
                      <li key={index}>{issue}</li>
                    ))}
                  </ul>
                </>
              )}
              {explanation.suggestions && (
                <>
                  <p><strong>Suggestions:</strong></p>
                  <ul>
                    {explanation.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </>
              )}
            </>
          ) : (
            <p>Loading explanation...</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default FlowNodeComponent;