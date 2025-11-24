# 🌐 EcoGrid+ 

**Plataforma Inteligente para Redes de Energia Sustentáveis**

Projeto acadêmico de Estruturas de Dados Avançadas que implementa um sistema completo de gerenciamento e otimização de redes elétricas usando algoritmos avançados, Machine Learning e IoT.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estruturas de Dados](#estruturas-de-dados)
- [Algoritmos](#algoritmos)
- [API](#api)
- [Testes](#testes)
- [Sprints](#sprints)

---

## 🎯 Visão Geral

O **EcoGrid+** é uma plataforma de gerenciamento inteligente de redes elétricas que utiliza:

- **Árvores AVL** para balanceamento dinâmico de carga
- **Árvores B+** para persistência eficiente de dados históricos
- **Grafos ponderados** para modelagem da rede de transmissão
- **Algoritmos de roteamento** (Dijkstra e A*) para otimização de fluxo
- **Machine Learning** (PyTorch/LSTM) para previsão de demanda
- **Simulação IoT** para geração de dados em tempo real

### Funcionalidades Principais

✅ Monitoramento em tempo real de consumo energético  
✅ Balanceamento automático de carga  
✅ Detecção e previsão de sobrecargas  
✅ Roteamento otimizado com múltiplas rotas  
✅ Previsão de demanda com IA  
✅ Análise de eficiência e pegada de carbono  
✅ Sugestões de integração de energia renovável  
✅ Interface web interativa com visualização D3.js  

---

## 🚀 Tecnologias

### Backend
- **Python 3.11+**
- **Flask** - API REST
- **PostgreSQL** - Banco de dados
- **SQLAlchemy** - ORM
- **PyTorch** - Machine Learning
- **NumPy/Pandas** - Análise de dados

### Frontend
- **HTML5/CSS3/JavaScript**
- **D3.js** - Visualização de grafos
- **Chart.js** - Gráficos interativos

### DevOps
- **Docker & Docker Compose**
- **Nginx** - Servidor web
- **Pytest** - Testes automatizados

---

## 🏗️ Arquitetura

```bash
ecogrid-plus/
├── backend/
│ ├── app.py # API Flask
│ ├── config.py # Configurações
│ ├── data_structures/ # AVL, B+, Grafo, Fila, Heap
│ ├── algorithms/ # Balanceamento, Roteamento, Eficiência
│ ├── ml/ # Modelo PyTorch e treinamento
│ ├── iot/ # Simulador IoT
│ ├── models/ # Schemas PostgreSQL
│ └── tests/ # Testes unitários
├── frontend/
│ ├── index.html
│ ├── css/style.css
│ └── js/ # API client, visualização, lógica
├── database/
│ └── init.sql # Schema PostgreSQL
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 📦 Instalação

### Opção 1: Docker (Recomendado)
- Clone o repositório
```bash
git clone https://github.com/usrJosephC/ecogrid-plus.git
cd ecogrid-plus
```

- Inicie com Docker Compose
```bash
docker-compose up -d
```

- Acesse:
```bash
Frontend: http://localhost:8080
API: http://localhost:5000
```

### Opção 2: Instalação Manual
1. PostgreSQL
Instale e configure PostgreSQL
```bash 
createdb ecogrid
psql ecogrid < database/init.sql
```

2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure .env
```bash
cp .env.example .env
```

Edite .env com suas credenciais
Execute
```bash
python app.py
```

3. Frontend
Sirva os arquivos frontend com qualquer servidor HTTP
```bash
cd frontend
python -m http.server 8080
```

---

## 💻 Uso

### 1. Inicialize o Sistema
- Via API
```bash
curl -X POST http://localhost:5000/api/init
-H "Content-Type: application/json"
-d '{"num_nodes": 20, "train_ml": true}'
```

- Ou pela interface web
Clique em "🚀 Inicializar Sistema"

### 2. Monitore a Rede

Acesse `http://localhost:8080` para visualizar:
- Dashboard com estatísticas em tempo real
- Visualização interativa da rede
- Gráficos de carga e previsões
- Lista de eventos críticos

### 3. Execute Operações
Balanceamento de carga
`POST /api/balance`

Otimização de eficiência
`POST /api/optimize`

Previsão de demanda
```bash
POST /api/ml/predict
{
"node_id": "CONS_0",
"hours_ahead": 24
}
```

Buscar rota ótima
```bash
POST /api/route
{
"source": "SUB_0",
"destination": "CONS_5",
"algorithm": "dijkstra"
}
```

---

## 🌳 Estruturas de Dados

### 1. Árvore AVL
**Complexidade:** O(log n) para inserção, busca e remoção
```bash
from data_structures.avl_tree import AVLTree

avl = AVLTree()
avl.insert('node_1', {'capacity': 1000, 'load': 750})
node = avl.search('node_1')
overloaded = avl.get_overloaded_nodes(threshold=0.9)
```
**Uso:** Indexação de nós para balanceamento rápido

### 2. Árvore B+
**Complexidade:** O(log n) para operações, O(log n + k) para range queries
```bash
from data_structures.bplus_tree import BPlusTree

bplus = BPlusTree(order=5)
bplus.insert(timestamp, reading)
historical = bplus.range_query(start_date, end_date)
```

**Uso:** Armazenamento de histórico temporal

### 3. Grafo Ponderado
**Complexidade:** Dijkstra O(E log V), A* O(E log V)
```bash
from data_structures.graph import EnergyGraph

graph = EnergyGraph()
graph.add_node('SUB_0', 'substation', 5000)
graph.add_edge('SUB_0', 'TRF_1', distance=10, resistance=0.05)
path, cost = graph.dijkstra('SUB_0', 'CONS_5')
```
**Uso:** Modelagem da topologia da rede

### 4. Fila FIFO
**Complexidade:** O(1) para enqueue/dequeue
```bash
from data_structures.event_queue import EventQueue

queue = EventQueue()
queue.enqueue(Event('overload', 'node_1', data))
event = queue.dequeue()
```
**Uso:** Processamento de eventos em tempo real

### 5. Heap de Prioridade
**Complexidade:** O(log n) para inserção/remoção
```bash
from data_structures.priority_heap import PriorityHeap, Priority

heap = PriorityHeap()
heap.push('failure', 'node_1', data, Priority.CRITICAL)
critical_event = heap.pop()
```
**Uso:** Tratamento de eventos críticos

---

## 🧮 Algoritmos

### 1. Balanceamento de Carga
```bash
balancer = LoadBalancer(avl_tree, graph)
result = balancer.balance_network()
efficiency = balancer.calculate_efficiency()
```

### 2. Roteamento (Dijkstra/A*)
```bash
router = EnergyRouter(graph)
route = router.find_optimal_route('SUB_0', 'CONS_5', 'dijkstra')
redundant = router.find_redundant_paths('SUB_0', 'CONS_5', k=3)
```

### 3. Otimização de Eficiência
```bash
optimizer = EfficiencyOptimizer(graph, avl_tree)
result = optimizer.optimize_network()
carbon = optimizer.calculate_carbon_footprint()
renewable = optimizer.suggest_renewable_integration()
```

## 🤖 Machine Learning

### Modelo LSTM para Previsão de Demanda
```bash
from ml.predictor import EnergyDemandPredictor

predictor = EnergyDemandPredictor()
```
### Treinar
```bash
historical_data = [...] # 90 dias de dados
predictor.train(historical_data, epochs=100)
predictor.save_model('model.pth')
```

### Prever
```bash
recent_data = [...] # Últimas 24h
predictions = predictor.predict(recent_data, hours_ahead=24)
peaks = predictor.predict_peak_times(predictions)
```
**Arquitetura:**
- Input: Sequência temporal de consumo (24h)
- LSTM: 2 camadas, 64 hidden units
- Output: Previsão para próximas 24h
- Métricas: MAE, RMSE, R²

---

## 📡 API

### Endpoints Principais:
POST /api/init # Inicializar sistema
GET /api/nodes # Listar nós
GET /api/nodes/:id # Detalhes do nó
POST /api/nodes # Criar nó
PUT /api/nodes/:id/load # Atualizar carga
POST /api/balance # Balancear rede
POST /api/route # Buscar rota
POST /api/optimize # Otimizar eficiência
POST /api/ml/predict # Prever demanda
POST /api/ml/train # Treinar modelo
GET /api/iot/readings # Leituras IoT
POST /api/iot/simulate-failure # Simular falha
GET /api/events # Listar eventos
GET /api/events/critical # Eventos críticos
GET /api/stats # Estatísticas globais
GET /api/health # Health check
**Documentação completa:** [API.md](docs/API.md)

---

## 🧪 Testes
- Executar testes unitários
```bash
cd backend
pytest tests/ -v
```

- Testes específicos
```bash
pytest tests/test_avl.py
pytest tests/test_bplus.py
```

- Benchmark de performance
```bash
python tests/benchmark.py
```

**Cobertura:**
- Estruturas de dados: Inserção, busca, balanceamento
- Algoritmos: Roteamento, otimização
- Integração: API endpoints

---

## 📅 Sprints

O projeto foi desenvolvido em **5 sprints** de 2 semanas cada:

### Sprint 1: Fundação (Semanas 1-2)
✅ Setup do ambiente  
✅ Implementação AVL e B+  
✅ Estrutura básica do grafo  
✅ Testes unitários  

### Sprint 2: Core Backend (Semanas 3-4)
✅ API Flask completa  
✅ Integração PostgreSQL  
✅ Algoritmos de balanceamento  
✅ Dijkstra e A*  

### Sprint 3: Machine Learning (Semanas 5-6)
✅ Modelo LSTM com PyTorch  
✅ Pipeline de treinamento  
✅ Simulador IoT  
✅ Previsão de demanda  

### Sprint 4: Frontend (Semanas 7-8)
✅ Interface web responsiva  
✅ Visualização D3.js  
✅ Gráficos Chart.js  
✅ Dashboard interativo  

### Sprint 5: Otimização e Deploy (Semanas 9-10)
✅ Análise de eficiência  
✅ Documentação completa  
✅ Docker/Docker Compose  
✅ Testes de integração  

Detalhes: [SPRINTS.md](docs/SPRINTS.md)

---

## 👥 Equipe

- **Líder de Projeto**: Gestão e integração
- **Dev Backend**: Estruturas de dados e algoritmos
- **Dev ML**: Modelo de previsão
- **Dev Frontend**: Interface e visualização
- **QA**: Testes e documentação
- **DevOps**: Infraestrutura e deploy

---

## 📄 Licença

Este projeto é acadêmico e desenvolvido para fins educacionais.

---

## 🙏 Agradecimentos

- Prof. Me. Icaro Ferreira - Orientação
- Comunidade Python/PyTorch
- Documentação D3.js

---

## 📞 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

**EcoGrid+** - Energia inteligente para um futuro sustentável 🌱⚡
