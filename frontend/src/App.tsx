import React from "react";
import FlowNodeComponent from "./components/FlowNode";

const App: React.FC = () => {
    const nodes = [
        { id: "1", label: "Insert", color: "lightblue" },
        { id: "2", label: "Swap", color: "lightgreen" },
        { id: "3", label: "Move Up", color: "lightcoral" },
    ];

    return (
        <div>
            <FlowNodeComponent nodes={nodes} />
        </div>
    );
};

export default App;
