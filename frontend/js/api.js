/**
 * API Client para comunicação com backend Flask
 */

const API_BASE_URL = 'http://localhost:5000/api';

class EcoGridAPI {
    constructor() {
        this.baseUrl = API_BASE_URL;
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro na requisição');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==================== SYSTEM ====================

    async initialize(numNodes = 20, trainML = true) {
        return this.request('/init', {
            method: 'POST',
            body: JSON.stringify({ num_nodes: numNodes, train_ml: trainML })
        });
    }

    async getHealth() {
        return this.request('/health');
    }

    async getStats() {
        return this.request('/stats');
    }

    // ==================== NODES ====================

    async getNodes() {
        return this.request('/nodes');
    }

    async getNode(nodeId) {
        return this.request(`/nodes/${nodeId}`);
    }

    async createNode(nodeData) {
        return this.request('/nodes', {
            method: 'POST',
            body: JSON.stringify(nodeData)
        });
    }

    async updateNodeLoad(nodeId, load) {
        return this.request(`/nodes/${nodeId}/load`, {
            method: 'PUT',
            body: JSON.stringify({ load })
        });
    }

    // ==================== BALANCING ====================

    async balanceNetwork() {
        return this.request('/balance', {
            method: 'POST'
        });
    }

    async getBalanceStats() {
        return this.request('/balance/stats');
    }

    // ==================== ROUTING ====================

    async findRoute(source, destination, algorithm = 'dijkstra') {
        return this.request('/route', {
            method: 'POST',
            body: JSON.stringify({ source, destination, algorithm })
        });
    }

    async findRedundantRoutes(source, destination, k = 3) {
        return this.request('/route/redundant', {
            method: 'POST',
            body: JSON.stringify({ source, destination, k })
        });
    }

    // ==================== OPTIMIZATION ====================

    async optimizeEfficiency() {
        return this.request('/optimize', {
            method: 'POST'
        });
    }

    // ==================== MACHINE LEARNING ====================

    async predictDemand(nodeId, hoursAhead = 24) {
        return this.request('/ml/predict', {
            method: 'POST',
            body: JSON.stringify({ node_id: nodeId, hours_ahead: hoursAhead })
        });
    }

    async trainML(epochs = 100) {
        return this.request('/ml/train', {
            method: 'POST',
            body: JSON.stringify({ epochs })
        });
    }

    async getMLStats() {
        return this.request('/ml/stats');
    }

    // ==================== IOT ====================

    async getIoTReadings() {
        return this.request('/iot/readings');
    }

    async simulateFailure(nodeId, durationHours = 2) {
        return this.request('/iot/simulate-failure', {
            method: 'POST',
            body: JSON.stringify({ node_id: nodeId, duration_hours: durationHours })
        });
    }

    // ==================== EVENTS ====================

    async getEvents(type = null) {
        const query = type ? `?type=${type}` : '';
        return this.request(`/events${query}`);
    }

    async getCriticalEvents() {
        return this.request('/events/critical');
    }

    // ==================== BENCHMARK & HEAP ====================

    async getBenchmarkSummary() {
        return this.request('/benchmark/summary');
    }

    async getHeapSnapshot() {
        return this.request('/events/heap');
    }
}

// Instância global
const api = new EcoGridAPI();
