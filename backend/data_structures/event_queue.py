"""
Fila FIFO para gerenciamento de eventos em tempo real.
Complexidade: O(1) para enqueue e dequeue.
"""

from collections import deque
from datetime import datetime

class Event:
    def __init__(self, event_type, node_id, data, priority=1):
        self.event_type = event_type  # 'overload', 'failure', 'recovery'
        self.node_id = node_id
        self.data = data
        self.priority = priority
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"Event({self.event_type}, node={self.node_id}, priority={self.priority})"

class EventQueue:
    def __init__(self, max_size=10000):
        self.queue = deque(maxlen=max_size)
        self.processed = 0
        self.dropped = 0
    
    def enqueue(self, event):
        """Adiciona evento na fila - O(1)"""
        if len(self.queue) == self.queue.maxlen:
            self.dropped += 1
        self.queue.append(event)
    
    def dequeue(self):
        """Remove e retorna próximo evento - O(1)"""
        if self.queue:
            self.processed += 1
            return self.queue.popleft()
        return None
    
    def peek(self):
        """Visualiza próximo evento sem remover"""
        return self.queue[0] if self.queue else None
    
    def is_empty(self):
        """Verifica se fila está vazia"""
        return len(self.queue) == 0
    
    def size(self):
        """Retorna tamanho atual"""
        return len(self.queue)
    
    def clear(self):
        """Limpa a fila"""
        self.queue.clear()
    
    def get_events_by_type(self, event_type):
        """Filtra eventos por tipo"""
        return [e for e in self.queue if e.event_type == event_type]
    
    def get_stats(self):
        """Estatísticas da fila"""
        return {
            'current_size': len(self.queue),
            'max_size': self.queue.maxlen,
            'processed': self.processed,
            'dropped': self.dropped,
            'utilization': len(self.queue) / self.queue.maxlen
        }
