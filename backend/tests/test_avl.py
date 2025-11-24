"""
Testes unitários para Árvore AVL
"""

import pytest
from data_structures.avl_tree import AVLTree

class TestAVLTree:
    def setup_method(self):
        """Setup executado antes de cada teste"""
        self.avl = AVLTree()
    
    def test_insert_single_node(self):
        """Testa inserção de um único nó"""
        self.avl.insert(10, {'data': 'test'})
        assert self.avl.size == 1
        assert self.avl.search(10) == {'data': 'test'}
    
    def test_insert_multiple_nodes(self):
        """Testa inserção de múltiplos nós"""
        values = [50, 30, 70, 20, 40, 60, 80]
        for val in values:
            self.avl.insert(val, {'value': val})
        
        assert self.avl.size == len(values)
        assert self.avl.get_stats()['is_balanced']
    
    def test_rotation_right(self):
        """Testa rotação à direita"""
        # Inserção que causa desbalanceamento à esquerda
        self.avl.insert(30, {'val': 30})
        self.avl.insert(20, {'val': 20})
        self.avl.insert(10, {'val': 10})
        
        assert self.avl.rotations > 0
        assert self.avl.get_stats()['is_balanced']
    
    def test_rotation_left(self):
        """Testa rotação à esquerda"""
        self.avl.insert(10, {'val': 10})
        self.avl.insert(20, {'val': 20})
        self.avl.insert(30, {'val': 30})
        
        assert self.avl.rotations > 0
        assert self.avl.get_stats()['is_balanced']
    
    def test_search_existing(self):
        """Testa busca de chave existente"""
        self.avl.insert(42, {'answer': 'universe'})
        result = self.avl.search(42)
        assert result == {'answer': 'universe'}
    
    def test_search_non_existing(self):
        """Testa busca de chave inexistente"""
        result = self.avl.search(999)
        assert result is None
    
    def test_inorder_traversal(self):
        """Testa percurso em ordem"""
        values = [50, 30, 70, 20, 40]
        for val in values:
            self.avl.insert(val, {'v': val})
        
        result = self.avl.inorder_traversal()
        keys = [item['key'] for item in result]
        assert keys == sorted(values)
    
    def test_get_overloaded_nodes(self):
        """Testa identificação de nós sobrecarregados"""
        self.avl.insert(1, {'capacity': 100, 'current_load': 95})
        self.avl.insert(2, {'capacity': 100, 'current_load': 50})
        self.avl.insert(3, {'capacity': 100, 'current_load': 92})
        
        overloaded = self.avl.get_overloaded_nodes(threshold=0.9)
        assert len(overloaded) == 2
    
    def test_height_balance(self):
        """Testa que a árvore mantém altura balanceada"""
        # Insere 100 nós
        for i in range(100):
            self.avl.insert(i, {'value': i})
        
        height = self.avl.get_stats()['height']
        # Altura de AVL com n nós: O(log n)
        # Para 100 nós, altura deve ser <= 10
        assert height <= 10
        assert self.avl.get_stats()['is_balanced']
    
    def test_update_existing_key(self):
        """Testa atualização de nó existente"""
        self.avl.insert(10, {'old': 'data'})
        self.avl.insert(10, {'new': 'data'})
        
        assert self.avl.size == 1  # Não aumentou o tamanho
        assert self.avl.search(10) == {'new': 'data'}
