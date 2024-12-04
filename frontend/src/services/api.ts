import axios from "axios";

export const getExplanation = async (nodeLabel: string): Promise<string> => {
    try {
        const response = await axios.post("http://127.0.0.1:5000/api/explain", {
            nodeLabel,
        });
        return response.data.explanation;
    } catch (error: any) {
        console.error("Error fetching explanation:", error.message);
        throw new Error("Failed to fetch explanation from the backend.");
    }
};
