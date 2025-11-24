"""
Modelo de Machine Learning para previsão de demanda energética.
Utiliza PyTorch com rede LSTM para séries temporais.
"""

import torch
import torch.nn as nn
import numpy as np
from datetime import datetime, timedelta

class DemandPredictor(nn.Module):
    """
    Rede LSTM para previsão de demanda.
    Input: histórico de consumo (sequência temporal)
    Output: previsão para próximas N horas
    """
    
    def __init__(self, input_size=10, hidden_size=64, num_layers=2, output_size=24):
        super(DemandPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)
    
    def forward(self, x):
        """
        Forward pass
        x shape: (batch_size, sequence_length, input_size)
        """
        # LSTM
        lstm_out, _ = self.lstm(x)
        
        # Pega último output da sequência
        last_output = lstm_out[:, -1, :].clone()
        
        # Fully connected
        out = self.fc1(last_output)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out

class EnergyDemandPredictor:
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = DemandPredictor().to(self.device)
        self.trained = False
        
        if model_path:
            self.load_model(model_path)
    
    def prepare_data(self, historical_data, sequence_length=24):
        """
        Prepara dados para treinamento/previsão.
        historical_data: lista de dicionários com timestamp e load
        """
        # Extrai valores de carga
        loads = [d['load'] for d in historical_data]
        
        # Normaliza
        loads_array = np.array(loads)
        self.mean = loads_array.mean()
        self.std = loads_array.std()
        normalized = (loads_array - self.mean) / self.std
        
        # Cria sequências
        X, y = [], []
        for i in range(len(normalized) - sequence_length - 24):
            X.append(normalized[i:i + sequence_length])
            y.append(normalized[i + sequence_length:i + sequence_length + 24])
        
        return np.array(X), np.array(y)
    
    def train(self, historical_data, epochs=100, learning_rate=0.001):
        """
        Treina modelo com dados históricos.
        """
        X, y = self.prepare_data(historical_data)
        
        # Reshape para LSTM: (batch, seq_len, features)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Converte para tensores
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.FloatTensor(y).to(self.device)
        
        # Otimizador e loss
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        self.model.train()
        losses = []
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            losses.append(loss.item())
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
        
        self.trained = True
        
        return {
            'final_loss': losses[-1],
            'losses': losses,
            'epochs': epochs
        }
    
    def predict(self, recent_data, hours_ahead=24):
        """
        Prevê demanda para próximas horas.
        recent_data: últimas 24h de dados
        """
        if not self.trained:
            raise ValueError("Modelo não foi treinado ainda!")
        
        self.model.eval()
        
        # Prepara input
        loads = np.array([d['load'] for d in recent_data])
        normalized = (loads - self.mean) / self.std
        X = normalized.reshape(1, len(normalized), 1)
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        # Predição
        with torch.no_grad():
            prediction = self.model(X_tensor)
        
        # Desnormaliza
        prediction_np = prediction.cpu().numpy()[0]
        denormalized = prediction_np * self.std + self.mean
        
        # Cria timestamps futuros
        last_timestamp = recent_data[-1]['timestamp']
        predictions = []
        
        for i, load in enumerate(denormalized[:hours_ahead]):
            future_time = last_timestamp + timedelta(hours=i+1)
            predictions.append({
                'timestamp': future_time,
                'predicted_load': float(load),
                'confidence': self._calculate_confidence(i)
            })
        
        return predictions
    
    def _calculate_confidence(self, hours_ahead):
        """Calcula confiança da previsão (decai com tempo)"""
        return max(0.5, 0.95 - (hours_ahead * 0.02))
    
    def predict_peak_times(self, predictions):
        """Identifica horários de pico nas previsões"""
        loads = [p['predicted_load'] for p in predictions]
        mean_load = np.mean(loads)
        std_load = np.std(loads)
        
        peaks = []
        for pred in predictions:
            if pred['predicted_load'] > mean_load + std_load:
                peaks.append({
                    'timestamp': pred['timestamp'],
                    'predicted_load': pred['predicted_load'],
                    'severity': 'high' if pred['predicted_load'] > mean_load + 2*std_load else 'medium'
                })
        
        return peaks
    
    def save_model(self, path):
        """Salva modelo treinado"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'mean': self.mean,
            'std': self.std,
            'trained': self.trained
        }, path)
    
    def load_model(self, path):
        """Carrega modelo treinado"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.mean = checkpoint['mean']
        self.std = checkpoint['std']
        self.trained = checkpoint['trained']
