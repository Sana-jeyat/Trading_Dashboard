# models.py
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
    token_pair = Column(String(50), nullable=False, default="KNO/WPOL")
    is_active = Column(Boolean, default=False)
    status = Column(String(20), default="paused")  # active, paused, error, offline
    
    # Paramètres de trading KNO
    volatility_percent = Column(Float, default=5.0)  # volatilité pour déclencher les trades
    buy_amount = Column(Float, default=0.05)         # montant WPOL à acheter
    sell_amount = Column(Float, default=0.05)        # montant KNO à vendre
    min_swap_amount = Column(Float, default=0.01)    # montant minimum pour swap
    reference_price = Column(Float, nullable=True)   # prix de référence dynamique
    
    # Paramètres aléatoires (optionnels)
    random_trades_count = Column(Integer, default=0)
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
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration Wallet (chiffrée)
    wallet_address = Column(String(100), nullable=True)
    wallet_private_key_encrypted = Column(Text, nullable=True)
    rpc_endpoint = Column(String(255), default="https://polygon-rpc.com")
    
    # Adresses pour KNO (avec valeurs par défaut)
    wpol_address = Column(String(100), default="0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270")
    kno_address = Column(String(100), default="0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631")
    router_address = Column(String(100), default="0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")
    quoter_address = Column(String(100), nullable=True)
    
    # Paramètres de transaction
    slippage_tolerance = Column(Float, default=1.0)  # en %
    gas_limit = Column(Integer, default=300000)
    gas_price = Column(Integer, default=30)
    
    # Anciens champs (pour compatibilité, à garder mais non utilisés par KNO)
    buy_price_threshold = Column(Float, default=0.0)
    buy_percentage_drop = Column(Float, default=0.0)
    sell_price_threshold = Column(Float, default=0.0)
    sell_percentage_gain = Column(Float, default=0.0)
    
    # Bot token pour authentification machine → utile pour endpoints /public
    bot_token = Column(String(255), nullable=True, unique=True, index=True)
    
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