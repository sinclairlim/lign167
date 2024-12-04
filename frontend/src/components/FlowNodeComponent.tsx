import React, { useState } from "react";
import ReactFlow, { MiniMap, Controls, Background, Node, Edge } from "reactflow";
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

  return (
    <>
      <div style={{ width: '100%', height: '500px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>
      <Modal show={showModal} onHide={() => setShowModal(false)}>
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
              {/* Similarly for issues and suggestions */}
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
