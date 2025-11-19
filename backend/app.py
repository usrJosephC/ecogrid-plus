"""
API REST Flask para o EcoGrid+.
Endpoints para gerenciamento da rede elétrica.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import logging
import json

from config import Config
from models.database import db, Base
from models.schemas import Node, Edge, SensorReading, Event, Prediction, BalancingOperation

from data_structures.avl_tree import AVLTree
from data_structures.bplus_tree import BPlusTree
from data_structures.graph import EnergyGraph
from data_structures.event_queue import EventQueue, Event as QueueEvent
from data_structures.priority_heap import PriorityHeap, Priority

from algorithms.balancing import LoadBalancer
from algorithms.routing import EnergyRouter
from algorithms.efficiency import EfficiencyOptimizer

from ml.predictor import EnergyDemandPredictor
from ml.trainer import ModelTrainer
from iot.simulator import IoTSimulator

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa Flask
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Estruturas de dados em memória
avl_tree = AVLTree()
bplus_tree = BPlusTree(order=5)
energy_graph = EnergyGraph()
event_queue = EventQueue()
priority_heap = PriorityHeap()

# Algoritmos
load_balancer = LoadBalancer(avl_tree, energy_graph)
energy_router = EnergyRouter(energy_graph)
efficiency_optimizer = EfficiencyOptimizer(energy_graph, avl_tree)

# ML e IoT
predictor = EnergyDemandPredictor()
iot_simulator = IoTSimulator()
trainer = ModelTrainer(predictor, iot_simulator)

# Estado da aplicação
app_state = {
    'initialized': False,
    'simulation_running': False,
    'last_balance': None,
    'total_operations': 0
}

# ==================== INICIALIZAÇÃO ====================

@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset completo do sistema"""
    try:
        logger.info("🔄 Resetando sistema...")
        
        # Limpa estruturas em memória
        global avl_tree, bplus_tree, energy_graph, event_queue, priority_heap
        avl_tree = AVLTree()
        bplus_tree = BPlusTree(order=5)
        energy_graph = EnergyGraph()
        event_queue = EventQueue()
        priority_heap = PriorityHeap()
        
        # Limpa banco de dados
        session = db.get_session()
        session.query(BalancingOperation).delete()
        session.query(Prediction).delete()
        session.query(Event).delete()
        session.query(SensorReading).delete()
        session.query(Edge).delete()
        session.query(Node).delete()
        session.commit()
        session.close()
        
        app_state['initialized'] = False
        
        return jsonify({
            'success': True,
            'message': 'Sistema resetado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao resetar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/init', methods=['POST'])
def initialize_system():
    """
    Inicializa sistema completo com rede de exemplo.
    POST /api/init
    Body: { "num_nodes": 20, "train_ml": true }
    """
    try:
        data = request.get_json() or {}
        num_nodes = data.get('num_nodes', 20)
        train_ml = data.get('train_ml', True)
        
        logger.info(f"🚀 Inicializando sistema com {num_nodes} nós...")
        
        # Inicializa banco de dados
        db.init_db()
        db.create_tables()
        
        # Cria rede de exemplo
        _create_sample_network(num_nodes)
        
        # Treina modelo ML se solicitado
        ml_status = None
        if train_ml:
            logger.info("🤖 Treinando modelo de ML...")
            ml_status = trainer.train_model(epochs=50)
        
        app_state['initialized'] = True
        
        return jsonify({
            'success': True,
            'message': 'Sistema inicializado com sucesso',
            'network_stats': energy_graph.get_network_stats(),
            'avl_stats': avl_tree.get_stats(),
            'ml_training': ml_status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _create_sample_network(num_nodes=20):
    """Cria rede elétrica de exemplo"""
    import random
    
    # Cria subestações (3)
    substations = []
    for i in range(3):
        node_id = f"SUB_{i}"
        energy_graph.add_node(node_id, 'substation', capacity=5000, efficiency=0.95)
        avl_tree.insert(node_id, {
            'capacity': 5000,
            'current_load': random.uniform(2000, 4000),
            'efficiency': 0.95,
            'type': 'substation'
        })
        iot_simulator.create_sensor(node_id, base_load=3000)
        substations.append(node_id)
        
        # Salva no PostgreSQL
        session = db.get_session()
        #Verifica se o nó já existe
        existing = session.query(Node).filter_by(node_id=node_id).first()
        if not existing:
            node = Node(
                node_id=node_id,
                node_type='substation',
                capacity=5000,
                current_load=random.uniform(2000, 4000),
                efficiency=0.95
            )
            session.add(node)
            session.commit()
        session.close()
    
    # Cria transformadores (7)
    transformers = []
    for i in range(7):
        node_id = f"TRF_{i}"
        energy_graph.add_node(node_id, 'transformer', capacity=2000, efficiency=0.90)
        avl_tree.insert(node_id, {
            'capacity': 2000,
            'current_load': random.uniform(800, 1600),
            'efficiency': 0.90,
            'type': 'transformer'
        })
        iot_simulator.create_sensor(node_id, base_load=1200)
        transformers.append(node_id)
        
        session = db.get_session()
        #Verifica se o nó já existe
        existing = session.query(Node).filter_by(node_id=node_id).first()
        if not existing:
            node = Node(
                node_id=node_id,
                node_type='transformer',
                capacity=2000,
                current_load=random.uniform(800, 1600),
                efficiency=0.90
            )
            session.add(node)
            session.commit()
        session.close()
    
    # Cria consumidores
    consumers = []
    for i in range(num_nodes - 10):
        node_id = f"CONS_{i}"
        capacity = random.uniform(200, 800)
        energy_graph.add_node(node_id, 'consumer', capacity=capacity, efficiency=0.85)
        avl_tree.insert(node_id, {
            'capacity': capacity,
            'current_load': random.uniform(capacity * 0.3, capacity * 0.9),
            'efficiency': 0.85,
            'type': 'consumer'
        })
        iot_simulator.create_sensor(node_id, base_load=capacity * 0.6)
        consumers.append(node_id)
        
        session = db.get_session()
        #Verifica se o nó já existe
        existing = session.query(Node).filter_by(node_id=node_id).first()
        if not existing:
            node = Node(
                node_id=node_id,
                node_type='consumer',
                capacity=capacity,
                current_load=random.uniform(capacity * 0.3, capacity * 0.9),
                efficiency=0.85
            )
            session.add(node)
            session.commit()
        session.close()
    
    # Conecta nós (cria grafo)
    # Substações <-> Transformadores
    for i, sub in enumerate(substations):
        for j in range(2, 4):  # Cada sub conecta a 2-3 transformadores
            trf_idx = (i * 2 + j - 2) % len(transformers)
            trf = transformers[trf_idx]
            distance = random.uniform(5, 20)
            energy_graph.add_edge(sub, trf, distance, resistance=0.05)
            
            session = db.get_session()
            sub_node = session.query(Node).filter_by(node_id=sub).first()
            trf_node = session.query(Node).filter_by(node_id=trf).first()
            edge = Edge(
                from_node_id=sub_node.id,
                to_node_id=trf_node.id,
                distance=distance,
                resistance=0.05
            )
            session.add(edge)
            session.commit()
            session.close()
    
    # Transformadores <-> Consumidores
    for i, cons in enumerate(consumers):
        trf_idx = i % len(transformers)
        trf = transformers[trf_idx]
        distance = random.uniform(1, 10)
        energy_graph.add_edge(trf, cons, distance, resistance=0.1)
        
        session = db.get_session()
        trf_node = session.query(Node).filter_by(node_id=trf).first()
        cons_node = session.query(Node).filter_by(node_id=cons).first()
        edge = Edge(
            from_node_id=trf_node.id,
            to_node_id=cons_node.id,
            distance=distance,
            resistance=0.1
        )
        session.add(edge)
        session.commit()
        session.close()
    
    logger.info(f"✅ Rede criada: {len(substations)} subestações, {len(transformers)} transformadores, {len(consumers)} consumidores")

# ==================== NODES ====================

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """
    Lista todos os nós da rede.
    GET /api/nodes
    """
    try:
        nodes = avl_tree.inorder_traversal()
        return jsonify({
            'success': True,
            'count': len(nodes),
            'nodes': nodes,
            'tree_stats': avl_tree.get_stats()
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nodes/<node_id>', methods=['GET'])
def get_node(node_id):
    """
    Obtém detalhes de um nó específico.
    GET /api/nodes/:node_id
    """
    try:
        node_data = avl_tree.search(node_id)
        if not node_data:
            return jsonify({'success': False, 'error': 'Nó não encontrado'}), 404
        
        # Busca dados do sensor
        sensor_reading = iot_simulator.generate_reading(node_id)
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'data': node_data,
            'sensor_reading': sensor_reading,
            'neighbors': [n[0] for n in energy_graph.edges.get(node_id, [])]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nodes', methods=['POST'])
def create_node():
    """
    Cria novo nó na rede.
    POST /api/nodes
    Body: { "node_id": "TEST_1", "type": "consumer", "capacity": 500 }
    """
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        node_type = data.get('type', 'consumer')
        capacity = data.get('capacity', 500)
        efficiency = data.get('efficiency', 0.85)
        
        if not node_id:
            return jsonify({'success': False, 'error': 'node_id obrigatório'}), 400
        
        # Adiciona ao grafo e AVL
        energy_graph.add_node(node_id, node_type, capacity, efficiency)
        avl_tree.insert(node_id, {
            'capacity': capacity,
            'current_load': 0,
            'efficiency': efficiency,
            'type': node_type
        })
        
        # Cria sensor
        iot_simulator.create_sensor(node_id, base_load=capacity * 0.5)
        
        # Salva no banco
        session = db.get_session()
        node = Node(
            node_id=node_id,
            node_type=node_type,
            capacity=capacity,
            efficiency=efficiency
        )
        session.add(node)
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'message': 'Nó criado com sucesso',
            'node_id': node_id
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nodes/<node_id>/load', methods=['PUT'])
def update_node_load(node_id):
    """
    Atualiza carga de um nó.
    PUT /api/nodes/:node_id/load
    Body: { "load": 450 }
    """
    try:
        data = request.get_json()
        new_load = data.get('load')
        
        if new_load is None:
            return jsonify({'success': False, 'error': 'load obrigatório'}), 400
        
        node_data = avl_tree.search(node_id)
        if not node_data:
            return jsonify({'success': False, 'error': 'Nó não encontrado'}), 404
        
        # Atualiza estruturas
        node_data['current_load'] = new_load
        avl_tree.insert(node_id, node_data)
        energy_graph.update_load(node_id, new_load)
        
        # Verifica sobrecarga
        if new_load > node_data['capacity'] * 0.9:
            priority_heap.push('overload', node_id, {'load': new_load}, Priority.HIGH)
            event_queue.enqueue(QueueEvent('overload', node_id, {'load': new_load}))
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'new_load': new_load,
            'capacity': node_data['capacity'],
            'utilization': new_load / node_data['capacity']
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== BALANCEAMENTO ====================

@app.route('/api/balance', methods=['POST'])
def balance_network():
    """
    Executa balanceamento de carga na rede.
    POST /api/balance
    """
    try:
        logger.info("⚖️ Executando balanceamento de carga...")
        
        result = load_balancer.balance_network()
        efficiency = load_balancer.calculate_efficiency()
        
        app_state['last_balance'] = datetime.now().isoformat()
        app_state['total_operations'] += result['balanced']
        
        return jsonify({
            'success': True,
            'balancing': result,
            'efficiency': efficiency,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro no balanceamento: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/balance/stats', methods=['GET'])
def get_balance_stats():
    """
    Obtém estatísticas de balanceamento.
    GET /api/balance/stats
    """
    try:
        stats = load_balancer.get_balancing_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ROTEAMENTO ====================

@app.route('/api/route', methods=['POST'])
def find_route():
    """
    Encontra rota ótima entre dois nós.
    POST /api/route
    Body: { "source": "SUB_0", "destination": "CONS_5", "algorithm": "dijkstra" }
    """
    try:
        data = request.get_json()
        source = data.get('source')
        destination = data.get('destination')
        algorithm = data.get('algorithm', 'dijkstra')
        
        if not source or not destination:
            return jsonify({'success': False, 'error': 'source e destination obrigatórios'}), 400
        
        result = energy_router.find_optimal_route(source, destination, algorithm)
        
        if result['path']:
            power_loss = energy_router.calculate_power_loss(result['path'])
            result['power_loss'] = power_loss
        
        return jsonify({
            'success': True,
            'route': result
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/route/redundant', methods=['POST'])
def find_redundant_routes():
    """
    Encontra rotas redundantes para failover.
    POST /api/route/redundant
    Body: { "source": "SUB_0", "destination": "CONS_5", "k": 3 }
    """
    try:
        data = request.get_json()
        source = data.get('source')
        destination = data.get('destination')
        k = data.get('k', 3)
        
        routes = energy_router.find_redundant_paths(source, destination, k)
        
        return jsonify({
            'success': True,
            'count': len(routes),
            'routes': routes
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== OTIMIZAÇÃO ====================

@app.route('/api/optimize', methods=['POST'])
def optimize_efficiency():
    """
    Executa otimização de eficiência energética.
    POST /api/optimize
    """
    try:
        logger.info("🔧 Otimizando eficiência da rede...")
        
        result = efficiency_optimizer.optimize_network()
        carbon = efficiency_optimizer.calculate_carbon_footprint()
        renewable = efficiency_optimizer.suggest_renewable_integration()
        
        return jsonify({
            'success': True,
            'optimization': result,
            'carbon_footprint': carbon,
            'renewable_suggestions': renewable[:3],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== MACHINE LEARNING ====================

@app.route('/api/ml/predict', methods=['POST'])
def predict_demand():
    """
    Prevê demanda energética.
    POST /api/ml/predict
    Body: { "node_id": "CONS_0", "hours_ahead": 24 }
    """
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        hours_ahead = data.get('hours_ahead', 24)
        
        if not node_id:
            return jsonify({'success': False, 'error': 'node_id obrigatório'}), 400
        
        # Gera dados recentes
        recent_data = iot_simulator.generate_historical_data(node_id, days=1, interval_hours=1)
        
        # Faz previsão
        predictions = predictor.predict(recent_data, hours_ahead)
        peaks = predictor.predict_peak_times(predictions)
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'predictions': predictions,
            'peak_times': peaks,
            'hours_ahead': hours_ahead
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ml/train', methods=['POST'])
def train_model():
    """
    Treina modelo de ML.
    POST /api/ml/train
    Body: { "epochs": 100 }
    """
    try:
        data = request.get_json() or {}
        epochs = data.get('epochs', 100)
        
        logger.info(f"🤖 Treinando modelo por {epochs} épocas...")
        result = trainer.train_model(epochs=epochs)
        
        # Salva modelo
        predictor.save_model(Config.MODEL_PATH)
        
        return jsonify({
            'success': True,
            'training_result': result
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== IoT SIMULATION ====================

@app.route('/api/iot/readings', methods=['GET'])
def get_iot_readings():
    """
    Obtém leituras atuais de todos os sensores.
    GET /api/iot/readings
    """
    try:
        readings = iot_simulator.generate_batch_readings()
        
        # Atualiza cargas na rede
        for reading in readings:
            node_id = reading['node_id']
            load = reading['load']
            
            node_data = avl_tree.search(node_id)
            if node_data:
                node_data['current_load'] = load
                avl_tree.insert(node_id, node_data)
                energy_graph.update_load(node_id, load)
        
        return jsonify({
            'success': True,
            'count': len(readings),
            'readings': readings,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/iot/simulate-failure', methods=['POST'])
def simulate_failure():
    """
    Simula falha em um nó.
    POST /api/iot/simulate-failure
    Body: { "node_id": "CONS_0", "duration_hours": 2 }
    """
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        duration = data.get('duration_hours', 2)
        
        failure = iot_simulator.simulate_failure(node_id, duration)
        
        # Registra evento
        priority_heap.push('failure', node_id, failure, Priority.CRITICAL)
        event_queue.enqueue(QueueEvent('failure', node_id, failure, priority=1))
        
        return jsonify({
            'success': True,
            'failure': failure
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== EVENTOS ====================

@app.route('/api/events', methods=['GET'])
def get_events():
    """
    Lista eventos da fila.
    GET /api/events?type=overload
    """
    try:
        event_type = request.args.get('type')
        
        if event_type:
            events = event_queue.get_events_by_type(event_type)
        else:
            events = [{'type': e.event_type, 'node_id': e.node_id, 'data': e.data} 
                     for e in list(event_queue.queue)]
        
        return jsonify({
            'success': True,
            'count': len(events),
            'events': events,
            'queue_stats': event_queue.get_stats()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/critical', methods=['GET'])
def get_critical_events():
    """
    Obtém eventos críticos do heap de prioridade.
    GET /api/events/critical
    """
    try:
        critical = priority_heap.get_critical_events(threshold=Priority.MEDIUM)
        
        return jsonify({
            'success': True,
            'count': len(critical),
            'events': [{'priority': e.priority, 'type': e.event_type, 
                       'node_id': e.node_id, 'data': e.data} for e in critical]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ESTATÍSTICAS ====================

@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """
    Obtém estatísticas globais do sistema.
    GET /api/stats
    """
    try:
        stats = {
            'network': energy_graph.get_network_stats(),
            'avl_tree': avl_tree.get_stats(),
            'event_queue': event_queue.get_stats(),
            'priority_heap': {'size': priority_heap.size()},
            'balancing': load_balancer.get_balancing_stats(),
            'routing': energy_router.get_routing_stats(),
            'efficiency': efficiency_optimizer.get_optimization_report(),
            'iot': iot_simulator.get_sensor_status(),
            'app_state': app_state,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'initialized': app_state['initialized'],
        'timestamp': datetime.now().isoformat()
    }), 200

# ==================== ROOT ====================

@app.route('/')
def index():
    """Página inicial - redireciona para frontend"""
    return """
    <html>
        <head><title>EcoGrid+ API</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🌐 EcoGrid+ API</h1>
            <p>Plataforma Inteligente para Redes de Energia Sustentáveis</p>
            <p><a href="/api/health">Health Check</a> | <a href="/api/stats">Statistics</a></p>
            <p><a href="/frontend/index.html">🎨 Acessar Interface Web</a></p>
        </body>
    </html>
    """

if __name__ == '__main__':
    logger.info("🚀 Iniciando EcoGrid+ API...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
