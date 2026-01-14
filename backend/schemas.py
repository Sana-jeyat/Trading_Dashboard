# schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
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
        orm_mode = True

# Schémas pour les bots KNO
class BotCreate(BaseModel):
    name: str
    token_pair: str = "KNO/WPOL"
    volatility_percent: Optional[float] = Field(5.0, description="Pourcentage de volatilité pour déclencher les trades")
    
    # Montants configurables pour KNO
    buy_amount: Optional[float] = Field(0.05, description="Montant WPOL à utiliser pour chaque achat")
    sell_amount: Optional[float] = Field(0.05, description="Montant KNO à vendre à chaque vente")
    min_swap_amount: Optional[float] = Field(0.01, description="Montant minimum pour un swap")
    
    # Paramètres optionnels
    random_trades_count: Optional[int] = 0
    trading_duration_hours: Optional[int] = 24
    balance: Optional[float] = 0.0
    
    # Configuration Wallet
    wallet_address: Optional[str] = None
    wallet_private_key: Optional[str] = None
    rpc_endpoint: Optional[str] = "https://polygon-rpc.com"
    
    # Adresses pour KNO (peuvent être laissées vides pour utiliser les valeurs par défaut)
    wpol_address: Optional[str] = None
    kno_address: Optional[str] = None
    router_address: Optional[str] = None
    
    # Paramètres de transaction
    slippage_tolerance: Optional[float] = 1.0
    gas_limit: Optional[int] = 300000
    gas_price: Optional[int] = 30
    
    @validator('volatility_percent')
    def validate_volatility(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('La volatilité doit être entre 0 et 100%')
        return v
    
    @validator('buy_amount', 'sell_amount')
    def validate_amounts(cls, v, values):
        min_swap = values.get('min_swap_amount', 0.01)
        if v < min_swap:
            raise ValueError(f'Le montant doit être au moins {min_swap}')
        return v

class BotUpdate(BaseModel):
    name: Optional[str] = None
    volatility_percent: Optional[float] = None
    
    # Montants configurables
    buy_amount: Optional[float] = None
    sell_amount: Optional[float] = None
    min_swap_amount: Optional[float] = None
    
    # Prix de référence pour KNO
    reference_price: Optional[float] = None
    
    # Paramètres divers
    random_trades_count: Optional[int] = None
    trading_duration_hours: Optional[int] = None
    balance: Optional[float] = None
    last_buy_price: Optional[float] = None
    last_sell_price: Optional[float] = None
    total_profit: Optional[float] = None
    
    # Configuration Wallet
    wallet_address: Optional[str] = None
    wallet_private_key: Optional[str] = None
    rpc_endpoint: Optional[str] = None
    wpol_address: Optional[str] = None
    kno_address: Optional[str] = None
    router_address: Optional[str] = None
    slippage_tolerance: Optional[float] = None
    gas_limit: Optional[int] = None
    gas_price: Optional[int] = None
    
    # État
    status: Optional[str] = None
    is_active: Optional[bool] = None

class BotResponse(BaseModel):
    id: int
    name: str
    token_pair: str
    is_active: bool
    status: str
    
    # Paramètres KNO
    volatility_percent: float
    buy_amount: float
    sell_amount: float
    min_swap_amount: float
    reference_price: Optional[float]
    
    # Statistiques
    random_trades_count: int
    trading_duration_hours: int
    balance: float
    total_profit: float
    last_buy_price: Optional[float]
    last_sell_price: Optional[float]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Configuration
    wallet_address: Optional[str]
    rpc_endpoint: Optional[str]
    wpol_address: Optional[str]
    kno_address: Optional[str]
    router_address: Optional[str]
    slippage_tolerance: Optional[float]
    gas_limit: Optional[int]
    gas_price: Optional[int]
    
    class Config:
        from_attributes = True

# Schéma spécifique pour la configuration KNO (pour le bot)
class KNOBotConfig(BaseModel):
    bot_id: int
    name: str
    token_pair: str
    volatility_percent: float
    buy_amount: float
    sell_amount: float
    min_swap_amount: float
    reference_price: Optional[float]
    wallet_address: Optional[str]
    wallet_private_key: Optional[str]
    rpc_endpoint: str
    slippage_tolerance: float
    gas_limit: int
    gas_price: int
    wpol_address: str
    kno_address: str
    router_address: str
    status: str
    is_active: bool

# Schéma pour mettre à jour le prix de référence
class ReferencePriceUpdate(BaseModel):
    price: float

# Schéma pour configuration wallet
class WalletConfig(BaseModel):
    wallet_address: str
    wallet_private_key: str
    rpc_endpoint: str
    wpol_address: Optional[str] = None
    kno_address: Optional[str] = None
    router_address: Optional[str] = None

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