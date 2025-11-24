"""
Heap de prioridade para classificação de eventos críticos.
Complexidade: O(log n) para inserção e remoção.
"""

import heapq
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

@dataclass(order=True)
class PriorityEvent:
    priority: int  # Menor valor = maior prioridade
    timestamp: datetime = field(compare=False)
    event_type: str = field(compare=False)
    node_id: Any = field(compare=False)
    data: dict = field(compare=False)
    
    def __repr__(self):
        return f"PriorityEvent(priority={self.priority}, type={self.event_type}, node={self.node_id})"

class PriorityHeap:
    def __init__(self):
        self.heap = []
        self.counter = 0  # Para desempate
    
    def push(self, event_type, node_id, data, priority):
        """Insere evento com prioridade - O(log n)"""
        event = PriorityEvent(
            priority=priority,
            timestamp=datetime.now(),
            event_type=event_type,
            node_id=node_id,
            data=data
        )
        heapq.heappush(self.heap, (priority, self.counter, event))
        self.counter += 1
    
    def pop(self):
        """Remove e retorna evento de maior prioridade - O(log n)"""
        if self.heap:
            _, _, event = heapq.heappop(self.heap)
            return event
        return None
    
    def peek(self):
        """Visualiza evento de maior prioridade"""
        if self.heap:
            return self.heap[0][2]
        return None
    
    def is_empty(self):
        """Verifica se heap está vazio"""
        return len(self.heap) == 0
    
    def size(self):
        """Retorna tamanho do heap"""
        return len(self.heap)
    
    def get_critical_events(self, threshold=3):
        """Retorna eventos com prioridade <= threshold"""
        return [event for _, _, event in self.heap if event.priority <= threshold]
    
    def clear(self):
        """Limpa o heap"""
        self.heap.clear()
        self.counter = 0

# Definição de níveis de prioridade
class Priority:
    CRITICAL = 1      # Blackout iminente
    HIGH = 2          # Sobrecarga severa
    MEDIUM = 3        # Sobrecarga moderada
    LOW = 4           # Aviso
    INFO = 5          # Informativo
