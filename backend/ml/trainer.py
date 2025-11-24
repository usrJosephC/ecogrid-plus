"""
Script de treinamento do modelo de ML.
Gerencia pipeline completo de treinamento.
"""

import torch
import numpy as np
from datetime import datetime
import json

class ModelTrainer:
    def __init__(self, predictor, data_generator):
        self.predictor = predictor
        self.data_generator = data_generator
        self.training_history = []
    
    def generate_training_data(self, num_nodes=10, days=90):
        """
        Gera dados sintéticos para treinamento.
        Simula 90 dias de consumo para múltiplos nós.
        """
        all_data = []
        
        for node_id in range(num_nodes):
            node_data = self.data_generator.generate_historical_data(
                node_id=node_id,
                days=days
            )
            all_data.extend(node_data)
        
        return all_data
    
    def train_model(self, epochs=100, validation_split=0.2):
        """
        Treina modelo com validação.
        """
        print("🔄 Gerando dados de treinamento...")
        training_data = self.generate_training_data()
        
        # Split train/validation
        split_idx = int(len(training_data) * (1 - validation_split))
        train_data = training_data[:split_idx]
        val_data = training_data[split_idx:]
        
        print(f"📊 Dados: {len(train_data)} treino, {len(val_data)} validação")
        
        # Treina
        print("🚀 Iniciando treinamento...")
        train_result = self.predictor.train(train_data, epochs=epochs)
        
        # Valida
        print("✅ Validando modelo...")
        val_metrics = self.validate_model(val_data)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'training': train_result,
            'validation': val_metrics,
            'data_size': len(training_data)
        }
        
        self.training_history.append(result)
        
        return result
    
    def validate_model(self, validation_data):
        """
        Valida modelo em dados não vistos.
        """
        predictions = []
        actuals = []
        
        # Testa em múltiplos pontos
        for i in range(24, len(validation_data) - 24, 24):
            recent = validation_data[i-24:i]
            actual_next = validation_data[i:i+24]
            
            try:
                pred = self.predictor.predict(recent, hours_ahead=24)
                predictions.extend([p['predicted_load'] for p in pred])
                actuals.extend([a['load'] for a in actual_next])
            except Exception as e:
                continue
        
        if not predictions:
            return {'error': 'Validação falhou'}
        
        # Calcula métricas
        predictions_np = np.array(predictions)
        actuals_np = np.array(actuals)
        
        mse = np.mean((predictions_np - actuals_np) ** 2)
        mae = np.mean(np.abs(predictions_np - actuals_np))
        rmse = np.sqrt(mse)
        
        # R² score
        ss_res = np.sum((actuals_np - predictions_np) ** 2)
        ss_tot = np.sum((actuals_np - np.mean(actuals_np)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mse': float(mse),
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'accuracy': float(max(0, min(1, 1 - mae / np.mean(actuals_np))))
        }
    
    def cross_validate(self, k_folds=5):
        """
        Validação cruzada k-fold.
        """
        print(f"🔄 Validação cruzada com {k_folds} folds...")
        
        full_data = self.generate_training_data()
        fold_size = len(full_data) // k_folds
        
        fold_results = []
        
        for i in range(k_folds):
            print(f"  Fold {i+1}/{k_folds}...")
            
            # Split data
            val_start = i * fold_size
            val_end = val_start + fold_size
            
            val_data = full_data[val_start:val_end]
            train_data = full_data[:val_start] + full_data[val_end:]
            
            # Treina
            self.predictor.train(train_data, epochs=50)
            
            # Valida
            metrics = self.validate_model(val_data)
            fold_results.append(metrics)
        
        # Calcula médias
        avg_metrics = {
            'mse': np.mean([f['mse'] for f in fold_results]),
            'mae': np.mean([f['mae'] for f in fold_results]),
            'rmse': np.mean([f['rmse'] for f in fold_results]),
            'r2_score': np.mean([f['r2_score'] for f in fold_results]),
            'accuracy': np.mean([f['accuracy'] for f in fold_results])
        }
        
        return {
            'fold_results': fold_results,
            'average_metrics': avg_metrics,
            'k_folds': k_folds
        }
    
    def save_training_report(self, filepath='training_report.json'):
        """Salva relatório de treinamento"""
        with open(filepath, 'w') as f:
            json.dump(self.training_history, f, indent=2)
