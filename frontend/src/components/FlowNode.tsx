import React, { useState } from "react";
import { getExplanation } from "../services/api";

interface Node {
    id: string;
    label: string;
    color: string;
}

interface FlowNodeProps {
    nodes: Node[];
}

const FlowNodeComponent: React.FC<FlowNodeProps> = ({ nodes }) => {
    const [selectedNode, setSelectedNode] = useState<string | null>(null);
    const [explanation, setExplanation] = useState<string>("");

    const handleNodeClick = async (nodeId: string): Promise<void> => {
        setSelectedNode(nodeId);
        const nodeLabel = nodes.find((node) => node.id === nodeId)?.label;

        if (nodeLabel) {
            try {
                const explanationText = await getExplanation(nodeLabel);
                setExplanation(explanationText);
            } catch (error) {
                setExplanation("Error fetching explanation.");
            }
        }
    };

    return (
        <div>
            <h3>Interactive Heap Logic</h3>
            <div>
                {nodes.map((node) => (
                    <button
                        key={node.id}
                        style={{ backgroundColor: node.color, margin: "10px" }}
                        onClick={() => handleNodeClick(node.id)}
                    >
                        {node.label}
                    </button>
                ))}
            </div>
            {selectedNode && (
                <div>
                    <h4>Explanation for Node {selectedNode}:</h4>
                    <p>{explanation || "Fetching explanation..."}</p>
                </div>
            )}
        </div>
    );
};

export default FlowNodeComponent;
