/**
 * Visualização da rede usando D3.js
 */

class NetworkVisualization {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.width = 0;
        this.height = 0;
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        
        this.init();
    }

    init() {
        const containerElement = document.getElementById('network-viz');
        this.width = containerElement.clientWidth;
        this.height = containerElement.clientHeight;

        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);

        // Gradient definitions
        const defs = this.svg.append('defs');
        
        const gradient = defs.append('linearGradient')
            .attr('id', 'node-gradient')
            .attr('x1', '0%')
            .attr('y1', '0%')
            .attr('x2', '100%')
            .attr('y2', '100%');
        
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#667eea');
        
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#764ba2');

        // Grupos para camadas
        this.svg.append('g').attr('class', 'links');
        this.svg.append('g').attr('class', 'nodes');
        this.svg.append('g').attr('class', 'labels');

        // Simulação de força
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30));
    }

    async update() {
        try {
            const nodesData = await api.getNodes();
            this.processData(nodesData);
            this.render();
        } catch (error) {
            console.error('Erro ao atualizar visualização:', error);
        }
    }

    processData(data) {
        this.nodes = data.nodes.map(node => ({
            id: node.key,
            ...node.data,
            radius: this.getNodeRadius(node.data.type),
            color: this.getNodeColor(node.data)
        }));

        // Cria links baseado em conexões (simplificado)
        this.links = [];
        // Aqui você pode adicionar lógica para criar links baseado no grafo
    }

    getNodeRadius(type) {
        switch(type) {
            case 'substation': return 25;
            case 'transformer': return 18;
            case 'consumer': return 12;
            default: return 15;
        }
    }

    getNodeColor(nodeData) {
        const utilization = nodeData.current_load / nodeData.capacity;
        
        if (utilization > 0.9) return '#ef4444'; // Vermelho
        if (utilization > 0.7) return '#f59e0b'; // Laranja
        return '#10b981'; // Verde
    }

    render() {
        // Links
        const link = this.svg.select('.links')
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2);

        // Nós
        const node = this.svg.select('.nodes')
            .selectAll('circle')
            .data(this.nodes)
            .join('circle')
            .attr('r', d => d.radius)
            .attr('fill', d => d.color)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(this.drag(this.simulation));

        // Labels
        const label = this.svg.select('.labels')
            .selectAll('text')
            .data(this.nodes)
            .join('text')
            .text(d => d.id)
            .attr('font-size', 10)
            .attr('dx', 15)
            .attr('dy', 4);

        // Tooltips
        node.append('title')
            .text(d => `${d.id}\nCarga: ${d.current_load.toFixed(1)}/${d.capacity.toFixed(1)} kW\nUtilização: ${(d.current_load/d.capacity*100).toFixed(1)}%`);

        // Atualiza simulação
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        this.simulation.alpha(1).restart();
    }

    drag(simulation) {
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }
}

// Instância global
let networkViz;
