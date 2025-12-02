"""
API REST Flask para o EcoGrid+.
Endpoints para gerenciamento da rede elétrica.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
import json
import time


from config import Config
from models.database import db, Base
from models.schemas import (
    Node,
    Edge,
    SensorReading,
    Event,
    Prediction,
    BalancingOperation
)

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
    "initialized": False,
    "simulation_running": False,
    "last_balance": None,
    "total_operations": 0,
    # métricas de sobrecarga / benchmark
    "overloads_detected": 0,
    "overloads_resolved": 0,
    "total_overload_response_ms": 0.0,
    "overload_actions": 0,
}

# Histórico simples de benchmark em memória
benchmark_history = {
    "balance": [],
    "route": [],
    "optimize": [],
}

# ==================== INICIALIZAÇÃO ====================

@app.route("/api/reset", methods=["POST"])
def reset_system():
    """Reset completo do sistema"""
    try:
        logger.info("🔄 Resetando sistema...")

        # Limpa banco de dados
        session = db.get_session()
        try:
            session.query(BalancingOperation).delete()
            session.query(Prediction).delete()
            session.query(Event).delete()
            session.query(SensorReading).delete()
            session.query(Edge).delete()
            session.query(Node).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao limpar banco: {e}")
        finally:
            session.close()

        # Recria estruturas em memória e algoritmos
        global avl_tree, bplus_tree, energy_graph, event_queue, priority_heap
        global load_balancer, energy_router, efficiency_optimizer
        global predictor, iot_simulator, trainer

        avl_tree = AVLTree()
        bplus_tree = BPlusTree(order=5)
        energy_graph = EnergyGraph()
        event_queue = EventQueue()
        priority_heap = PriorityHeap()

        load_balancer = LoadBalancer(avl_tree, energy_graph)
        energy_router = EnergyRouter(energy_graph)
        efficiency_optimizer = EfficiencyOptimizer(energy_graph, avl_tree)

        predictor = EnergyDemandPredictor()
        iot_simulator = IoTSimulator()
        trainer = ModelTrainer(predictor, iot_simulator)

        app_state["initialized"] = False
        app_state["simulation_running"] = False
        app_state["last_balance"] = None
        app_state["total_operations"] = 0
        app_state["overloads_detected"] = 0
        app_state["overloads_resolved"] = 0
        app_state["total_overload_response_ms"] = 0.0
        app_state["overload_actions"] = 0

        benchmark_history["balance"].clear()
        benchmark_history["route"].clear()
        benchmark_history["optimize"].clear()

        return jsonify({"success": True, "message": "Sistema resetado com sucesso"}), 200

    except Exception as e:
        logger.error(f"❌ Erro ao resetar: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/init", methods=["POST"])
def initialize_system():
    """
    Inicializa sistema completo com rede de exemplo.
    POST /api/init
    Body: { "num_nodes": 20, "train_ml": true }
    """
    try:
        data = request.get_json() or {}
        num_nodes = data.get("num_nodes", 20)
        train_ml = data.get("train_ml", True)

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
            predictor.save_model(Config.MODEL_PATH)
            predictor.last_train_meta = {
                "epochs": 50,
                "train_accuracy": ml_status["validation"]["accuracy"],
                "train_loss": ml_status["validation"]["loss"],
                "train_samples": ml_status.get("train_samples", 0),
                "last_train_time": datetime.now().isoformat(),
            }

        app_state["initialized"] = True

        return jsonify(
            {
                "success": True,
                "message": "Sistema inicializado com sucesso",
                "network_stats": energy_graph.get_network_stats(),
                "avl_stats": avl_tree.get_stats(),
                "ml_training": ml_status,
                "timestamp": datetime.now().isoformat(),
            }
        ), 200

    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _create_sample_network(num_nodes=20):
    """Cria rede elétrica de exemplo"""
    import random

    # Cria subestações (3)
    substations = []
    for i in range(3):
        node_id = f"SUB_{i}"
        initial_load = random.uniform(2000, 4000)

        energy_graph.add_node(
            node_id,
            "substation",
            capacity=5000,
            efficiency=0.95,
            current_load=initial_load,
        )
        avl_tree.insert(
            node_id,
            {
                "capacity": 5000,
                "current_load": initial_load,
                "efficiency": 0.95,
                "type": "substation",
            },
        )
        iot_simulator.create_sensor(node_id, base_load=3000)
        substations.append(node_id)

        session = db.get_session()
        existing = session.query(Node).filter_by(node_id=node_id).first()
        if not existing:
            node = Node(
                node_id=node_id,
                node_type="substation",
                capacity=5000,
                current_load=initial_load,
                efficiency=0.95,
            )
            session.add(node)
            session.commit()
        session.close()

    # Cria transformadores (7)
    transformers = []
    for i in range(7):
        node_id = f"TRF_{i}"
        initial_load = random.uniform(800, 1600)

        energy_graph.add_node(
            node_id,
            "transformer",
            capacity=2000,
            efficiency=0.90,
            current_load=initial_load,
        )
        avl_tree.insert(
            node_id,
            {
                "capacity": 2000,
                "current_load": initial_load,
                "efficiency": 0.90,
                "type": "transformer",
            },
        )
        iot_simulator.create_sensor(node_id, base_load=1200)
        transformers.append(node_id)

        session = db.get_session()
        existing = session.query(Node).filter_by(node_id=node_id).first()
        if not existing:
            node = Node(
                node_id=node_id,
                node_type="transformer",
                capacity=2000,
                current_load=initial_load,
                efficiency=0.90,
            )
            session.add(node)
            session.commit()
        session.close()

    # Cria consumidores
    consumers = []
    for i in range(num_nodes - 10):
        node_id = f"CONS_{i}"
        capacity = random.uniform(200, 800)
        initial_load = random.uniform(capacity * 0.3, capacity * 0.9)

        energy_graph.add_node(
            node_id,
            "consumer",
            capacity=capacity,
            efficiency=0.85,
            current_load=initial_load,
        )
        avl_tree.insert(
            node_id,
            {
                "capacity": capacity,
                "current_load": initial_load,
                "efficiency": 0.85,
                "type": "consumer",
            },
        )
        iot_simulator.create_sensor(node_id, base_load=capacity * 0.6)
        consumers.append(node_id)

        session = db.get_session()
        existing = session.query(Node).filter_by(node_id=node_id).first()
        if not existing:
            node = Node(
                node_id=node_id,
                node_type="consumer",
                capacity=capacity,
                current_load=initial_load,
                efficiency=0.85,
            )
            session.add(node)
            session.commit()
        session.close()

    # Subestações <-> Transformadores (totalmente conectadas)
    for sub in substations:
        for trf in transformers:
            distance = random.uniform(5, 20)
            energy_graph.add_edge(sub, trf, distance, resistance=0.05)

            session = db.get_session()
            sub_node = session.query(Node).filter_by(node_id=sub).first()
            trf_node = session.query(Node).filter_by(node_id=trf).first()
            edge = Edge(
                from_node_id=sub_node.id,
                to_node_id=trf_node.id,
                distance=distance,
                resistance=0.05,
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
            resistance=0.1,
        )
        session.add(edge)
        session.commit()
        session.close()

    logger.info(
        f"✅ Rede criada: {len(substations)} subestações, {len(transformers)} transformadores, {len(consumers)} consumidores"
    )

# ==================== NODES ====================

@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    try:
        nodes = avl_tree.inorder_traversal()
        return jsonify(
            {
                "success": True,
                "count": len(nodes),
                "nodes": nodes,
                "tree_stats": avl_tree.get_stats(),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<node_id>", methods=["GET"])
def get_node(node_id):
    try:
        node_data = avl_tree.search(node_id)
        if not node_data:
            return jsonify({"success": False, "error": "Nó não encontrado"}), 404

        sensor_reading = iot_simulator.generate_reading(node_id)

        return jsonify(
            {
                "success": True,
                "node_id": node_id,
                "data": node_data,
                "sensor_reading": sensor_reading,
                "neighbors": [n[0] for n in energy_graph.edges.get(node_id, [])],
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes", methods=["POST"])
def create_node():
    try:
        data = request.get_json()
        node_id = data.get("node_id")
        node_type = data.get("type", "consumer")
        capacity = data.get("capacity", 500)
        efficiency = data.get("efficiency", 0.85)

        if not node_id:
            return jsonify({"success": False, "error": "node_id obrigatório"}), 400

        energy_graph.add_node(node_id, node_type, capacity, efficiency, current_load=0)
        avl_tree.insert(
            node_id,
            {
                "capacity": capacity,
                "current_load": 0,
                "efficiency": efficiency,
                "type": node_type,
            },
        )

        iot_simulator.create_sensor(node_id, base_load=capacity * 0.5)

        session = db.get_session()
        node = Node(
            node_id=node_id,
            node_type=node_type,
            capacity=capacity,
            efficiency=efficiency,
        )
        session.add(node)
        session.commit()
        session.close()

        return jsonify(
            {"success": True, "message": "Nó criado com sucesso", "node_id": node_id}
        ), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<node_id>/load", methods=["PUT"])
def update_node_load(node_id):
    """
    Atualiza carga de um nó.
    PUT /api/nodes/:node_id/load
    Body: { "load": 450 }
    """
    try:
        data = request.get_json()
        new_load = data.get("load")

        if new_load is None:
            return jsonify({"success": False, "error": "load obrigatório"}), 400

        node_data = avl_tree.search(node_id)
        if not node_data:
            return jsonify({"success": False, "error": "Nó não encontrado"}), 404

        node_data["current_load"] = new_load
        avl_tree.insert(node_id, node_data)
        energy_graph.update_load(node_id, new_load)

        utilization = new_load / node_data["capacity"]

        if new_load > node_data["capacity"] * 0.9:
            event_payload = {
                "load": new_load,
                "capacity": node_data["capacity"],
                "utilization": utilization,
            }
            priority_heap.push("overload", node_id, event_payload, Priority.HIGH)
            event_queue.enqueue(
                QueueEvent("overload", node_id, event_payload, priority=2)
            )
            app_state["overloads_detected"] += 1

        return jsonify(
            {
                "success": True,
                "node_id": node_id,
                "new_load": new_load,
                "capacity": node_data["capacity"],
                "utilization": utilization,
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== BALANCEAMENTO ====================

@app.route("/api/balance", methods=["POST"])
def balance_network():
    """
    Executa balanceamento de carga na rede.
    POST /api/balance
    """
    global priority_heap

    try:
        logger.info("⚖️ Executando balanceamento de carga...")

        start = time.time()
        result = load_balancer.balance_network()
        efficiency = load_balancer.calculate_efficiency()
        elapsed_ms = (time.time() - start) * 1000.0

        benchmark_history["balance"].append(elapsed_ms)
        if len(benchmark_history["balance"]) > 50:
            benchmark_history["balance"].pop(0)

        # limpa eventos de sobrecarga resolvidos
        cleared = 0
        new_heap = PriorityHeap()
        while priority_heap.size() > 0:
            event = priority_heap.pop()
            if event.event_type == "overload":
                cleared += 1
            else:
                new_heap.push(event.event_type, event.node_id, event.data, event.priority)
        # substitui heap
        priority_heap = new_heap

        # limpa fila de eventos de sobrecarga
        old_queue = list(event_queue.queue)
        event_queue.queue.clear()
        for event in old_queue:
            if event.event_type != "overload":
                event_queue.enqueue(event)

        app_state["last_balance"] = datetime.now().isoformat()
        app_state["total_operations"] += result["balanced"]
        if cleared > 0:
            app_state["overloads_resolved"] += cleared
            app_state["overload_actions"] += 1
            app_state["total_overload_response_ms"] += elapsed_ms

        return jsonify(
            {
                "success": True,
                "balancing": result,
                "efficiency": efficiency,
                "events_cleared": cleared,
                "execution_time_ms": elapsed_ms,
                "timestamp": datetime.now().isoformat(),
            }
        ), 200

    except Exception as e:
        logger.error(f"❌ Erro no balanceamento: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/balance/stats", methods=["GET"])
def get_balance_stats():
    try:
        stats = load_balancer.get_balancing_stats()
        return jsonify({"success": True, "stats": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== ROTEAMENTO ====================

@app.route("/api/route", methods=["POST"])
def find_route():
    """
    Encontra rota ótima entre dois nós e compara algoritmos.
    POST /api/route
    Body: { "source": "SUB_0", "destination": "CONS_5", "algorithm": "dijkstra" }
    """
    try:
        data = request.get_json()
        source = data.get("source")
        destination = data.get("destination")
        preferred = data.get("algorithm", "dijkstra")

        if not source or not destination:
            return jsonify({"success": False, "error": "source e destination obrigatórios"}), 400

        # roda algoritmo escolhido
        start = time.time()
        main_result = energy_router.find_optimal_route(source, destination, preferred)
        main_elapsed_ms = (time.time() - start) * 1000.0

        # roda também o outro algoritmo só para benchmark
        other_algo = "astar" if preferred == "dijkstra" else "dijkstra"
        start_other = time.time()
        other_result = energy_router.find_optimal_route(source, destination, other_algo)
        other_elapsed_ms = (time.time() - start_other) * 1000.0

        # salva benchmarks separados por algoritmo
        benchmark_history["route"].append({
            "source": source,
            "destination": destination,
            "preferred": preferred,
            preferred: main_elapsed_ms,
            other_algo: other_elapsed_ms
        })
        if len(benchmark_history["route"]) > 50:
            benchmark_history["route"].pop(0)

        # calcula perda de potência só para a rota principal se existir
        if main_result["path"]:
            power_loss = energy_router.calculate_power_loss(main_result["path"])
            main_result["power_loss"] = power_loss

        main_result["execution_time"] = main_elapsed_ms / 1000.0

        comparison = {
            preferred: main_elapsed_ms,
            other_algo: other_elapsed_ms,
        }

        return jsonify({
            "success": True,
            "route": main_result,
            "comparison": comparison
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/route/redundant", methods=["POST"])
def find_redundant_routes():
    try:
        data = request.get_json()
        source = data.get("source")
        destination = data.get("destination")
        k = data.get("k", 3)

        routes = energy_router.find_redundant_paths(source, destination, k)

        return jsonify(
            {"success": True, "count": len(routes), "routes": routes}
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== OTIMIZAÇÃO ====================

@app.route("/api/optimize", methods=["POST"])
def optimize_efficiency():
    """
    Executa otimização de eficiência energética.
    POST /api/optimize
    """
    try:
        logger.info("🔧 Otimizando eficiência da rede...")

        start = time.time()
        result = efficiency_optimizer.optimize_network()
        carbon = efficiency_optimizer.calculate_carbon_footprint()
        renewable = efficiency_optimizer.suggest_renewable_integration()
        elapsed_ms = (time.time() - start) * 1000.0

        benchmark_history["optimize"].append(elapsed_ms)
        if len(benchmark_history["optimize"]) > 50:
            benchmark_history["optimize"].pop(0)

        return jsonify(
            {
                "success": True,
                "optimization": result,
                "carbon_footprint": carbon,
                "renewable_suggestions": renewable[:5],
                "execution_time_ms": elapsed_ms,
                "timestamp": datetime.now().isoformat(),
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ==================== MACHINE LEARNING ====================

@app.route("/api/ml/predict", methods=["POST"])
def predict_demand():
    try:
        data = request.get_json()
        node_id = data.get("node_id")
        hours_ahead = data.get("hours_ahead", 24)

        if not node_id:
            return jsonify({"success": False, "error": "node_id obrigatório"}), 400

        recent_data = iot_simulator.generate_historical_data(
            node_id, days=1, interval_hours=1
        )

        predictions = predictor.predict(recent_data, hours_ahead)
        peaks = predictor.predict_peak_times(predictions)

        return jsonify(
            {
                "success": True,
                "node_id": node_id,
                "predictions": predictions,
                "peak_times": peaks,
                "hours_ahead": hours_ahead,
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ml/train", methods=["POST"])
def train_model():
    try:
        data = request.get_json() or {}
        epochs = data.get("epochs", 100)

        logger.info(f"🤖 Treinando modelo por {epochs} épocas...")
        result = trainer.train_model(epochs=epochs)

        # Garante estrutura padrão
        validation = result.get("validation", {})
        validation.setdefault("accuracy", 0.0)
        validation.setdefault("loss", 0.0)
        result["validation"] = validation
        result.setdefault("train_samples", 0)
        result.setdefault("epochs", epochs)
        result.setdefault("timestamp", datetime.now().isoformat())

        predictor.save_model(Config.MODEL_PATH)

        predictor.last_train_meta = {
            "epochs": result["epochs"],
            "train_accuracy": validation["accuracy"],
            "train_loss": validation["loss"],
            "train_samples": result["train_samples"],
            "last_train_time": result["timestamp"],
        }

        return jsonify({"success": True, "training_result": result}), 200

    except Exception as e:
        logger.error(f"Erro no treino ML: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ml/stats", methods=["GET"])
def ml_stats():
    meta = getattr(predictor, "last_train_meta", None)
    if not meta:
        return jsonify({"success": False, "error": "Modelo não treinado ainda"}), 400

    return jsonify({"success": True, "ml_stats": meta}), 200

# ==================== IoT SIMULATION ====================

@app.route("/api/iot/readings", methods=["GET"])
def get_iot_readings():
    try:
        readings = iot_simulator.generate_batch_readings()

        for reading in readings:
            node_id = reading["node_id"]
            load = reading["load"]
            node_data = avl_tree.search(node_id)
            if node_data:
                node_data["current_load"] = load
                avl_tree.insert(node_id, node_data)
                energy_graph.update_load(node_id, load)

        return jsonify(
            {
                "success": True,
                "count": len(readings),
                "readings": readings,
                "timestamp": datetime.now().isoformat(),
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== EVENTOS & HEAP ====================

@app.route("/api/iot/simulate-failure", methods=["POST"])
def simulate_failure():
    try:
        data = request.get_json()
        node_id = data.get("node_id")
        duration = data.get("duration_hours", 2)

        failure = iot_simulator.simulate_failure(node_id, duration)

        priority_heap.push("failure", node_id, failure, Priority.CRITICAL)
        event_queue.enqueue(QueueEvent("failure", node_id, failure, priority=1))

        return jsonify({"success": True, "failure": failure}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/events", methods=["GET"])
def get_events():
    try:
        event_type = request.args.get("type")

        if event_type:
            events = event_queue.get_events_by_type(event_type)
        else:
            events = [
                {"type": e.event_type, "node_id": e.node_id, "data": e.data}
                for e in list(event_queue.queue)
            ]

        return jsonify(
            {
                "success": True,
                "count": len(events),
                "events": events,
                "queue_stats": event_queue.get_stats(),
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/events/critical", methods=["GET"])
def get_critical_events():
    try:
        critical = priority_heap.get_critical_events(threshold=Priority.MEDIUM)

        return jsonify(
            {
                "success": True,
                "count": len(critical),
                "events": [
                    {
                        "priority": e.priority,
                        "type": e.event_type,
                        "node_id": e.node_id,
                        "data": e.data,
                    }
                    for e in critical
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/events/heap", methods=["GET"])
def get_heap_snapshot():
    """
    Retorna uma visão do heap de prioridade para visualização.
    GET /api/events/heap
    """
    try:
        items = priority_heap.to_list()
        return jsonify({"success": True, "count": len(items), "heap": items}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== ESTATÍSTICAS + BENCHMARK ====================

@app.route("/api/simulate-overload", methods=["POST"])
def simulate_overload():
    """Simula sobrecarga em alguns nós para teste"""
    try:
        data = request.get_json() or {}
        num_nodes = data.get("num_nodes", 3)

        all_nodes = avl_tree.inorder_traversal()
        consumers = [n for n in all_nodes if n["data"]["type"] == "consumer"]

        import random

        selected = random.sample(consumers, min(num_nodes, len(consumers)))

        for node in selected:
            node_id = node["key"]
            node_data = node["data"]

            new_load = node_data["capacity"] * 0.95
            node_data["current_load"] = new_load

            avl_tree.insert(node_id, node_data)
            energy_graph.update_load(node_id, new_load)

            event_payload = {
                "load": new_load,
                "capacity": node_data["capacity"],
                "utilization": new_load / node_data["capacity"],
            }
            priority_heap.push("overload", node_id, event_payload, Priority.HIGH)
            event_queue.enqueue(
                QueueEvent("overload", node_id, event_payload, priority=2)
            )
            app_state["overloads_detected"] += 1

        return jsonify(
            {
                "success": True,
                "message": f"{len(selected)} nós sobrecarregados para teste",
                "nodes": [n["key"] for n in selected],
            }
        ), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_system_stats():
    try:
        efficiency = load_balancer.calculate_efficiency()

        avg_overload_response = (
            app_state["total_overload_response_ms"] / app_state["overload_actions"]
            if app_state["overload_actions"] > 0
            else 0.0
        )

        stats = {
            "network": energy_graph.get_network_stats(),
            "avl_tree": avl_tree.get_stats(),
            "event_queue": event_queue.get_stats(),
            "priority_heap": {"size": priority_heap.size()},
            "balancing": {
                **load_balancer.get_balancing_stats(),
                "efficiency": efficiency,
            },
            "routing": energy_router.get_routing_stats(),
            "efficiency": efficiency,
            "iot": iot_simulator.get_sensor_status(),
            "app_state": app_state,
            "overload_metrics": {
                "overloads_detected": app_state["overloads_detected"],
                "overloads_resolved": app_state["overloads_resolved"],
                "avg_overload_response_ms": avg_overload_response,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify({"success": True, "stats": stats}), 200

    except Exception as e:
        logger.error(f"Erro ao obter stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/benchmark/summary", methods=["GET"])
def get_benchmark_summary():
    """
    Retorna métricas de benchmark para exibir na UI.
    GET /api/benchmark/summary
    """
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0

    summary = {
        "balance_avg_ms": avg(benchmark_history["balance"]),
        "route_avg_ms": avg(benchmark_history["route"]),
        "optimize_avg_ms": avg(benchmark_history["optimize"]),
        "balance_samples": len(benchmark_history["balance"]),
        "route_samples": len(benchmark_history["route"]),
        "optimize_samples": len(benchmark_history["optimize"]),
    }
    return jsonify({"success": True, "benchmark": summary}), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "initialized": app_state["initialized"],
            "timestamp": datetime.now().isoformat(),
        }
    ), 200

# ==================== ROOT ====================

@app.route("/")
def index():
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

if __name__ == "__main__":
    logger.info("🚀 Iniciando EcoGrid+ API...")
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
