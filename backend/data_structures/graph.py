"""
Grafo ponderado para modelagem da rede elétrica.
Suporta múltiplas rotas e detecção de falhas.
"""

import heapq
from collections import defaultdict, deque

class EnergyGraph:
    def __init__(self):
        self.nodes = {}  # node_id -> {type, capacity, current_load, ...}
        self.edges = defaultdict(list)  # node_id -> [(neighbor, weight, line_data)]
        self.node_count = 0
        self.edge_count = 0
    
    def add_node(self, node_id, node_type, capacity, efficiency=1.0):
        """
        Adiciona nó à rede
        node_type: 'substation', 'transformer', 'consumer'
        """
        self.nodes[node_id] = {
            'type': node_type,
            'capacity': capacity,
            'current_load': 0,
            'efficiency': efficiency,
            'status': 'active',  # 'active', 'overloaded', 'failed'
            'voltage': 220.0,
            'connections': 0
        }
        self.node_count += 1
    
    def add_edge(self, from_node, to_node, distance, resistance=0.1):
        """
        Adiciona linha de transmissão (aresta)
        weight = perda energética (distance * resistance)
        """
        weight = distance * resistance
        line_data = {
            'distance': distance,
            'resistance': resistance,
            'capacity': 1000,  # kW
            'status': 'active'
        }
        
        # Grafo não direcionado
        self.edges[from_node].append((to_node, weight, line_data))
        self.edges[to_node].append((from_node, weight, line_data))
        
        self.nodes[from_node]['connections'] += 1
        self.nodes[to_node]['connections'] += 1
        self.edge_count += 1
    
    def update_load(self, node_id, load):
        """Atualiza carga atual do nó"""
        if node_id in self.nodes:
            self.nodes[node_id]['current_load'] = load
            
            # Atualiza status
            capacity = self.nodes[node_id]['capacity']
            if load > capacity:
                self.nodes[node_id]['status'] = 'overloaded'
            elif load > capacity * 0.9:
                self.nodes[node_id]['status'] = 'warning'
            else:
                self.nodes[node_id]['status'] = 'active'
    
    def dijkstra(self, start, end):
        """
        Algoritmo de Dijkstra para caminho de menor perda
        Complexidade: O(E log V)
        """
        if start not in self.nodes or end not in self.nodes:
            return None, float('inf')
        
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        previous = {node: None for node in self.nodes}
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end:
                break
            
            for neighbor, weight, line_data in self.edges[current]:
                if line_data['status'] != 'active':
                    continue  # Ignora linhas com falha
                
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        # Reconstrói caminho
        path = []
        current = end
        while current:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        if path[0] != start:
            return None, float('inf')
        
        return path, distances[end]
    
    def astar(self, start, end):
        """
        Algoritmo A* com heurística de distância euclidiana
        Complexidade: O(E log V)
        """
        def heuristic(node1, node2):
            # Heurística simplificada: assume perda proporcional à carga
            load1 = self.nodes[node1]['current_load']
            load2 = self.nodes[node2]['current_load']
            return abs(load1 - load2) * 0.01
        
        if start not in self.nodes or end not in self.nodes:
            return None, float('inf')
        
        open_set = [(0, start)]
        came_from = {}
        g_score = {node: float('inf') for node in self.nodes}
        g_score[start] = 0
        f_score = {node: float('inf') for node in self.nodes}
        f_score[start] = heuristic(start, end)
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path, g_score[end]
            
            for neighbor, weight, line_data in self.edges[current]:
                if line_data['status'] != 'active':
                    continue
                
                tentative_g = g_score[current] + weight
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None, float('inf')
    
    def find_alternative_routes(self, start, end, k=3):
        """Encontra k rotas alternativas"""
        routes = []
        
        for _ in range(k):
            path, cost = self.dijkstra(start, end)
            if path:
                routes.append({'path': path, 'cost': cost})
                # Temporariamente remove arestas do caminho
                for i in range(len(path) - 1):
                    self._disable_edge(path[i], path[i+1])
        
        # Restaura arestas
        for route in routes:
            for i in range(len(route['path']) - 1):
                self._enable_edge(route['path'][i], route['path'][i+1])
        
        return routes
    
    def _disable_edge(self, from_node, to_node):
        """Desabilita temporariamente uma aresta"""
        for i, (neighbor, weight, line_data) in enumerate(self.edges[from_node]):
            if neighbor == to_node:
                self.edges[from_node][i][2]['status'] = 'temp_disabled'
    
    def _enable_edge(self, from_node, to_node):
        """Reabilita aresta"""
        for i, (neighbor, weight, line_data) in enumerate(self.edges[from_node]):
            if neighbor == to_node and line_data['status'] == 'temp_disabled':
                self.edges[from_node][i][2]['status'] = 'active'
    
    def detect_isolated_nodes(self):
        """Detecta nós isolados (BFS)"""
        if not self.nodes:
            return []
        
        visited = set()
        start = next(iter(self.nodes))
        queue = deque([start])
        visited.add(start)
        
        while queue:
            node = queue.popleft()
            for neighbor, _, line_data in self.edges[node]:
                if neighbor not in visited and line_data['status'] == 'active':
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return [node for node in self.nodes if node not in visited]
    
    def get_network_stats(self):
        """Estatísticas da rede"""
        total_load = sum(n['current_load'] for n in self.nodes.values())
        total_capacity = sum(n['capacity'] for n in self.nodes.values())
        overloaded = [nid for nid, n in self.nodes.items() if n['status'] == 'overloaded']
        
        return {
            'node_count': self.node_count,
            'edge_count': self.edge_count,
            'total_load': total_load,
            'total_capacity': total_capacity,
            'utilization': total_load / total_capacity if total_capacity > 0 else 0,
            'overloaded_nodes': len(overloaded),
            'isolated_nodes': len(self.detect_isolated_nodes())
        }
