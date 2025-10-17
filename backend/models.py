from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    bots = relationship("Bot", back_populates="user", cascade="all, delete-orphan")


class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    token_pair = Column(String(50), nullable=False, default="")  # pour éviter erreur
    is_active = Column(Boolean, default=False)
    status = Column(String(20), default="paused")  # active, paused, error

    # Réseau
    ip_address = Column(String(50), nullable=True)  # nullable pour MySQL
    port = Column(Integer, default=8000)

    # Paramètres de trading
    buy_price_threshold = Column(Float, nullable=False)
    buy_percentage_drop = Column(Float, nullable=False)
    sell_price_threshold = Column(Float, nullable=False)
    sell_percentage_gain = Column(Float, nullable=False)
    
    # Paramètres aléatoires
    random_trades_count = Column(Integer, default=20)
    trading_duration_hours = Column(Integer, default=24)
    
    # Métriques
    balance = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    last_buy_price = Column(Float, nullable=True)
    last_sell_price = Column(Float, nullable=True)
    
    # Métadonnées
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Configuration Wallet (chiffrée)
    wallet_address = Column(String(100), nullable=True)
    wallet_private_key_encrypted = Column(Text, nullable=True)
    rpc_endpoint = Column(String(255), default="https://polygon-rpc.com")
    wpol_address = Column(String(100), nullable=True)
    kno_address = Column(String(100), nullable=True)
    router_address = Column(String(100), nullable=True)
    quoter_address = Column(String(100), nullable=True)
    slippage_tolerance = Column(Float, default=1.0)
    gas_limit = Column(Integer, default=300000)
    gas_price = Column(Integer, default=30)
    
    # Relations
    user = relationship("User", back_populates="bots")
    transactions = relationship("Transaction", back_populates="bot", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    type = Column(String(20), nullable=False)  # buy, sell
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    profit = Column(Float, nullable=True)
    
    tx_hash = Column(String(255), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    bot = relationship("Bot", back_populates="transactions")
