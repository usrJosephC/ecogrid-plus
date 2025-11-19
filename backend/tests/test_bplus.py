"""
Testes para Árvore B+
"""

import pytest
from data_structures.bplus_tree import BPlusTree

class TestBPlusTree:
    def setup_method(self):
        self.bplus = BPlusTree(order=4)
    
    def test_insert_and_search(self):
        """Testa inserção e busca"""
        self.bplus.insert(10, 'value_10')
        assert self.bplus.search(10) == 'value_10'
    
    def test_multiple_inserts(self):
        """Testa múltiplas inserções"""
        for i in range(20):
            self.bplus.insert(i, f'value_{i}')
        
        for i in range(20):
            assert self.bplus.search(i) == f'value_{i}'
    
    def test_range_query(self):
        """Testa consulta de intervalo"""
        for i in range(100):
            self.bplus.insert(i, f'val_{i}')
        
        result = self.bplus.range_query(10, 20)
        assert len(result) == 11  # 10 a 20 inclusive
        assert result[0]['key'] == 10
        assert result[-1]['key'] == 20
    
    def test_get_all_records(self):
        """Testa obtenção de todos os registros"""
        values = [5, 15, 3, 20, 1, 10]
        for val in values:
            self.bplus.insert(val, f'data_{val}')
        
        all_records = self.bplus.get_all_records()
        keys = [r['key'] for r in all_records]
        assert keys == sorted(values)
