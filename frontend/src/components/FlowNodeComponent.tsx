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
// newly installed react-markdown to display explanation as markdown
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

// constructing a dagre graph for auto-layout
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

  // recalculate layout whenever nodes or edges change
  useEffect(() => {
    const { nodes: layouted, edges: layoutedEdgs } = getLayoutedElements(nodes, edges);
    setLayoutedNodes(layouted);
    setLayoutedEdges(layoutedEdgs);
  }, [nodes, edges]);

  const onNodeClick = async (_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setShowModal(true);

    if (node.data.error) {
      setExplanation({ description: node.data.error });
    } else {
      setExplanation({ description: "No errors in this node." });
    }
  };

  const nodeTypes = {
    customNode: (props: NodeProps) => {
      const { data } = props;
      // highlight node red if data.error exists
      const hasError = !!data.error;

      return (
        <div
          style={{
            padding: 10,
            border: "1px solid",
            borderColor: hasError ? "red" : "#222",
            backgroundColor: hasError ? "#ffe6e6" : "#fff",
            borderRadius: 5,
            textAlign: "center",
            minWidth: nodeWidth,
            cursor: "pointer",
          }}
        >
          <strong>{data.label}</strong>
        </div>
      );
    },
  };

  return (
    <>
      <div style={{ width: "100%", height: "500px" }}>
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

      <Modal show={showModal} onHide={() => setShowModal(false)} animation={false}>
        <Modal.Header closeButton>
          <Modal.Title>Node Explanation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {explanation ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {explanation.description}
            </ReactMarkdown>
          ) : (
            <p>Loading explanation...</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default FlowNodeComponent;
