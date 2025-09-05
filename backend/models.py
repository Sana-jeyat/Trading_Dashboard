from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    bots = relationship("Bot", back_populates="user", cascade="all, delete-orphan")

class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    token_pair = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    status = Column(String, default="paused")  # active, paused, error
    
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Configuration Wallet (chiffrée)
    wallet_address = Column(String, nullable=True)
    wallet_private_key_encrypted = Column(Text, nullable=True)  # Clé privée chiffrée
    rpc_endpoint = Column(String, default="https://polygon-rpc.com")
    wpol_address = Column(String, nullable=True)
    kno_address = Column(String, nullable=True)
    router_address = Column(String, nullable=True)
    quoter_address = Column(String, nullable=True)
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
    
    type = Column(String, nullable=False)  # buy, sell
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    profit = Column(Float, nullable=True)
    
    # Hash de transaction blockchain (optionnel)
    tx_hash = Column(String, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    bot = relationship("Bot", back_populates="transactions")