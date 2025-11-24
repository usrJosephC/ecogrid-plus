-- Script de inicialização do banco PostgreSQL
-- EcoGrid+ Database Schema

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de Nós
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) UNIQUE NOT NULL,
    node_type VARCHAR(20) NOT NULL CHECK (node_type IN ('substation', 'transformer', 'consumer')),
    capacity REAL NOT NULL CHECK (capacity > 0),
    current_load REAL DEFAULT 0 CHECK (current_load >= 0),
    efficiency REAL DEFAULT 1.0 CHECK (efficiency >= 0 AND efficiency <= 1),
    voltage REAL DEFAULT 220.0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'warning', 'overloaded', 'failed')),
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para nodes
CREATE INDEX idx_nodes_node_id ON nodes(node_id);
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_status ON nodes(status);

-- Tabela de Arestas (Linhas de Transmissão)
CREATE TABLE IF NOT EXISTS edges (
    id SERIAL PRIMARY KEY,
    from_node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    distance REAL NOT NULL CHECK (distance > 0),
    resistance REAL DEFAULT 0.1 CHECK (resistance >= 0),
    capacity REAL DEFAULT 1000 CHECK (capacity > 0),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT different_nodes CHECK (from_node_id != to_node_id)
);

-- Índices para edges
CREATE INDEX idx_edges_from_node ON edges(from_node_id);
CREATE INDEX idx_edges_to_node ON edges(to_node_id);

-- Tabela de Leituras de Sensores IoT
CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    load REAL NOT NULL,
    voltage REAL,
    current REAL,
    power_factor REAL CHECK (power_factor >= 0 AND power_factor <= 1),
    frequency REAL,
    temperature REAL,
    status VARCHAR(20) DEFAULT 'active'
);

-- Índices para sensor_readings
CREATE INDEX idx_sensor_readings_node ON sensor_readings(node_id);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);
CREATE INDEX idx_sensor_readings_composite ON sensor_readings(node_id, timestamp DESC);

-- Particionamento por data (opcional, para alto volume)
-- CREATE TABLE sensor_readings_2025_11 PARTITION OF sensor_readings
-- FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Tabela de Eventos
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    node_id VARCHAR(50),
    severity INTEGER DEFAULT 3 CHECK (severity >= 1 AND severity <= 5),
    description TEXT,
    data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP
);

-- Índices para events
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_resolved ON events(resolved);
CREATE INDEX idx_events_severity ON events(severity);

-- Tabela de Previsões ML
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(50) NOT NULL,
    prediction_timestamp TIMESTAMP NOT NULL,
    predicted_load REAL NOT NULL,
    confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
    actual_load REAL,
    error REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para predictions
CREATE INDEX idx_predictions_node ON predictions(node_id);
CREATE INDEX idx_predictions_timestamp ON predictions(prediction_timestamp);

-- Tabela de Operações de Balanceamento
CREATE TABLE IF NOT EXISTS balancing_operations (
    id SERIAL PRIMARY KEY,
    from_node VARCHAR(50) NOT NULL,
    to_node VARCHAR(50) NOT NULL,
    amount_transferred REAL NOT NULL CHECK (amount_transferred > 0),
    efficiency_gain REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE
);

-- Índices para balancing_operations
CREATE INDEX idx_balancing_timestamp ON balancing_operations(timestamp DESC);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_nodes_updated_at BEFORE UPDATE ON nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View para estatísticas da rede
CREATE OR REPLACE VIEW network_stats AS
SELECT 
    COUNT(*) as total_nodes,
    SUM(capacity) as total_capacity,
    SUM(current_load) as total_load,
    AVG(current_load / NULLIF(capacity, 0)) as avg_utilization,
    SUM(CASE WHEN status = 'overloaded' THEN 1 ELSE 0 END) as overloaded_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM nodes;

-- View para eventos recentes
CREATE OR REPLACE VIEW recent_critical_events AS
SELECT *
FROM events
WHERE severity <= 2
  AND resolved = FALSE
ORDER BY timestamp DESC
LIMIT 50;

-- Função para calcular utilização de um nó
CREATE OR REPLACE FUNCTION get_node_utilization(p_node_id VARCHAR)
RETURNS REAL AS $$
DECLARE
    utilization REAL;
BEGIN
    SELECT current_load / NULLIF(capacity, 0)
    INTO utilization
    FROM nodes
    WHERE node_id = p_node_id;
    
    RETURN COALESCE(utilization, 0);
END;
$$ LANGUAGE plpgsql;

-- Função para registrar evento
CREATE OR REPLACE FUNCTION log_event(
    p_event_type VARCHAR,
    p_node_id VARCHAR,
    p_severity INTEGER,
    p_description TEXT,
    p_data JSONB DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    event_id INTEGER;
BEGIN
    INSERT INTO events (event_type, node_id, severity, description, data)
    VALUES (p_event_type, p_node_id, p_severity, p_description, p_data)
    RETURNING id INTO event_id;
    
    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- Dados de exemplo iniciais

INSERT INTO nodes (node_id, node_type, capacity, current_load, efficiency) VALUES
    ('SUB_0', 'substation', 5000, 3500, 0.95),
    ('SUB_1', 'substation', 5000, 4200, 0.95),
    ('TRF_0', 'transformer', 2000, 1200, 0.90),
    ('TRF_1', 'transformer', 2000, 1500, 0.90),
    ('CONS_0', 'consumer', 500, 350, 0.85),
    ('CONS_1', 'consumer', 600, 480, 0.85);


-- Comentários nas tabelas
COMMENT ON TABLE nodes IS 'Nós da rede elétrica (subestações, transformadores, consumidores)';
COMMENT ON TABLE edges IS 'Linhas de transmissão entre nós';
COMMENT ON TABLE sensor_readings IS 'Leituras dos sensores IoT em tempo real';
COMMENT ON TABLE events IS 'Eventos do sistema (sobrecargas, falhas, etc)';
COMMENT ON TABLE predictions IS 'Previsões de demanda do modelo ML';
COMMENT ON TABLE balancing_operations IS 'Histórico de operações de balanceamento de carga';

-- Grant permissions (ajuste conforme necessário)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ecogrid_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ecogrid_user;
