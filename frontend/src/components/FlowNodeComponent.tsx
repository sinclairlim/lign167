import React, { useState, useEffect } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  Node,
  Edge,
  Position,
  NodeProps,
} from "reactflow";
import dagre from "dagre";
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

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const isHorizontal = false;
  dagreGraph.setGraph({ rankdir: isHorizontal ? 'LR' : 'TB' });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;

    // Shift the dagre node position to match React Flow's position format
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    node.style = {
      ...node.style,
      width: nodeWidth,
      height: nodeHeight,
    };
  });

  return { nodes, edges };
};

const FlowNodeComponent: React.FC<FlowNodeProps> = ({ nodes, edges }) => {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [layoutedNodes, setLayoutedNodes] = useState<Node[]>([]);
  const [layoutedEdges, setLayoutedEdges] = useState<Edge[]>([]);

  useEffect(() => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      nodes,
      edges
    );
    setLayoutedNodes(layoutedNodes);
    setLayoutedEdges(layoutedEdges);
  }, [nodes, edges]);

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
            minWidth: nodeWidth,
          }}
        >
          <strong>{data.label}</strong>
          {hasError && <div style={{ color: 'red' }}>{data.error}</div>}
        </div>
      );
    },
  };

  return (
    <>
      <div style={{ width: '100%', height: '500px' }}>
        <ReactFlow
          nodes={layoutedNodes}
          edges={layoutedEdges}
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
        animation={false}
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