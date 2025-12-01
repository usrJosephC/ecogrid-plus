"""
Grafo para representar a rede elétrica.
"""

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

    # dijkstra, astar iguais aos que você já tinha...

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
