"""
Árvore B+ para persistência em disco e consultas históricas.
Otimizada para armazenamento em blocos e range queries.
"""

class BPlusNode:
    def __init__(self, order, is_leaf=False):
        self.order = order
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []  # Para nós internos
        self.values = []    # Para folhas
        self.next = None    # Linked list nas folhas

class BPlusTree:
    def __init__(self, order=4):
        self.root = BPlusNode(order, is_leaf=True)
        self.order = order
        self.leaf_head = self.root  # Primeira folha para range queries
    
    def insert(self, key, value):
        """Insere par chave-valor - O(log n)"""
        root = self.root
        
        if len(root.keys) == self.order - 1:
            # Root está cheio, precisa dividir
            new_root = BPlusNode(self.order)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, key, value)
    
    def _insert_non_full(self, node, key, value):
        """Insere em nó não cheio"""
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insere na folha
            node.keys.append(None)
            node.values.append(None)
            
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            # Encontra filho apropriado
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if len(node.children[i].keys) == self.order - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, value)
    
    def _split_child(self, parent, index):
        """Divide filho cheio"""
        order = self.order
        child = parent.children[index]
        new_child = BPlusNode(order, is_leaf=child.is_leaf)
        
        mid = order // 2
        
        # Copia segunda metade para novo nó
        new_child.keys = child.keys[mid:]
        child.keys = child.keys[:mid]
        
        if child.is_leaf:
            new_child.values = child.values[mid:]
            child.values = child.values[:mid]
            new_child.next = child.next
            child.next = new_child
        else:
            new_child.children = child.children[mid:]
            child.children = child.children[:mid]
        
        # Insere chave no pai
        parent.keys.insert(index, new_child.keys[0])
        parent.children.insert(index + 1, new_child)
    
    def search(self, key):
        """Busca valor por chave - O(log n)"""
        return self._search_recursive(self.root, key)
    
    def _search_recursive(self, node, key):
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if node.is_leaf:
            if i < len(node.keys) and node.keys[i] == key:
                return node.values[i]
            return None
        else:
            return self._search_recursive(node.children[i], key)
    
    def range_query(self, start_key, end_key):
        """Consulta de intervalo - O(log n + k) onde k é o resultado"""
        # Encontra primeira folha
        node = self._find_leaf(start_key)
        result = []
        
        while node:
            for i, key in enumerate(node.keys):
                if start_key <= key <= end_key:
                    result.append({'key': key, 'value': node.values[i]})
                elif key > end_key:
                    return result
            node = node.next
        
        return result
    
    def _find_leaf(self, key):
        """Encontra folha que contém ou deve conter a chave"""
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node
    
    def get_all_records(self):
        """Retorna todos os registros em ordem"""
        result = []
        node = self.leaf_head
        
        while node:
            for i in range(len(node.keys)):
                result.append({'key': node.keys[i], 'value': node.values[i]})
            node = node.next
        
        return result
