"""
Configuração do banco de dados PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config
import logging

logger = logging.getLogger(__name__)

# Base para modelos
Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
    
    def init_db(self):
        """Inicializa conexão com PostgreSQL"""
        try:
            self.engine = create_engine(
                Config.DATABASE_URI,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
            
            session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.SessionLocal = scoped_session(session_factory)
            
            logger.info("✅ Conexão com PostgreSQL estabelecida")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            return False
    
    def create_tables(self):
        """Cria todas as tabelas"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tabelas criadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
    
    def drop_tables(self):
        """Remove todas as tabelas (cuidado!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Retorna sessão do banco"""
        return self.SessionLocal()
    
    def close_session(self):
        """Fecha sessão"""
        if self.SessionLocal:
            self.SessionLocal.remove()

# Instância global
db = Database()

def get_db():
    """Dependency para rotas Flask"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
