/**
 * Visualização da rede elétrica usando D3.js
 * Suporta dois modos: força e hierárquico.
 */

class NetworkVisualization {
    constructor(containerId) {
        this.containerId = containerId;
        this.width = 800;
        this.height = 500;
        this.nodes = [];
        this.links = [];
        this.mode = 'force'; // 'force' ou 'hierarchical'

        this.init();
    }

    init() {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '';

        this.svg = d3
            .select(`#${this.containerId}`)
            .append('svg')
            .attr('width', '100%')
            .attr('height', this.height)
            .style('background', '#f9fafb')
            .style('border-radius', '12px');

        this.g = this.svg.append('g');

        const zoom = d3
            .zoom()
            .scaleExtent([0.4, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        this.linkGroup = this.g.append('g').attr('class', 'links');
        this.nodeGroup = this.g.append('g').attr('class', 'nodes');

        this.simulation = d3
            .forceSimulation()
            .force('link', d3.forceLink().id((d) => d.id).distance(120))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(400, this.height / 2))
            .force('collision', d3.forceCollide().radius(40));
    }

    async update() {
        try {
            const nodesData = await api.getNodes();
            this.nodes = nodesData.nodes.map((n) => ({
                id: n.key,
                type: n.data.type,
                capacity: n.data.capacity,
                load: n.data.current_load,
                efficiency: n.data.efficiency,
                utilization: n.data.current_load / n.data.capacity,
            }));

            this.links = [];

            const substations = this.nodes.filter((n) => n.type === 'substation');
            const transformers = this.nodes.filter((n) => n.type === 'transformer');
            const consumers = this.nodes.filter((n) => n.type === 'consumer');

            substations.forEach((sub, i) => {
                transformers.forEach((trf, j) => {
                    if (j % substations.length === i) {
                        this.links.push({
                            source: sub.id,
                            target: trf.id,
                        });
                    }
                });
            });

            transformers.forEach((trf, i) => {
                consumers.forEach((cons, j) => {
                    if (j % transformers.length === i) {
                        this.links.push({
                            source: trf.id,
                            target: cons.id,
                        });
                    }
                });
            });

            this.render();
        } catch (error) {
            console.error('Erro ao atualizar visualização:', error);
        }
    }

    setMode(mode) {
        this.mode = mode;
        this.render();
    }

    render() {
        const nodeConfig = {
            substation: { color: '#3b82f6', size: 22, label: '⚡' },
            transformer: { color: '#8b5cf6', size: 18, label: '🔌' },
            consumer: { color: '#10b981', size: 14, label: '🏠' },
        };

        const link = this.linkGroup
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#cbd5e1')
            .attr('stroke-width', 2)
            .attr('stroke-opacity', 0.7);

        const node = this.nodeGroup
            .selectAll('g')
            .data(this.nodes, (d) => d.id)
            .join((enter) => {
                const g = enter.append('g').call(
                    d3
                        .drag()
                        .on('start', (event, d) => this.dragStarted(event, d))
                        .on('drag', (event, d) => this.dragged(event, d))
                        .on('end', (event, d) => this.dragEnded(event, d))
                );

                g.append('circle');
                g.append('text').attr('class', 'icon');
                g.append('text').attr('class', 'label');
                g.append('title');

                return g;
            });

        node
            .select('circle')
            .attr('r', (d) => nodeConfig[d.type].size)
            .attr('fill', (d) => {
                if (d.utilization > 0.9) return '#ef4444';
                if (d.utilization > 0.7) return '#f59e0b';
                return nodeConfig[d.type].color;
            })
            .attr('stroke', '#ffffff')
            .attr('stroke-width', 3)
            .style('cursor', 'pointer');

        node
            .select('text.icon')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('font-size', (d) => `${nodeConfig[d.type].size}px`)
            .style('pointer-events', 'none')
            .text((d) => nodeConfig[d.type].label);

        node
            .select('text.label')
            .attr('text-anchor', 'middle')
            .attr('dy', (d) => nodeConfig[d.type].size + 14)
            .style('font-size', '10px')
            .style('font-weight', '600')
            .style('fill', '#374151')
            .style('pointer-events', 'none')
            .text((d) => d.id);

        node
            .select('title')
            .text(
                (d) =>
                    `${d.id}\nTipo: ${d.type}\nCarga: ${d.load.toFixed(
                        1
                    )} kW\nCapacidade: ${d.capacity.toFixed(
                        1
                    )} kW\nUtilização: ${(d.utilization * 100).toFixed(
                        1
                    )}%\nEficiência: ${(d.efficiency * 100).toFixed(0)}%`
            );

        if (this.mode === 'force') {
            this.simulation.nodes(this.nodes).on('tick', () => {
                link
                    .attr('x1', (d) => d.source.x)
                    .attr('y1', (d) => d.source.y)
                    .attr('x2', (d) => d.target.x)
                    .attr('y2', (d) => d.target.y);

                node.attr('transform', (d) => `translate(${d.x},${d.y})`);
            });

            this.simulation.force('link').links(this.links);
            this.simulation.alpha(0.4).restart();
        } else {
            const width = 800;
            const height = this.height;
            const layers = {
                substation: height * 0.2,
                transformer: height * 0.5,
                consumer: height * 0.8,
            };

            const byType = {
                substation: this.nodes.filter((n) => n.type === 'substation'),
                transformer: this.nodes.filter((n) => n.type === 'transformer'),
                consumer: this.nodes.filter((n) => n.type === 'consumer'),
            };

            Object.keys(byType).forEach((type) => {
                const arr = byType[type];
                const step = width / (arr.length + 1);
                arr.forEach((n, idx) => {
                    n.x = (idx + 1) * step;
                    n.y = layers[type];
                });
            });

            link
                .attr('x1', (d) => this.getNodeById(d.source).x)
                .attr('y1', (d) => this.getNodeById(d.source).y)
                .attr('x2', (d) => this.getNodeById(d.target).x)
                .attr('y2', (d) => this.getNodeById(d.target).y);

            node.attr('transform', (d) => `translate(${d.x},${d.y})`);

            this.simulation.stop();
        }
    }

    getNodeById(id) {
        if (typeof id === 'object') return id;
        return this.nodes.find((n) => n.id === id) || { x: 0, y: 0 };
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
