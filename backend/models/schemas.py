"""
Schemas SQLAlchemy para tabelas PostgreSQL.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base

class Node(Base):
    """Tabela de nós da rede"""
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(50), unique=True, nullable=False, index=True)
    node_type = Column(String(20), nullable=False)  # substation, transformer, consumer
    capacity = Column(Float, nullable=False)
    current_load = Column(Float, default=0)
    efficiency = Column(Float, default=1.0)
    voltage = Column(Float, default=220.0)
    status = Column(String(20), default='active')
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    edges_from = relationship("Edge", foreign_keys="Edge.from_node_id", back_populates="from_node")
    edges_to = relationship("Edge", foreign_keys="Edge.to_node_id", back_populates="to_node")
    readings = relationship("SensorReading", back_populates="node", cascade="all, delete-orphan")

class Edge(Base):
    """Tabela de linhas de transmissão (arestas)"""
    __tablename__ = 'edges'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    to_node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    distance = Column(Float, nullable=False)
    resistance = Column(Float, default=0.1)
    capacity = Column(Float, default=1000)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    from_node = relationship("Node", foreign_keys=[from_node_id], back_populates="edges_from")
    to_node = relationship("Node", foreign_keys=[to_node_id], back_populates="edges_to")

class SensorReading(Base):
    """Tabela de leituras dos sensores IoT"""
    __tablename__ = 'sensor_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    load = Column(Float, nullable=False)
    voltage = Column(Float)
    current = Column(Float)
    power_factor = Column(Float)
    frequency = Column(Float)
    temperature = Column(Float)
    status = Column(String(20), default='active')
    
    # Relacionamento
    node = relationship("Node", back_populates="readings")

class Event(Base):
    """Tabela de eventos do sistema"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    node_id = Column(String(50), nullable=True)
    severity = Column(Integer, default=3)  # 1=critical, 5=info
    description = Column(String(500))
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

class Prediction(Base):
    """Tabela de previsões ML"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(50), nullable=False, index=True)
    prediction_timestamp = Column(DateTime, nullable=False, index=True)
    predicted_load = Column(Float, nullable=False)
    confidence = Column(Float)
    actual_load = Column(Float, nullable=True)  # Preenchido depois
    error = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BalancingOperation(Base):
    """Tabela de operações de balanceamento"""
    __tablename__ = 'balancing_operations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_node = Column(String(50), nullable=False)
    to_node = Column(String(50), nullable=False)
    amount_transferred = Column(Float, nullable=False)
    efficiency_gain = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, default=True)
