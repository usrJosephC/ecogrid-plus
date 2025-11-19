"""
Árvore AVL para balanceamento dinâmico da rede elétrica.
Complexidade: O(log n) para inserção, busca e remoção.
"""

class AVLNode:
    def __init__(self, key, data):
        self.key = key  # ID do nó da rede
        self.data = data  # {capacity, current_load, efficiency, ...}
        self.left = None
        self.right = None
        self.height = 1
        self.balance_factor = 0

class AVLTree:
    def __init__(self):
        self.root = None
        self.size = 0
        self.rotations = 0  # Para análise de desempenho
    
    def get_height(self, node):
        """Retorna altura do nó"""
        return node.height if node else 0
    
    def get_balance(self, node):
        """Calcula fator de balanceamento"""
        return self.get_height(node.left) - self.get_height(node.right) if node else 0
    
    def update_height(self, node):
        """Atualiza altura do nó"""
        if node:
            node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))
            node.balance_factor = self.get_balance(node)
    
    def rotate_right(self, z):
        """Rotação simples à direita"""
        self.rotations += 1
        y = z.left
        T3 = y.right
        
        y.right = z
        z.left = T3
        
        self.update_height(z)
        self.update_height(y)
        
        return y
    
    def rotate_left(self, z):
        """Rotação simples à esquerda"""
        self.rotations += 1
        y = z.right
        T2 = y.left
        
        y.left = z
        z.right = T2
        
        self.update_height(z)
        self.update_height(y)
        
        return y
    
    def insert(self, key, data):
        """Insere nó e rebalancea a árvore - O(log n)"""
        self.root = self._insert_recursive(self.root, key, data)
        self.size += 1
    
    def _insert_recursive(self, node, key, data):
        # Inserção normal de BST
        if not node:
            return AVLNode(key, data)
        
        if key < node.key:
            node.left = self._insert_recursive(node.left, key, data)
        elif key > node.key:
            node.right = self._insert_recursive(node.right, key, data)
        else:
            node.data = data  # Atualiza se já existe
            return node
        
        # Atualiza altura
        self.update_height(node)
        
        # Verifica balanceamento
        balance = self.get_balance(node)
        
        # Caso Esquerda-Esquerda
        if balance > 1 and key < node.left.key:
            return self.rotate_right(node)
        
        # Caso Direita-Direita
        if balance < -1 and key > node.right.key:
            return self.rotate_left(node)
        
        # Caso Esquerda-Direita
        if balance > 1 and key > node.left.key:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        
        # Caso Direita-Esquerda
        if balance < -1 and key < node.right.key:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        
        return node
    
    def search(self, key):
        """Busca nó - O(log n)"""
        return self._search_recursive(self.root, key)
    
    def _search_recursive(self, node, key):
        if not node or node.key == key:
            return node.data if node else None
        
        if key < node.key:
            return self._search_recursive(node.left, key)
        return self._search_recursive(node.right, key)
    
    def get_overloaded_nodes(self, threshold=0.9):
        """Retorna nós com carga > threshold"""
        overloaded = []
        self._find_overloaded(self.root, threshold, overloaded)
        return overloaded
    
    def _find_overloaded(self, node, threshold, result):
        if not node:
            return
        
        self._find_overloaded(node.left, threshold, result)
        
        load_ratio = node.data['current_load'] / node.data['capacity']
        if load_ratio > threshold:
            result.append({
                'key': node.key,
                'data': node.data,
                'load_ratio': load_ratio
            })
        
        self._find_overloaded(node.right, threshold, result)
    
    def inorder_traversal(self):
        """Percurso em ordem"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append({'key': node.key, 'data': node.data})
            self._inorder_recursive(node.right, result)
    
    def get_stats(self):
        """Estatísticas da árvore"""
        return {
            'size': self.size,
            'height': self.get_height(self.root),
            'rotations': self.rotations,
            'is_balanced': abs(self.get_balance(self.root)) <= 1
        }
