"""
Algoritmos de balanceamento de carga usando AVL.
Redistribui energia automaticamente quando há sobrecarga.
"""


class LoadBalancer:
    def __init__(self, avl_tree, graph):
        self.avl = avl_tree
        self.graph = graph
        self.balancing_history = []
    
    def balance_network(self):
        """
        Identifica nós sobrecarregados e redistribui carga.
        Utiliza rotações AVL para otimização.
        """
        overloaded = self.avl.get_overloaded_nodes(threshold=0.9)
        balanced_count = 0
        
        for node_info in overloaded:
            node_id = node_info['key']
            excess_load = node_info['data']['current_load'] - node_info['data']['capacity'] * 0.8
            
            if excess_load > 0:
                success = self._redistribute_load(node_id, excess_load)
                if success:
                    balanced_count += 1
        
        return {
            'overloaded_nodes': len(overloaded),
            'balanced': balanced_count,
            'success_rate': balanced_count / len(overloaded) if overloaded else 1.0
        }
    
    def _redistribute_load(self, source_node, load_to_transfer):
        """
        Redistribui carga para nós vizinhos com capacidade.
        """
        neighbors = self.graph.edges[source_node]
        available_neighbors = []
        
        # Encontra vizinhos com capacidade disponível
        for neighbor_id, _, line_data in neighbors:
            if line_data['status'] != 'active':
                continue
            
            neighbor_data = self.avl.search(neighbor_id)
            if not neighbor_data:
                continue
            
            available_capacity = neighbor_data['capacity'] - neighbor_data['current_load']
            if available_capacity > 0:
                available_neighbors.append({
                    'id': neighbor_id,
                    'available': available_capacity,
                    'efficiency': neighbor_data['efficiency']
                })
        
        if not available_neighbors:
            return False
        
        # Ordena por eficiência
        available_neighbors.sort(key=lambda x: x['efficiency'], reverse=True)
        
        # Distribui carga
        remaining_load = load_to_transfer
        transfers = []
        
        for neighbor in available_neighbors:
            if remaining_load <= 0:
                break
            
            transfer_amount = min(remaining_load, neighbor['available'])
            transfers.append({
                'from': source_node,
                'to': neighbor['id'],
                'amount': transfer_amount
            })
            
            remaining_load -= transfer_amount
        
        # Aplica transferências
        for transfer in transfers:
            self._apply_transfer(transfer)
        
        self.balancing_history.append({
            'source': source_node,
            'transfers': transfers,
            'total_transferred': load_to_transfer - remaining_load
        })
        
        return remaining_load < load_to_transfer * 0.1
    
    def _apply_transfer(self, transfer):
        """Aplica transferência de carga"""
        # Atualiza nó origem
        source_data = self.avl.search(transfer['from'])
        source_data['current_load'] -= transfer['amount']
        self.avl.insert(transfer['from'], source_data)
        self.graph.update_load(transfer['from'], source_data['current_load'])
        
        # Atualiza nó destino
        dest_data = self.avl.search(transfer['to'])
        dest_data['current_load'] += transfer['amount']
        self.avl.insert(transfer['to'], dest_data)
        self.graph.update_load(transfer['to'], dest_data['current_load'])
    
    def calculate_efficiency(self):
        """
        Calcula eficiência global da rede.
        """
        all_nodes = self.avl.inorder_traversal()
        
        if not all_nodes:
            return {
                'global_efficiency': 0,
                'total_efficiency': 0,
                'total_losses': 0,
                'efficiency_ratio': 0
            }
        
        total_efficiency = 0
        total_load = 0
        
        for node in all_nodes:
            data = node['data']
            load = data['current_load']
            efficiency = data['efficiency']
            
            total_efficiency += load * efficiency
            total_load += load
        
        # Calcula perdas
        total_losses = total_load - total_efficiency if total_load > 0 else 0
        efficiency_ratio = total_efficiency / total_load if total_load > 0 else 0
        
        return {
            'global_efficiency': round(total_efficiency, 2),
            'total_efficiency': round(total_efficiency, 2),
            'total_losses': round(total_losses, 2),
            'efficiency_ratio': round(efficiency_ratio, 4)
        }
    
    def get_balancing_stats(self):
        """Retorna estatísticas de balanceamento"""
        if not self.balancing_history:
            return {'total_operations': 0}
        
        total_transferred = sum(
            op['total_transferred'] for op in self.balancing_history
        )
        
        return {
            'total_operations': len(self.balancing_history),
            'total_load_transferred': total_transferred,
            'avg_transfer_per_operation': total_transferred / len(self.balancing_history),
            'recent_operations': self.balancing_history[-5:]
        }
