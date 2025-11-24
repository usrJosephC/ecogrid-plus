"""
Benchmark de performance das estruturas de dados.
Análise de complexidade Big-O.
"""

import time
import random
import matplotlib.pyplot as plt
from data_structures.avl_tree import AVLTree
from data_structures.bplus_tree import BPlusTree
from data_structures.graph import EnergyGraph

def benchmark_avl_insert():
    """Benchmark de inserção AVL - O(log n)"""
    sizes = [100, 500, 1000, 5000, 10000]
    times = []
    
    for n in sizes:
        avl = AVLTree()
        values = random.sample(range(n * 10), n)
        
        start = time.time()
        for val in values:
            avl.insert(val, {'data': val})
        end = time.time()
        
        times.append(end - start)
        print(f"AVL Insert {n} nodes: {times[-1]:.4f}s")
    
    return sizes, times

def benchmark_avl_search():
    """Benchmark de busca AVL - O(log n)"""
    sizes = [100, 500, 1000, 5000, 10000]
    times = []
    
    for n in sizes:
        avl = AVLTree()
        values = list(range(n))
        random.shuffle(values)
        
        for val in values:
            avl.insert(val, {'data': val})
        
        # Busca valores aleatórios
        search_values = random.sample(values, min(1000, n))
        
        start = time.time()
        for val in search_values:
            avl.search(val)
        end = time.time()
        
        times.append(end - start)
        print(f"AVL Search {len(search_values)} in {n} nodes: {times[-1]:.4f}s")
    
    return sizes, times

def benchmark_dijkstra():
    """Benchmark do algoritmo de Dijkstra - O(E log V)"""
    sizes = [10, 50, 100, 200, 500]
    times = []
    
    for n in sizes:
        graph = EnergyGraph()
        
        # Cria grafo denso
        for i in range(n):
            graph.add_node(f'node_{i}', 'consumer', 500)
        
        # Adiciona arestas (grafo conectado)
        for i in range(n):
            for j in range(i + 1, min(i + 5, n)):
                graph.add_edge(f'node_{i}', f'node_{j}', random.uniform(1, 10))
        
        start = time.time()
        path, cost = graph.dijkstra('node_0', f'node_{n-1}')
        end = time.time()
        
        times.append(end - start)
        print(f"Dijkstra {n} nodes: {times[-1]:.4f}s")
    
    return sizes, times

def run_all_benchmarks():
    """Executa todos os benchmarks"""
    print("=" * 50)
    print("BENCHMARK DE PERFORMANCE - EcoGrid+")
    print("=" * 50)
    
    print("\n1. AVL Tree - Insert")
    avl_insert_sizes, avl_insert_times = benchmark_avl_insert()
    
    print("\n2. AVL Tree - Search")
    avl_search_sizes, avl_search_times = benchmark_avl_search()
    
    print("\n3. Dijkstra Algorithm")
    dijkstra_sizes, dijkstra_times = benchmark_dijkstra()
    
    print("\n" + "=" * 50)
    print("BENCHMARK CONCLUÍDO!")
    print("=" * 50)
    
    # Salva resultados
    with open('benchmark_results.txt', 'w') as f:
        f.write("EcoGrid+ Performance Benchmark\n")
        f.write("=" * 50 + "\n\n")
        f.write("AVL Insert:\n")
        for size, time_val in zip(avl_insert_sizes, avl_insert_times):
            f.write(f"  {size} nodes: {time_val:.4f}s\n")
        f.write("\nAVL Search:\n")
        for size, time_val in zip(avl_search_sizes, avl_search_times):
            f.write(f"  {size} nodes: {time_val:.4f}s\n")
        f.write("\nDijkstra:\n")
        for size, time_val in zip(dijkstra_sizes, dijkstra_times):
            f.write(f"  {size} nodes: {time_val:.4f}s\n")

if __name__ == '__main__':
    run_all_benchmarks()
