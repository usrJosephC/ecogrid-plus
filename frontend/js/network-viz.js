/**
 * Visualização da rede elétrica usando D3.js
 */

class NetworkVisualization {
    constructor(containerId) {
        this.containerId = containerId;
        this.width = 800;
        this.height = 600;
        this.nodes = [];
        this.links = [];
        
        this.init();
    }
    
    init() {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '';
        
        // Cria SVG
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', '100%')
            .attr('height', this.height)
            .style('background', '#f8f9fa')
            .style('border-radius', '12px');
        
        // Grupo principal com zoom
        this.g = this.svg.append('g');
        
        // Adiciona zoom
        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
        
        // Cria grupos para links e nós
        this.linkGroup = this.g.append('g').attr('class', 'links');
        this.nodeGroup = this.g.append('g').attr('class', 'nodes');
        
        // Simulação de força
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(120))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(400, 300))
            .force('collision', d3.forceCollide().radius(40));
    }
    
    async update() {
        try {
            // Busca dados da API
            const nodesData = await api.getNodes();
            
            // Prepara nós
            this.nodes = nodesData.nodes.map(n => ({
                id: n.key,
                type: n.data.type,
                capacity: n.data.capacity,
                load: n.data.current_load,
                efficiency: n.data.efficiency,
                utilization: (n.data.current_load / n.data.capacity)
            }));
            
            // Busca conexões (edges)
            const stats = await api.getStats();
            this.links = [];
            
            // Cria links baseado no grafo
            // Como não temos endpoint específico, vamos criar conexões lógicas
            const substations = this.nodes.filter(n => n.type === 'substation');
            const transformers = this.nodes.filter(n => n.type === 'transformer');
            const consumers = this.nodes.filter(n => n.type === 'consumer');
            
            // Conecta subestações aos transformadores
            substations.forEach((sub, i) => {
                transformers.forEach((trf, j) => {
                    if (j % substations.length === i) {
                        this.links.push({
                            source: sub.id,
                            target: trf.id
                        });
                    }
                });
            });
            
            // Conecta transformadores aos consumidores
            transformers.forEach((trf, i) => {
                consumers.forEach((cons, j) => {
                    if (j % transformers.length === i) {
                        this.links.push({
                            source: trf.id,
                            target: cons.id
                        });
                    }
                });
            });
            
            this.render();
            
        } catch (error) {
            console.error('Erro ao atualizar visualização:', error);
        }
    }
    
    render() {
        // Define cores e tamanhos por tipo
        const nodeConfig = {
            'substation': { color: '#3b82f6', size: 24, label: '⚡' },
            'transformer': { color: '#8b5cf6', size: 18, label: '🔌' },
            'consumer': { color: '#10b981', size: 14, label: '🏠' }
        };
        
        // Renderiza links
        const link = this.linkGroup
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#cbd5e1')
            .attr('stroke-width', 2)
            .attr('stroke-opacity', 0.6);
        
        // Renderiza nós
        const node = this.nodeGroup
            .selectAll('g')
            .data(this.nodes)
            .join('g')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)));
        
        // Círculo do nó com cor baseada em utilização
        node.selectAll('circle').remove();
        node.append('circle')
            .attr('r', d => nodeConfig[d.type].size)
            .attr('fill', d => {
                if (d.utilization > 0.9) return '#ef4444'; // Sobrecarga
                if (d.utilization > 0.7) return '#f59e0b'; // Alerta
                return nodeConfig[d.type].color; // Normal
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 3)
            .style('cursor', 'pointer');
        
        // Ícone do nó
        node.selectAll('text.icon').remove();
        node.append('text')
            .attr('class', 'icon')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('font-size', d => `${nodeConfig[d.type].size}px`)
            .style('pointer-events', 'none')
            .text(d => nodeConfig[d.type].label);
        
        // Label do nó
        node.selectAll('text.label').remove();
        node.append('text')
            .attr('class', 'label')
            .attr('text-anchor', 'middle')
            .attr('dy', d => nodeConfig[d.type].size + 15)
            .style('font-size', '11px')
            .style('font-weight', '600')
            .style('fill', '#374151')
            .style('pointer-events', 'none')
            .text(d => d.id);
        
        // Tooltip
        node.append('title')
            .text(d => `${d.id}\nTipo: ${d.type}\nCarga: ${d.load.toFixed(1)} kW\nCapacidade: ${d.capacity.toFixed(1)} kW\nUtilização: ${(d.utilization * 100).toFixed(1)}%\nEficiência: ${(d.efficiency * 100).toFixed(0)}%`);
        
        // Atualiza simulação
        this.simulation
            .nodes(this.nodes)
            .on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
        
        this.simulation.force('link').links(this.links);
        this.simulation.alpha(0.3).restart();
    }
    
    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}
