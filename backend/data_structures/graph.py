"""
Grafo para representar a rede elétrica.
"""
import heapq
import math

class EnergyGraph:
    def __init__(self):
        self.nodes = {}  # {node_id: {type, capacity, current_load, efficiency}}
        self.edges = {}  # {node_id: [(neighbor_id, weight, line_data)]}
        self.routing_stats = {
            "total_routes": 0
        }

    def add_node(self, node_id, node_type, capacity, efficiency=1.0, current_load=0):
        self.nodes[node_id] = {
            "type": node_type,
            "capacity": capacity,
            "current_load": current_load,
            "efficiency": efficiency,
        }
        if node_id not in self.edges:
            self.edges[node_id] = []

    def add_edge(self, from_node, to_node, distance, resistance=0.1, status="active"):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Nós {from_node} ou {to_node} não existem")

        weight = distance * (1 + resistance)
        line_data = {
            "distance": distance,
            "resistance": resistance,
            "status": status,
            "capacity": 1000,
        }

        if from_node not in self.edges:
            self.edges[from_node] = []
        if to_node not in self.edges:
            self.edges[to_node] = []

        self.edges[from_node].append((to_node, weight, line_data))
        self.edges[to_node].append((from_node, weight, line_data))

    def update_load(self, node_id, new_load):
        if node_id in self.nodes:
            self.nodes[node_id]["current_load"] = new_load

    def get_neighbors(self, node_id):
        return self.edges.get(node_id, [])

    def dijkstra(self, source, target):
        """Menor caminho em termos de peso total."""
        if source not in self.nodes or target not in self.nodes:
            return [], float("inf")

        dist = {node: float("inf") for node in self.nodes}
        prev = {node: None for node in self.nodes}
        dist[source] = 0.0

        heap = [(0.0, source)]

        while heap:
            current_dist, u = heapq.heappop(heap)
            if current_dist > dist[u]:
                continue

            if u == target:
                break

            for v, weight, line_data in self.get_neighbors(u):
                # Ignora linhas inativas
                if line_data.get("status", "active") != "active":
                    continue

                alt = current_dist + weight
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, (alt, v))

        if dist[target] == float("inf"):
            return [], float("inf")

        # Reconstrói caminho
        path = []
        node = target
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

        # atualiza stats básicos
        self.routing_stats["total_routes"] = self.routing_stats.get("total_routes", 0) + 1

        return path, dist[target]

    def astar(self, source, target):
        """Versão A* simples com heurística neutra (equivale a Dijkstra)."""
        # Se quiser algo mais sofisticado, pode usar distância mínima das arestas
        def heuristic(u, v):
            return 0.0  # sem info geométrica, mantém neutro

        if source not in self.nodes or target not in self.nodes:
            return [], float("inf")

        g_score = {node: float("inf") for node in self.nodes}
        f_score = {node: float("inf") for node in self.nodes}
        came_from = {node: None for node in self.nodes}

        g_score[source] = 0.0
        f_score[source] = heuristic(source, target)

        open_set = [(f_score[source], source)]

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == target:
                # Reconstrói caminho
                path = []
                node = current
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()

                self.routing_stats["total_routes"] = self.routing_stats.get("total_routes", 0) + 1
                return path, g_score[target]

            for neighbor, weight, line_data in self.get_neighbors(current):
                if line_data.get("status", "active") != "active":
                    continue

                tentative_g = g_score[current] + weight
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, target)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return [], float("inf")

    def get_network_stats(self):
        total_capacity = 0
        total_load = 0
        overloaded = 0

        for node_id, node_data in self.nodes.items():
            total_capacity += node_data.get("capacity", 0)
            total_load += node_data.get("current_load", 0)

            utilization = node_data.get("current_load", 0) / max(
                node_data.get("capacity", 1), 1
            )
            if utilization > 0.9:
                overloaded += 1

        utilization = total_load / total_capacity if total_capacity > 0 else 0

        isolated = sum(
            1 for node_id in self.nodes if len(self.edges.get(node_id, [])) == 0
        )

        return {
            "node_count": len(self.nodes),
            "edge_count": sum(len(edges) for edges in self.edges.values()) // 2,
            "total_capacity": total_capacity,
            "total_load": total_load,
            "utilization": utilization,
            "overloaded_nodes": overloaded,
            "isolated_nodes": isolated,
        }

    def get_routing_stats(self):
        return self.routing_stats
