import React, { useState, useEffect } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  Node,
  Edge,
  Position,
  NodeProps,
} from "reactflow"; // referencing react flow docs: https://reactflow.dev
import dagre from "dagre"; // referencing dagre layout approach: https://github.com/dagrejs/dagre
import { getExplanation } from "../services/api";
import { Modal, Button } from 'react-bootstrap';

// informal interface naming can remain the same, just adding references as comments

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

// constructing a dagre graph for auto-layout (ref: dagre documentation: https://github.com/dagrejs/dagre)
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

// using dagre to layout the nodes automatically (similar approach found here: https://reactflow.dev/examples/layouting/)
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

    // shifting the dagre node position to match react flow's positioning
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
  // using local states to store selected node and explanation
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [layoutedNodes, setLayoutedNodes] = useState<Node[]>([]);
  const [layoutedEdges, setLayoutedEdges] = useState<Edge[]>([]);

  // effect that calculates layout using dagre whenever nodes or edges change
  useEffect(() => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      nodes,
      edges
    );
    setLayoutedNodes(layoutedNodes);
    setLayoutedEdges(layoutedEdges);
  }, [nodes, edges]);

  // handling a node click to show explanation
  const onNodeClick = async (_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setShowModal(true);
  
    if (node.data.error) {
      // if there's an error, we store it as the explanation
      setExplanation({
        description: node.data.error,
      });
    } else {
      // otherwise, no error
      setExplanation({
        description: 'no errors in this node.',
      });
    }
  };

  // define custom node types for react flow to highlight errors
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
            cursor: 'pointer', // indicate that the node is clickable
          }}
        >
          <strong>{data.label}</strong>
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
          <Modal.Title>node explanation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {explanation ? (
            <>
              <p><strong>description:</strong> {explanation.description}</p>
            </>
          ) : (
            <p>loading explanation...</p>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>close</Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default FlowNodeComponent;
