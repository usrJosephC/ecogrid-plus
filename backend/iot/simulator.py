"""
Simulador IoT para geração de dados sintéticos de sensores.
Simula comportamento realista de consumo energético.
"""

import random
import numpy as np
from datetime import datetime, timedelta
import math

class IoTSimulator:
    def __init__(self):
        self.sensors = {}
        self.simulation_started = False
    
    def create_sensor(self, node_id, sensor_type='smart_meter', base_load=100):
        """
        Cria sensor virtual.
        sensor_type: 'smart_meter', 'voltage_sensor', 'current_sensor'
        """
        self.sensors[node_id] = {
            'node_id': node_id,
            'type': sensor_type,
            'base_load': base_load,
            'status': 'active',
            'last_reading': None,
            'failure_rate': 0.001  # 0.1% chance de falha
        }
    
    def generate_reading(self, node_id, timestamp=None):
        """
        Gera leitura realista do sensor.
        Considera:
        - Padrão diário (picos manhã/noite)
        - Ruído aleatório
        - Sazonalidade
        - Eventos aleatórios
        """
        if node_id not in self.sensors:
            return None
        
        sensor = self.sensors[node_id]
        base_load = sensor['base_load']
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Padrão horário (24h)
        hour = timestamp.hour
        hour_factor = self._get_hourly_factor(hour)
        
        # Padrão semanal (dia da semana)
        weekday = timestamp.weekday()
        weekday_factor = 0.85 if weekday >= 5 else 1.0  # Fim de semana menor
        
        # Sazonalidade (mês do ano)
        month = timestamp.month
        seasonal_factor = self._get_seasonal_factor(month)
        
        # Ruído aleatório (-5% a +5%)
        noise = random.uniform(0.95, 1.05)
        
        # Eventos aleatórios (spikes ocasionais)
        event_factor = 1.0
        if random.random() < 0.05:  # 5% chance
            event_factor = random.uniform(1.2, 1.5)  # Spike de 20-50%
        
        # Calcula carga final
        load = (base_load * 
                hour_factor * 
                weekday_factor * 
                seasonal_factor * 
                noise * 
                event_factor)
        
        # Simula falha do sensor
        if random.random() < sensor['failure_rate']:
            status = 'failed'
            load = 0
        else:
            status = 'active'
        
        reading = {
            'node_id': node_id,
            'timestamp': timestamp,
            'load': round(load, 2),
            'voltage': round(220 + random.uniform(-5, 5), 2),
            'current': round(load / 220, 2),
            'power_factor': round(random.uniform(0.85, 0.95), 2),
            'frequency': round(60 + random.uniform(-0.5, 0.5), 2),
            'temperature': round(25 + random.uniform(-5, 15), 1),
            'status': status
        }
        
        sensor['last_reading'] = reading
        return reading
    
    def _get_hourly_factor(self, hour):
        """
        Retorna fator de carga baseado na hora do dia.
        Picos: 7-9h (manhã) e 18-22h (noite)
        Vales: 0-6h (madrugada)
        """
        # Curva senoidal dupla para simular dois picos
        morning_peak = math.sin((hour - 8) * math.pi / 12) * 0.3
        evening_peak = math.sin((hour - 20) * math.pi / 12) * 0.4
        base = 0.6
        
        return max(0.4, min(1.3, base + morning_peak + evening_peak))
    
    def _get_seasonal_factor(self, month):
        """
        Fator sazonal (maior consumo no verão/inverno).
        """
        # Brasil: verão (dez-fev), inverno (jun-ago)
        if month in [12, 1, 2]:  # Verão - ar condicionado
            return 1.2
        elif month in [6, 7, 8]:  # Inverno - aquecimento
            return 1.15
        else:
            return 1.0
    
    def generate_historical_data(self, node_id, days=30, interval_hours=1):
        """
        Gera histórico de dados para treinamento ML.
        """
        if node_id not in self.sensors:
            self.create_sensor(node_id)
        
        historical_data = []
        start_date = datetime.now() - timedelta(days=days)
        
        current_time = start_date
        end_time = datetime.now()
        
        while current_time <= end_time:
            reading = self.generate_reading(node_id, current_time)
            historical_data.append(reading)
            current_time += timedelta(hours=interval_hours)
        
        return historical_data
    
    def simulate_failure(self, node_id, duration_hours=2):
        """Simula falha em um nó"""
        if node_id in self.sensors:
            self.sensors[node_id]['status'] = 'failed'
            # Agenda recuperação
            return {
                'node_id': node_id,
                'failure_start': datetime.now(),
                'estimated_recovery': datetime.now() + timedelta(hours=duration_hours)
            }
    
    def restore_sensor(self, node_id):
        """Restaura sensor após falha"""
        if node_id in self.sensors:
            self.sensors[node_id]['status'] = 'active'
    
    def get_sensor_status(self):
        """Retorna status de todos os sensores"""
        return {
            'total_sensors': len(self.sensors),
            'active': sum(1 for s in self.sensors.values() if s['status'] == 'active'),
            'failed': sum(1 for s in self.sensors.values() if s['status'] == 'failed'),
            'sensors': list(self.sensors.values())
        }
    
    def generate_batch_readings(self, timestamp=None):
        """Gera leituras para todos os sensores"""
        readings = []
        for node_id in self.sensors:
            reading = self.generate_reading(node_id, timestamp)
            if reading:
                readings.append(reading)
        return readings
