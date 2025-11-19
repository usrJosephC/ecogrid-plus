"""
Heurísticas de eficiência energética.
Implementa algoritmos de otimização para minimizar perdas.
"""

import numpy as np

class EfficiencyOptimizer:
    def __init__(self, graph, avl_tree):
        self.graph = graph
        self.avl = avl_tree
        self.optimization_history = []
    
    def optimize_network(self):
        """
        Otimiza rede usando heurística gulosa.
        Prioriza nós de alta eficiência para distribuição.
        """
        all_nodes = self.avl.inorder_traversal()
        
        # Ordena por eficiência
        sorted_nodes = sorted(
            all_nodes,
            key=lambda x: x['data']['efficiency'],
            reverse=True
        )
        
        improvements = []
        
        for node in sorted_nodes:
            node_id = node['key']
            data = node['data']
            
            # Se nó eficiente está subutilizado, tenta atrair carga
            utilization = data['current_load'] / data['capacity']
            
            if utilization < 0.6 and data['efficiency'] > 0.85:
                improvement = self._attract_load_to_efficient_node(node_id, data)
                if improvement:
                    improvements.append(improvement)
        
        total_improvement = sum(imp['efficiency_gain'] for imp in improvements)
        
        result = {
            'optimizations_performed': len(improvements),
            'total_efficiency_gain': total_improvement,
            'details': improvements
        }
        
        self.optimization_history.append(result)
        return result
    
    def _attract_load_to_efficient_node(self, target_node, target_data):
        """
        Transfere carga de nós menos eficientes para nó eficiente.
        """
        available_capacity = target_data['capacity'] - target_data['current_load']
        if available_capacity <= 0:
            return None
        
        neighbors = self.graph.edges[target_node]
        transfers = []
        total_transferred = 0
        
        for neighbor_id, weight, line_data in neighbors:
            if line_data['status'] != 'active':
                continue
            
            neighbor_data = self.avl.search(neighbor_id)
            if not neighbor_data:
                continue
            
            # Só transfere de nós menos eficientes
            if neighbor_data['efficiency'] < target_data['efficiency']:
                # Calcula quanto pode transferir
                transferable = min(
                    neighbor_data['current_load'] * 0.2,  # Max 20% da carga
                    available_capacity - total_transferred
                )
                
                if transferable > 0:
                    transfers.append({
                        'from': neighbor_id,
                        'to': target_node,
                        'amount': transferable,
                        'efficiency_from': neighbor_data['efficiency'],
                        'efficiency_to': target_data['efficiency']
                    })
                    total_transferred += transferable
                    
                    if total_transferred >= available_capacity:
                        break
        
        # Aplica transferências
        for transfer in transfers:
            self._apply_efficiency_transfer(transfer)
        
        if transfers:
            efficiency_gain = sum(
                t['amount'] * (t['efficiency_to'] - t['efficiency_from'])
                for t in transfers
            )
            
            return {
                'target_node': target_node,
                'transfers': transfers,
                'total_transferred': total_transferred,
                'efficiency_gain': efficiency_gain
            }
        
        return None
    
    def _apply_efficiency_transfer(self, transfer):
        """Aplica transferência de otimização"""
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
    
    def calculate_carbon_footprint(self):
        """
        Estima pegada de carbono baseada em eficiência.
        Menor eficiência = maior emissão de CO2.
        """
        all_nodes = self.avl.inorder_traversal()
        total_co2 = 0
        
        # Fator de emissão: kg CO2 / kWh
        EMISSION_FACTOR = 0.5  # Valor médio
        
        for node in all_nodes:
            data = node['data']
            load = data['current_load']
            efficiency = data['efficiency']
            
            # Energia desperdiçada gera mais CO2
            wasted_energy = load * (1 - efficiency)
            co2 = wasted_energy * EMISSION_FACTOR
            total_co2 += co2
        
        return {
            'total_co2_kg': total_co2,
            'co2_per_kwh': total_co2 / sum(n['data']['current_load'] for n in all_nodes) if all_nodes else 0,
            'efficiency_class': self._get_efficiency_class(total_co2)
        }
    
    def _get_efficiency_class(self, co2_total):
        """Classifica eficiência em A-E"""
        if co2_total < 100:
            return 'A'
        elif co2_total < 250:
            return 'B'
        elif co2_total < 500:
            return 'C'
        elif co2_total < 1000:
            return 'D'
        else:
            return 'E'
    
    def suggest_renewable_integration(self):
        """
        Sugere pontos ideais para integração de energia renovável.
        Prioriza nós com:
        - Alta demanda
        - Baixa eficiência atual
        - Boa conectividade
        """
        all_nodes = self.avl.inorder_traversal()
        candidates = []
        
        for node in all_nodes:
            node_id = node['key']
            data = node['data']
            
            # Calcula score de viabilidade
            demand_score = data['current_load'] / data['capacity']
            efficiency_score = 1 - data['efficiency']
            connectivity_score = self.graph.nodes[node_id]['connections'] / 10
            
            total_score = (demand_score * 0.4 + 
                          efficiency_score * 0.4 + 
                          connectivity_score * 0.2)
            
            if total_score > 0.5:
                candidates.append({
                    'node_id': node_id,
                    'score': total_score,
                    'current_load': data['current_load'],
                    'efficiency': data['efficiency'],
                    'recommended_source': self._recommend_renewable_type(data)
                })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)[:5]
    
    def _recommend_renewable_type(self, node_data):
        """Recomenda tipo de energia renovável"""
        load = node_data['current_load']
        
        if load > 500:
            return 'solar_farm'
        elif load > 200:
            return 'wind_turbine'
        else:
            return 'solar_panels'
    
    def get_optimization_report(self):
        """Relatório completo de otimizações"""
        if not self.optimization_history:
            return {'total_optimizations': 0}
        
        total_gain = sum(opt['total_efficiency_gain'] for opt in self.optimization_history)
        total_ops = sum(opt['optimizations_performed'] for opt in self.optimization_history)
        
        return {
            'total_optimization_cycles': len(self.optimization_history),
            'total_operations': total_ops,
            'total_efficiency_gain': total_gain,
            'avg_gain_per_cycle': total_gain / len(self.optimization_history),
            'recent_optimizations': self.optimization_history[-3:]
        }
