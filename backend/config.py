import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'ecogrid')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'senha123')
    
    DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # IoT Simulation
    IOT_SAMPLING_RATE = 5  # segundos
    MAX_NODES = 1000
    
    # ML
    MODEL_PATH = 'ml/models/demand_predictor.pth'
    TRAINING_EPOCHS = 100
    BATCH_SIZE = 32
