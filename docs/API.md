# 📡 Documentação da API - EcoGrid+

## Base URL
`http://localhost:5000/api`

---

## 🔐 Autenticação

Atualmente a API não requer autenticação. Em produção, implemente JWT ou OAuth2.

---

## 📋 Endpoints

### Sistema

#### Health Check
Verifica status da API.
`GET /api/health`
**Response 200:**
```bash
{
"status": "healthy",
"initialized": true,
"timestamp": "2025-11-19T15:30:00"
}
```

---

#### Inicializar Sistema
Inicializa a rede elétrica com nós de exemplo e treina modelo ML.
`POST /api/init`
**Request Body:**
```bash
{
"num_nodes": 20,
"train_ml": true
}
```
**Response 200:**
```bash
{
"success": true,
"message": "Sistema inicializado com sucesso",
"network_stats": {
"node_count": 20,
"edge_count": 35,
"total_load": 18500.5,
"total_capacity": 32000.0,
"utilization": 0.578,
"overloaded_nodes": 2
},
"avl_stats": {
"size": 20,
"height": 5,
"rotations": 8,
"is_balanced": true
},
"ml_training": {
"final_loss": 0.0234,
"epochs": 50,
"validation": {
"mse": 234.5,
"mae": 15.3,
"rmse": 15.3,
"r2_score": 0.88,
"accuracy": 0.92
}
},
"timestamp": "2025-11-19T15:30:00"
}
```

---

#### Estatísticas Globais
Retorna estatísticas completas do sistema.
`GET /api/stats`
**Response 200:**
```bash
{
"success": true,
"stats": {
"network": {
"node_count": 20,
"edge_count": 35,
"total_load": 18500.5,
"total_capacity": 32000.0,
"utilization": 0.578,
"overloaded_nodes": 2,
"isolated_nodes": 0
},
"avl_tree": {
"size": 20,
"height": 5,
"rotations": 8,
"is_balanced": true
},
"event_queue": {
"current_size": 12,
"max_size": 10000,
"processed": 145,
"dropped": 0,
"utilization": 0.0012
},
"priority_heap": {
"size": 3
},
"balancing": {
"total_operations": 8,
"total_load_transferred": 1250.5,
"avg_transfer_per_operation": 156.31
},
"routing": {
"total_routes": 23,
"cache_size": 15,
"avg_execution_time": 0.0023,
"avg_hops": 3.2
},
"iot": {
"total_sensors": 20,
"active": 19,
"failed": 1
}
}
}
```

---

### Nós (Nodes)

#### Listar Todos os Nós
Lista todos os nós da rede em ordem (AVL inorder traversal).
`GET /api/nodes`
**Response 200:**
```bash
{
"success": true,
"count": 20,
"nodes": [
{
"key": "CONS_0",
"data": {
"capacity": 500.0,
"current_load": 350.5,
"efficiency": 0.85,
"type": "consumer"
}
},
{
"key": "SUB_0",
"data": {
"capacity": 5000.0,
"current_load": 3800.2,
"efficiency": 0.95,
"type": "substation"
}
}
],
"tree_stats": {
"size": 20,
"height": 5,
"is_balanced": true
}
}
```

---

#### Obter Detalhes de um Nó
Retorna informações detalhadas de um nó específico.
`GET /api/nodes/:node_id`
**Params:**
- `node_id` (string) - ID do nó (ex: "SUB_0", "CONS_5")

**Response 200:**
```bash
{
"success": true,
"node_id": "SUB_0",
"data": {
"capacity": 5000.0,
"current_load": 3800.2,
"efficiency": 0.95,
"type": "substation"
},
"sensor_reading": {
"node_id": "SUB_0",
"timestamp": "2025-11-19T15:30:00",
"load": 3805.3,
"voltage": 222.5,
"current": 17.1,
"power_factor": 0.92,
"frequency": 60.2,
"temperature": 32.5,
"status": "active"
},
"neighbors": ["TRF_0", "TRF_1", "TRF_2"]
}
```
**Response 404:**
```bash
{
"success": false,
"error": "Nó não encontrado"
}
```

---

#### Criar Novo Nó
Adiciona um novo nó à rede.
`POST /api/nodes`
**Request Body:**
```bash
{
"node_id": "CONS_10",
"type": "consumer",
"capacity": 600.0,
"efficiency": 0.85
}
```
**Response 201:**
```bash
{
"success": true,
"message": "Nó criado com sucesso",
"node_id": "CONS_10"
}
```
**Response 400:**
```bash
{
"success": false,
"error": "node_id obrigatório"
}
```

---

#### Atualizar Carga de um Nó
Atualiza a carga atual de um nó.
`PUT /api/nodes/:node_id/load`
**Request Body:**
```bash
{
"load": 450.5
}
```
**Response 200:**
```bash
{
"success": true,
"node_id": "CONS_0",
"new_load": 450.5,
"capacity": 500.0,
"utilization": 0.901
}
```

---

### Balanceamento

#### Balancear Rede
Executa algoritmo de balanceamento de carga na rede.
`POST /api/balance`
**Response 200:**
```bash
{
"success": true,
"balancing": {
"overloaded_nodes": 3,
"balanced": 3,
"success_rate": 1.0
},
"efficiency": {
"global_efficiency": 15234.7,
"total_efficiency": 16890.2,
"total_losses": 1655.5,
"efficiency_ratio": 0.902
},
"timestamp": "2025-11-19T15:30:00"
}
```

---

#### Estatísticas de Balanceamento
Retorna histórico de operações de balanceamento.
`GET /api/balance/stats`
**Response 200:**
```bash
{
"success": true,
"stats": {
"total_operations": 8,
"total_load_transferred": 1250.5,
"avg_transfer_per_operation": 156.31,
"recent_operations": [
{
"source": "SUB_0",
"transfers": [
{
"from": "SUB_0",
"to": "TRF_1",
"amount": 200.5
}
],
"total_transferred": 200.5
}
]
}
}
```

---

### Roteamento

#### Buscar Rota Ótima
Encontra caminho de menor custo entre dois nós.
`POST /api/route`
**Request Body:**
```bash
{
"source": "SUB_0",
"destination": "CONS_5",
"algorithm": "dijkstra"
}
```
**Params:**
- `algorithm` (string) - "dijkstra" ou "astar"

**Response 200:**
```bash
{
"success": true,
"route": {
"path": ["SUB_0", "TRF_1", "CONS_5"],
"cost": 2.45,
"algorithm": "dijkstra",
"execution_time": 0.0023,
"hops": 2,
"power_loss": 12.3
}
}
```

---

#### Buscar Rotas Redundantes
Encontra k rotas alternativas para failover.
`POST /api/route/redundant`
**Request Body:**
```bash
{
"source": "SUB_0",
"destination": "CONS_5",
"k": 3
}
```
**Response 200:**
```bash
{
"success": true,
"count": 3,
"routes": [
{
"path_id": 1,
"nodes": ["SUB_0", "TRF_1", "CONS_5"],
"cost": 2.45,
"reliability": 0.92
},
{
"path_id": 2,
"nodes": ["SUB_0", "TRF_2", "TRF_1", "CONS_5"],
"cost": 3.12,
"reliability": 0.87
},
{
"path_id": 3,
"nodes": ["SUB_0", "TRF_0", "TRF_2", "TRF_1", "CONS_5"],
"cost": 4.23,
"reliability": 0.81
}
]
}
```

---

### Otimização

#### Otimizar Eficiência
Executa otimização de eficiência energética.
`POST /api/optimize`
**Response 200:**
```bash
{
"success": true,
"optimization": {
"optimizations_performed": 5,
"total_efficiency_gain": 234.5,
"details": [
{
"target_node": "TRF_1",
"transfers": [],
"total_transferred": 150.0,
"efficiency_gain": 45.2
}
]
},
"carbon_footprint": {
"total_co2_kg": 234.5,
"co2_per_kwh": 0.012,
"efficiency_class": "B"
},
"renewable_suggestions": [
{
"node_id": "CONS_3",
"score": 0.87,
"current_load": 450.0,
"efficiency": 0.78,
"recommended_source": "solar_panels"
}
],
"timestamp": "2025-11-19T15:30:00"
}
```

---

### Machine Learning

#### Prever Demanda
Prevê demanda energética para as próximas horas.
`POST /api/ml/predict`
**Request Body:**
```bash
{
"node_id": "CONS_0",
"hours_ahead": 24
}
```
**Response 200:**
```bash
{
"success": true,
"node_id": "CONS_0",
"predictions": [
{
"timestamp": "2025-11-19T16:00:00",
"predicted_load": 352.3,
"confidence": 0.95
},
{
"timestamp": "2025-11-19T17:00:00",
"predicted_load": 389.7,
"confidence": 0.93
}
],
"peak_times": [
{
"timestamp": "2025-11-19T19:00:00",
"predicted_load": 487.2,
"severity": "high"
}
],
"hours_ahead": 24
}
```
---

#### Treinar Modelo
Treina modelo de Machine Learning.
`POST /api/ml/train`
**Request Body:**
```bash
{
"epochs": 100
}
```
**Response 200:**
```bash
{
"success": true,
"training_result": {
"timestamp": "2025-11-19T15:30:00",
"training": {
"final_loss": 0.0234,
"epochs": 100
},
"validation": {
"mse": 234.5,
"mae": 15.3,
"rmse": 15.3,
"r2_score": 0.88,
"accuracy": 0.92
},
"data_size": 2160
}
}
```

---

### IoT Simulation

#### Obter Leituras dos Sensores
Retorna leituras atuais de todos os sensores IoT.
`GET /api/iot/readings`
**Response 200:**
```bash
{
"success": true,
"count": 20,
"readings": [
{
"node_id": "SUB_0",
"timestamp": "2025-11-19T15:30:00",
"load": 3805.3,
"voltage": 222.5,
"current": 17.1,
"power_factor": 0.92,
"frequency": 60.2,
"temperature": 32.5,
"status": "active"
}
],
"timestamp": "2025-11-19T15:30:00"
}
```

---

#### Simular Falha
Simula falha em um nó específico.
`POST /api/iot/simulate-failure`
**Request Body:**
```bash
{
"node_id": "CONS_0",
"duration_hours": 2
}
```
**Response 200:**
```bash
{
"success": true,
"failure": {
"node_id": "CONS_0",
"failure_start": "2025-11-19T15:30:00",
"estimated_recovery": "2025-11-19T17:30:00"
}
}
```

---

### Eventos

#### Listar Eventos
Lista eventos da fila.
`GET /api/events?type=overload`
**Query Params:**
- `type` (string, optional) - Filtrar por tipo de evento

**Response 200:**
```bash
{
"success": true,
"count": 12,
"events": [
{
"type": "overload",
"node_id": "CONS_3",
"data": {
"load": 487.5,
"capacity": 500.0
}
}
],
"queue_stats": {
"current_size": 12,
"max_size": 10000,
"processed": 145,
"dropped": 0
}
}
```

---

#### Eventos Críticos
Retorna eventos críticos do heap de prioridade.
`GET /api/events/critical`
**Response 200:**
```bash
{
"success": true,
"count": 3,
"events": [
{
"priority": 1,
"type": "failure",
"node_id": "TRF_2",
"data": {
"failure_start": "2025-11-19T15:00:00"
}
},
{
"priority": 2,
"type": "overload",
"node_id": "SUB_1",
"data": {
"load": 5200.0,
"capacity": 5000.0
}
}
]
}
```

---

## ⚠️ Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Recurso criado |
| 400 | Requisição inválida |
| 404 | Recurso não encontrado |
| 500 | Erro interno do servidor |

**Formato de Erro:**
```bash
{
"success": false,
"error": "Descrição do erro"
}
```

---

## 📊 Tipos de Dados

### Node Type
- "substation" | "transformer" | "consumer"
### Status
"active" | "warning" | "overloaded" | "failed"
### Event Type
"overload" | "failure" | "recovery" | "maintenance"
### Algorithm
"dijkstra" | "astar"

---

## 🔄 Rate Limiting

Atualmente sem limite. Em produção, implemente:
- 100 requisições/minuto por IP
- 1000 requisições/hora por usuário

---

## 📝 Exemplos com cURL

### Inicializar Sistema
```bash
curl -X POST http://localhost:5000/api/init
-H "Content-Type: application/json"
-d '{"num_nodes": 20, "train_ml": true}'
```
### Balancear Rede
`curl -X POST http://localhost:5000/api/balance`
### Buscar Rota
```bash
curl -X POST http://localhost:5000/api/route
-H "Content-Type: application/json"
-d '{
"source": "SUB_0",
"destination": "CONS_5",
"algorithm": "dijkstra"
}'
```
### Prever Demanda
```bash
curl -X POST http://localhost:5000/api/ml/predict
-H "Content-Type: application/json"
-d '{
"node_id": "CONS_0",
"hours_ahead": 24
}'
```

---

## 🐍 Exemplos com Python
`import requests`

`BASE_URL = "http://localhost:5000/api"`

Inicializar
```bash
response = requests.post(f"{BASE_URL}/init", json={
"num_nodes": 20,
"train_ml": True
})
print(response.json())
```

Listar nós
```bash
response = requests.get(f"{BASE_URL}/nodes")
nodes = response.json()["nodes"]
```

Balancear
```bash
response = requests.post(f"{BASE_URL}/balance")
result = response.json()
```

Prever
```bash
response = requests.post(f"{BASE_URL}/ml/predict", json={
"node_id": "CONS_0",
"hours_ahead": 24
})
predictions = response.json()["predictions"]
```

---

## 🌐 Exemplos com JavaScript (Fetch)
```bash
const BASE_URL = 'http://localhost:5000/api';

// Inicializar
async function init() {
const response = await fetch(${BASE_URL}/init, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ num_nodes: 20, train_ml: true })
});
const data = await response.json();
console.log(data);
}

// Obter estatísticas
async function getStats() {
const response = await fetch(${BASE_URL}/stats);
const data = await response.json();
return data.stats;
}

// Balancear rede
async function balance() {
const response = await fetch(${BASE_URL}/balance, {
method: 'POST'
});
const data = await response.json();
console.log(data.balancing);
}
```

---

## 📚 Referências

- [Flask Documentation](https://flask.palletsprojects.com/)
- [RESTful API Design](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)

---

**EcoGrid+ API v1.0** - Documentação completa para desenvolvedores 🚀