import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000'; // Ensure this matches your backend

interface AnalyzeCodeResponse {
  nodes: any[];
  edges: any[];
  high_level_feedback: {
    summary: string;
    strengths?: string[];
    weaknesses?: string[];
    recommendations?: string[];
  };
}

export const analyzeCode = async (code: string, intent: string): Promise<AnalyzeCodeResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/analyze_code`, { code, intent });
    return response.data;
  } catch (error) {
    console.error('Error in analyzeCode:', error);
    throw error;
  }
};

interface GetExplanationResponse {
  explanation: {
    description: string;
    concepts?: string[];
    issues?: string[];
    suggestions?: string[];
  };
}

export const getExplanation = async (nodeInfo: string): Promise<GetExplanationResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/get_explanation`, { nodeInfo });
    return response.data;
  } catch (error) {
    console.error('Error in getExplanation:', error);
    throw error;
  }
};
