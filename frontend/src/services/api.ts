const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export interface GraphData {
    nodes: { id: string | number; [key: string]: any }[];
    links: { source: string | number; target: string | number; [key: string]: any }[];
}

/**
 * Fetches the entire knowledge graph from the backend.
 * @returns {Promise<GraphData>} A promise that resolves to the graph data.
 */
export const getFullGraph = async (): Promise<GraphData> => {
    const response = await fetch(`${API_BASE_URL}/api/graph/full`);
    if (!response.ok) {
        throw new Error('Failed to fetch graph data');
    }
    return response.json();
};

/**
 * Adds a new observation to the short-term memory.
 * @param {string} observation - The observation text to add.
 * @returns {Promise<any>} A promise that resolves to the API response.
 */
export const addObservation = async (observation: string): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/observations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ observation }),
    });
    if (!response.ok) {
        throw new Error('Failed to add observation');
    }
    return response.json();
};

/**
 * Triggers the memory consolidation process.
 * @returns {Promise<any>} A promise that resolves to the API response.
 */
export const triggerConsolidation = async (): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/consolidate`, {
        method: 'POST',
    });
    if (!response.ok) {
        throw new Error('Failed to trigger consolidation');
    }
    return response.json();
};

/**
 * Searches the memory with a given query.
 * @param {string} query - The search query.
 * @returns {Promise<any>} A promise that resolves to the search results.
 */
export const searchMemory = async (query: string): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    });
    if (!response.ok) {
        throw new Error('Failed to search memory');
    }
    return response.json();
};

/**
 * Sends a chat message to the AI agent.
 * @param {string} message - The user's message.
 * @param {Array} messages - Previous conversation history.
 * @returns {Promise<any>} A promise that resolves to the agent's response.
 */
export const sendChatMessage = async (message: string, messages: any[] = []): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message,
            messages: messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }))
        }),
    });
    if (!response.ok) {
        throw new Error('Failed to send chat message');
    }
    return response.json();
};