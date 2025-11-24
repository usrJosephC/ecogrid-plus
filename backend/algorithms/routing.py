"""
Algoritmos de roteamento otimizado para fluxo de energia.
Implementa Dijkstra e A* para encontrar melhores caminhos.
"""

import heapq
from collections import defaultdict

class EnergyRouter:
    def __init__(self, graph):
        self.graph = graph
        self.routing_cache = {}  # Cache de rotas calculadas
        self.route_history = []
    
    def find_optimal_route(self, source, destination, algorithm='dijkstra'):
        """
        Encontra rota ótima considerando perdas e eficiência.
        Retorna: dict com caminho, custo, tempo de execução
        """
        import time
        
        cache_key = f"{source}_{destination}_{algorithm}"
        if cache_key in self.routing_cache:
            return self.routing_cache[cache_key]
        
        start_time = time.time()
        
        try:
            if algorithm == 'dijkstra':
                path, cost = self.graph.dijkstra(source, destination)
            elif algorithm == 'astar':
                path, cost = self.graph.astar(source, destination)
            else:
                raise ValueError(f"Algoritmo desconhecido: {algorithm}")
            
            execution_time = time.time() - start_time
            
            # CORREÇÃO: Converte Infinity para None
            if cost == float('inf'):
                cost = None
            
            result = {
                'path': path if path else [],
                'cost': cost,
                'algorithm': algorithm,
                'execution_time': execution_time,
                'hops': len(path) - 1 if path else 0,
                'found': len(path) > 0  # ← ADICIONA FLAG
            }
            
            if result['found']:
                self.routing_cache[cache_key] = result
                self.route_history.append(result)
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'path': [],
                'cost': None,
                'algorithm': algorithm,
                'execution_time': 0,
                'hops': 0,
                'found': False,
                'error': str(e)
            }
    
    def find_redundant_paths(self, source, destination, k=3):
        """
        Encontra k caminhos redundantes para failover.
        Usa Yen's algorithm simplificado.
        """
        paths = self.graph.find_alternative_routes(source, destination, k)
        
        redundant_paths = []
        for i, route in enumerate(paths):
            redundant_paths.append({
                'path_id': i + 1,
                'nodes': route['path'],
                'cost': route['cost'],
                'reliability': self._calculate_path_reliability(route['path'])
            })
        
        return redundant_paths
    
    def _calculate_path_reliability(self, path):
        """
        Calcula confiabilidade do caminho baseado em:
        - Status dos nós
        - Capacidade das linhas
        - Histórico de falhas
        """
        if not path or len(path) < 2:
            return 0.0
        
        reliability = 1.0
        
        for i in range(len(path) - 1):
            node = self.graph.nodes[path[i]]
            
            # Penaliza nós sobrecarregados
            if node['status'] == 'overloaded':
                reliability *= 0.5
            elif node['status'] == 'warning':
                reliability *= 0.8
            
            # Penaliza baixa eficiência
            reliability *= node['efficiency']
        
        return reliability
    
    def calculate_power_loss(self, path):
        """
        Calcula perda de potência ao longo do caminho.
        P_loss = I² * R * distance
        """
        if not path or len(path) < 2:
            return 0.0
        
        total_loss = 0.0
        
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            
            # Encontra aresta entre nós
            for neighbor, weight, line_data in self.graph.edges[current_node]:
                if neighbor == next_node:
                    # Assume corrente proporcional à carga
                    current = self.graph.nodes[current_node]['current_load'] / 220  # I = P/V
                    resistance = line_data['resistance']
                    distance = line_data['distance']
                    
                    loss = (current ** 2) * resistance * distance
                    total_loss += loss
                    break
        
        return total_loss
    
    def suggest_line_upgrades(self, threshold_loss=50):
        """
        Sugere upgrades de linhas com alta perda.
        """
        suggestions = []
        
        for node_id, neighbors in self.graph.edges.items():
            for neighbor, weight, line_data in neighbors:
                if node_id < neighbor:  # Evita duplicatas
                    path = [node_id, neighbor]
                    loss = self.calculate_power_loss(path)
                    
                    if loss > threshold_loss:
                        suggestions.append({
                            'from': node_id,
                            'to': neighbor,
                            'current_loss': loss,
                            'distance': line_data['distance'],
                            'suggested_action': 'upgrade_conductor' if loss > 100 else 'maintenance'
                        })
        
        return sorted(suggestions, key=lambda x: x['current_loss'], reverse=True)
    
    def clear_cache(self):
        """Limpa cache de rotas"""
        self.routing_cache.clear()
    
    def get_routing_stats(self):
        """Estatísticas de roteamento"""
        if not self.route_history:
            return {'total_routes': 0}
        
        avg_time = sum(r['execution_time'] for r in self.route_history) / len(self.route_history)
        avg_hops = sum(r['hops'] for r in self.route_history) / len(self.route_history)
        
        return {
            'total_routes': len(self.route_history),
            'cache_size': len(self.routing_cache),
            'avg_execution_time': avg_time,
            'avg_hops': avg_hops,
            'algorithms_used': list(set(r['algorithm'] for r in self.route_history))
        }
