from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Schémas pour les utilisateurs
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        # orm_mode = True

# Schémas pour les bots
class BotCreate(BaseModel):
    name: str
    token_pair: str
    buy_price_threshold: float
    buy_percentage_drop: float
    sell_price_threshold: float
    sell_percentage_gain: float
    # NOUVEAUX CHAMPS POUR LES MONTANTS
    buy_amount: Optional[float] = Field(0.1, description="Montant à acheter (en token de base)")
    sell_amount: Optional[float] = Field(0.1, description="Montant à vendre (en token de base)")
    min_swap_amount: Optional[float] = Field(0.01, description="Montant minimum pour un swap")
    random_trades_count: Optional[int] = 20
    trading_duration_hours: Optional[int] = 24
    balance: Optional[float] = 0.0
    # Configuration Wallet
    wallet_address: Optional[str] = None
    wallet_private_key: Optional[str] = None
    rpc_endpoint: Optional[str] = "https://polygon-rpc.com"
    wpol_address: Optional[str] = None
    kno_address: Optional[str] = None
    router_address: Optional[str] = None
    quoter_address: Optional[str] = None
    slippage_tolerance: Optional[float] = 1.0
    gas_limit: Optional[int] = 300000
    gas_price: Optional[int] = 30

class BotUpdate(BaseModel):
    name: Optional[str] = None
    buy_price_threshold: Optional[float] = None
    buy_percentage_drop: Optional[float] = None
    sell_price_threshold: Optional[float] = None
    sell_percentage_gain: Optional[float] = None
    # NOUVEAUX CHAMPS POUR LES MONTANTS
    buy_amount: Optional[float] = None
    sell_amount: Optional[float] = None
    min_swap_amount: Optional[float] = None
    random_trades_count: Optional[int] = None
    trading_duration_hours: Optional[int] = None
    balance: Optional[float] = None
    last_buy_price: Optional[float] = None
    last_sell_price: Optional[float] = None
    wallet_address: Optional[str] = None
    wallet_private_key: Optional[str] = None
    rpc_endpoint: Optional[str] = None
    wpol_address: Optional[str] = None
    kno_address: Optional[str] = None
    router_address: Optional[str] = None
    quoter_address: Optional[str] = None
    slippage_tolerance: Optional[float] = None
    gas_limit: Optional[int] = None
    gas_price: Optional[int] = None

class BotResponse(BaseModel):
    id: int
    name: str
    token_pair: str
    is_active: bool
    status: str
    buy_price_threshold: float
    buy_percentage_drop: float
    sell_price_threshold: float
    sell_percentage_gain: float
    # NOUVEAUX CHAMPS POUR LES MONTANTS
    buy_amount: float
    sell_amount: float
    min_swap_amount: float
    random_trades_count: int
    trading_duration_hours: int
    balance: float
    total_profit: float
    last_buy_price: Optional[float]
    last_sell_price: Optional[float]
    created_at: datetime
    updated_at: datetime
    wallet_address: Optional[str]
    rpc_endpoint: Optional[str]
    wpol_address: Optional[str]
    kno_address: Optional[str]
    router_address: Optional[str]
    quoter_address: Optional[str]
    slippage_tolerance: Optional[float]
    gas_limit: Optional[int]
    gas_price: Optional[int]
    # Note: wallet_private_key n'est jamais retournée dans les réponses API
    
    class Config:
        from_attributes = True

# Schémas pour les transactions
class TransactionCreate(BaseModel):
    bot_id: int
    type: str
    amount: float
    price: float
    profit: Optional[float] = None
    tx_hash: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    bot_id: int
    type: str
    amount: float
    price: float
    profit: Optional[float]
    tx_hash: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True