"""
Grafo direcionado para representar a rede elétrica.
Usa lista de adjacências otimizada.
"""


class EnergyGraph:
    def __init__(self):
        self.nodes = {}  # {node_id: {type, capacity, current_load, efficiency}}
        self.edges = {}  # {node_id: [(neighbor_id, weight, line_data)]}
    
    def add_node(self, node_id, node_type, capacity, efficiency=1.0, current_load=0):
        """Adiciona nó ao grafo - O(1)"""
        self.nodes[node_id] = {
            'type': node_type,
            'capacity': capacity,
            'current_load': current_load,
            'efficiency': efficiency
        }
        
        # Inicializa lista de edges se ainda não existir
        if node_id not in self.edges:
            self.edges[node_id] = []
    
    def add_edge(self, from_node, to_node, distance, resistance=0.1, status='active'):
        """Adiciona aresta bidirecional - O(1)"""
        # Verifica se os nós existem
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Nós {from_node} ou {to_node} não existem")
        
        # Calcula peso (considera distância e resistência)
        weight = distance * (1 + resistance)
        
        line_data = {
            'distance': distance,
            'resistance': resistance,
            'status': status,
            'capacity': 1000  # Capacidade da linha
        }
        
        # Adiciona aresta bidirecional
        if from_node not in self.edges:
            self.edges[from_node] = []
        if to_node not in self.edges:
            self.edges[to_node] = []
        
        self.edges[from_node].append((to_node, weight, line_data))
        self.edges[to_node].append((from_node, weight, line_data))
    
    def update_load(self, node_id, new_load):
        """Atualiza carga de um nó - O(1)"""
        if node_id in self.nodes:
            self.nodes[node_id]['current_load'] = new_load
    
    def get_neighbors(self, node_id):
        """Retorna vizinhos de um nó - O(1)"""
        return self.edges.get(node_id, [])
    
    def dijkstra(self, source, destination):
        """
        Algoritmo de Dijkstra para caminho mais curto.
        Complexidade: O((V + E) log V)
        """
        import heapq
        
        if source not in self.nodes or destination not in self.nodes:
            return [], float('inf')
        
        # Inicialização
        distances = {node: float('inf') for node in self.nodes}
        distances[source] = 0
        previous = {node: None for node in self.nodes}
        pq = [(0, source)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == destination:
                break
            
            for neighbor, weight, line_data in self.edges.get(current, []):
                if line_data['status'] != 'active':
                    continue
                
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        # Reconstrói caminho
        path = []
        current = destination
        
        if previous[current] is not None or current == source:
            while current is not None:
                path.insert(0, current)
                current = previous[current]
        
        return path, distances[destination]
    
    def astar(self, source, destination):
        """
        Algoritmo A* com heurística baseada em tipo de nó.
        Complexidade: O((V + E) log V)
        """
        import heapq
        
        if source not in self.nodes or destination not in self.nodes:
            return [], float('inf')
        
        def heuristic(node):
            """Heurística: prioriza nós mais eficientes"""
            node_data = self.nodes[node]
            base_h = 1.0
            
            # Penaliza nós com baixa eficiência
            if node_data['efficiency'] < 0.85:
                base_h *= 1.2
            
            # Penaliza nós sobrecarregados
            utilization = node_data['current_load'] / node_data['capacity']
            if utilization > 0.8:
                base_h *= 1.5
            
            return base_h
        
        # Inicialização
        g_score = {node: float('inf') for node in self.nodes}
        g_score[source] = 0
        
        f_score = {node: float('inf') for node in self.nodes}
        f_score[source] = heuristic(source)
        
        previous = {node: None for node in self.nodes}
        pq = [(f_score[source], source)]
        visited = set()
        
        while pq:
            _, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == destination:
                break
            
            for neighbor, weight, line_data in self.edges.get(current, []):
                if line_data['status'] != 'active':
                    continue
                
                tentative_g = g_score[current] + weight
                
                if tentative_g < g_score[neighbor]:
                    previous[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor)
                    heapq.heappush(pq, (f_score[neighbor], neighbor))
        
        # Reconstrói caminho
        path = []
        current = destination
        
        if previous[current] is not None or current == source:
            while current is not None:
                path.insert(0, current)
                current = previous[current]
        
        return path, g_score[destination]
    
    def get_network_stats(self):
        """Retorna estatísticas da rede"""
        total_capacity = 0
        total_load = 0
        overloaded = 0
        
        for node_id, node_data in self.nodes.items():
            total_capacity += node_data.get('capacity', 0)
            total_load += node_data.get('current_load', 0)
            
            # Conta nós sobrecarregados (>90% capacidade)
            utilization = node_data.get('current_load', 0) / node_data.get('capacity', 1)
            if utilization > 0.9:
                overloaded += 1
        
        utilization = total_load / total_capacity if total_capacity > 0 else 0
        
        # Conta nós isolados
        isolated = sum(1 for node_id in self.nodes if len(self.edges.get(node_id, [])) == 0)
        
        return {
            'node_count': len(self.nodes),
            'edge_count': sum(len(edges) for edges in self.edges.values()) // 2,
            'total_capacity': total_capacity,
            'total_load': total_load,
            'utilization': utilization,
            'overloaded_nodes': overloaded,
            'isolated_nodes': isolated
        }
