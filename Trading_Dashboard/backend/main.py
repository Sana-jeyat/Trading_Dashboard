"""Backend principal pour l'API FastAPI du tableau de bord de trading.
Adapté pour le bot KNO sur Polygon.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta, timezone
import asyncio
import json
import logging
import requests

from utils import get_current_price
from database import SessionLocal, engine, Base
from models import Bot, Transaction, User
from schemas import BotCreate, BotUpdate, BotResponse, TransactionResponse, TransactionCreate, UserCreate, UserResponse, KNOBotConfig, ReferencePriceUpdate, WalletConfig
from auth import create_access_token, verify_token, get_password_hash, verify_password
from bot_manager import BotManager
from wallet_security import wallet_security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KNO Trading Bot API", version="2.0.0")

# Configuration CORS pour le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permettre toutes les origines pour l'accès réseau
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
bot_manager = BotManager()

# Route pour vérifier la connectivité réseau
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "KNO Trading Bot API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Dependency pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency pour l'authentification
async def get_current_user(db: Session = Depends(get_db)):
    # Retourne toujours le premier utilisateur (pour les tests)
    user = db.query(User).first()
    if not user:
        # Crée un utilisateur par défaut si aucun n'existe
        user = User(email="test@example.com", hashed_password=get_password_hash("password123"))
        db.add(user)
        db.commit()
        db.refresh(user)
        print("✅ Utilisateur test créé automatiquement")
    return user

@app.get("/")
async def root():
    return {"message": "KNO Trading Bot API is running"}

# Routes d'authentification
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'utilisateur existe déjà
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    
    # Créer l'utilisateur
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(id=db_user.id, email=db_user.email, created_at=db_user.created_at)

@app.post("/auth/login")
async def login(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier les identifiants
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    # Créer le token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Routes pour les bots
@app.get("/bots", response_model=List[BotResponse])
async def get_bots(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bots = db.query(Bot).filter(Bot.user_id == current_user.id).all()
    
    # Traiter les bots pour assurer des valeurs par défaut
    processed_bots = []
    for bot in bots:
        # Créer un dict avec des valeurs par défaut
        bot_dict = {
            "id": bot.id,
            "name": bot.name,
            "token_pair": bot.token_pair or "KNO/WPOL",
            "is_active": bot.is_active if bot.is_active is not None else False,
            "status": bot.status or "paused",
            
            # Paramètres KNO avec valeurs par défaut
            "volatility_percent": bot.volatility_percent if bot.volatility_percent is not None else 5.0,
            "buy_amount": bot.buy_amount if bot.buy_amount is not None else 0.05,
            "sell_amount": bot.sell_amount if bot.sell_amount is not None else 0.05,
            "min_swap_amount": bot.min_swap_amount if bot.min_swap_amount is not None else 0.01,
            "reference_price": bot.reference_price,
            
            # Trading
            "random_trades_count": bot.random_trades_count if bot.random_trades_count is not None else 0,
            "trading_duration_hours": bot.trading_duration_hours if bot.trading_duration_hours is not None else 24,
            
            # Wallet
            "wallet_address": bot.wallet_address,
            "rpc_endpoint": bot.rpc_endpoint or "https://polygon-rpc.com",
            
            # Adresses
            "wpol_address": bot.wpol_address or "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
            "kno_address": bot.kno_address or "0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631",
            "router_address": bot.router_address or "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
            "quoter_address": bot.quoter_address,
            
            # Transaction
            "slippage_tolerance": bot.slippage_tolerance if bot.slippage_tolerance is not None else 1.0,
            "gas_limit": bot.gas_limit if bot.gas_limit is not None else 300000,
            "gas_price": bot.gas_price if bot.gas_price is not None else 30,
            
            # Stats
            "balance": bot.balance if bot.balance is not None else 0.0,
            "total_profit": bot.total_profit if bot.total_profit is not None else 0.0,
            "last_buy_price": bot.last_buy_price,
            "last_sell_price": bot.last_sell_price,
            
            # Champs hérités
            "buy_price_threshold": bot.buy_price_threshold if bot.buy_price_threshold is not None else 0.0,
            "buy_percentage_drop": bot.buy_percentage_drop if bot.buy_percentage_drop is not None else 0.0,
            "sell_price_threshold": bot.sell_price_threshold if bot.sell_price_threshold is not None else 0.0,
            "sell_percentage_gain": bot.sell_percentage_gain if bot.sell_percentage_gain is not None else 0.0,
            
            # Timestamps
            "created_at": bot.created_at,
            "updated_at": bot.updated_at,
        }
        processed_bots.append(bot_dict)
    
    return processed_bots

@app.post("/bots", response_model=BotResponse)
async def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    # Validation des données wallet si fournies
    if bot.wallet_address and not wallet_security.validate_wallet_address(bot.wallet_address):
        raise HTTPException(status_code=400, detail="Format d'adresse wallet invalide")
    
    if bot.wallet_private_key and not wallet_security.validate_private_key(bot.wallet_private_key):
        raise HTTPException(status_code=400, detail="Format de clé privée invalide")
    
    # Chiffrer la clé privée si fournie
    encrypted_private_key = None
    if bot.wallet_private_key:
        try:
            encrypted_private_key = wallet_security.encrypt_private_key(bot.wallet_private_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Erreur lors du chiffrement de la clé privée")
    
    # Préparer les données du bot
    bot_data = bot.dict(exclude={'wallet_private_key'})
    bot_data['wallet_private_key_encrypted'] = encrypted_private_key
    
    # Remplir les adresses par défaut si non fournies
    if not bot_data.get('wpol_address'):
        bot_data['wpol_address'] = "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270"
    if not bot_data.get('kno_address'):
        bot_data['kno_address'] = "0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631"
    if not bot_data.get('router_address'):
        bot_data['router_address'] = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
    
    # Créer le bot dans la DB
    user = await get_current_user(db)
    db_bot = Bot(**bot_data, user_id=user.id)
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    logger.info(f"Bot KNO créé: {db_bot.name} (ID: {db_bot.id})")
    return db_bot

@app.get("/bots/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    return bot

@app.get("/bots/{bot_id}/kno-config", response_model=KNOBotConfig)
async def get_kno_bot_config(
    bot_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Retourne la configuration spécifique pour le bot KNO
    Utilisé par le bot distant pour récupérer sa configuration
    """
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Déchiffrer la clé privée
    private_key = ""
    if bot.wallet_private_key_encrypted:
        try:
            private_key = wallet_security.decrypt_private_key(bot.wallet_private_key_encrypted)
        except Exception as e:
            logger.error(f"Erreur déchiffrement clé privée bot {bot_id}: {str(e)}")
            # Ne pas lever d'exception pour ne pas bloquer le bot
    
    return KNOBotConfig(
        bot_id=bot.id,
        name=bot.name,
        token_pair=bot.token_pair,
        volatility_percent=bot.volatility_percent,
        buy_amount=bot.buy_amount,
        sell_amount=bot.sell_amount,
        min_swap_amount=bot.min_swap_amount,
        reference_price=bot.reference_price,
        wallet_address=bot.wallet_address,
        wallet_private_key=private_key,
        rpc_endpoint=bot.rpc_endpoint,
        slippage_tolerance=bot.slippage_tolerance,
        gas_limit=bot.gas_limit,
        gas_price=bot.gas_price,
        wpol_address=bot.wpol_address,
        kno_address=bot.kno_address,
        router_address=bot.router_address,
        status=bot.status,
        is_active=bot.is_active
    )

@app.get("/bots/{bot_id}/wallet-config")
async def get_bot_wallet_config(
    bot_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Retourne la configuration wallet déchiffrée pour le bot distant"""
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Déchiffrer la clé privée
    private_key = ""
    if bot.wallet_private_key_encrypted:
        try:
            private_key = wallet_security.decrypt_private_key(bot.wallet_private_key_encrypted)
        except Exception as e:
            logger.error(f"Erreur déchiffrement clé privée bot {bot_id}: {str(e)}")
    
    return {
        "wallet_address": bot.wallet_address,
        "wallet_private_key": private_key,
        "rpc_endpoint": bot.rpc_endpoint,
        "wpol_address": bot.wpol_address,
        "kno_address": bot.kno_address,
        "router_address": bot.router_address,
        "slippage_tolerance": bot.slippage_tolerance,
        "gas_limit": bot.gas_limit,
        "gas_price": bot.gas_price,
        "volatility_percent": bot.volatility_percent,
        "buy_amount": bot.buy_amount,
        "sell_amount": bot.sell_amount,
        "min_swap_amount": bot.min_swap_amount,
        "reference_price": bot.reference_price
    }

@app.put("/bots/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int, 
    bot_update: BotUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Validation des données wallet si mises à jour
    if bot_update.wallet_address and not wallet_security.validate_wallet_address(bot_update.wallet_address):
        raise HTTPException(status_code=400, detail="Format d'adresse wallet invalide")
    
    if bot_update.wallet_private_key and not wallet_security.validate_private_key(bot_update.wallet_private_key):
        raise HTTPException(status_code=400, detail="Format de clé privée invalide")
    
    # Chiffrer la nouvelle clé privée si fournie
    if bot_update.wallet_private_key:
        try:
            encrypted_private_key = wallet_security.encrypt_private_key(bot_update.wallet_private_key)
            bot.wallet_private_key_encrypted = encrypted_private_key
        except Exception as e:
            raise HTTPException(status_code=500, detail="Erreur lors du chiffrement de la clé privée")
    
    # Mettre à jour les champs
    update_data = bot_update.dict(exclude_unset=True)
    update_data.pop('wallet_private_key', None)  # Supprimer la clé en clair (déjà traitée)
    
    for field, value in update_data.items():
        if hasattr(bot, field):
            setattr(bot, field, value)
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)
    
    logger.info(f"Configuration du bot {bot_id} mise à jour")
    
    return bot

@app.delete("/bots/{bot_id}")
async def delete_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Arrêter le bot s'il est actif
    if bot.is_active:
        await bot_manager.stop_bot(bot_id)
    
    db.delete(bot)
    db.commit()
    return {"message": "Bot supprimé avec succès"}

@app.put("/bots/{bot_id}/reference-price")
async def update_reference_price(
    bot_id: int,
    price_data: ReferencePriceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier que le bot appartient bien à l'utilisateur
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")

    # Mettre à jour le prix de référence
    bot.reference_price = price_data.price
    bot.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(bot)

    logger.info(f"Prix de référence du bot {bot_id} mis à jour : {bot.reference_price}")

    return {
        "bot_id": bot.id,
        "reference_price": bot.reference_price
    }

@app.put("/bots/{bot_id}/wallet")
async def update_wallet(
    bot_id: int, 
    wallet: WalletConfig, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Met à jour la configuration wallet du bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Validation
    if not wallet_security.validate_wallet_address(wallet.wallet_address):
        raise HTTPException(status_code=400, detail="Format d'adresse wallet invalide")
    
    if not wallet_security.validate_private_key(wallet.wallet_private_key):
        raise HTTPException(status_code=400, detail="Format de clé privée invalide")
    
    # Chiffrer la clé privée
    try:
        encrypted_private_key = wallet_security.encrypt_private_key(wallet.wallet_private_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur lors du chiffrement de la clé privée")
    
    # Mettre à jour
    bot.wallet_address = wallet.wallet_address
    bot.wallet_private_key_encrypted = encrypted_private_key
    bot.rpc_endpoint = wallet.rpc_endpoint or bot.rpc_endpoint
    bot.wpol_address = wallet.wpol_address or bot.wpol_address
    bot.kno_address = wallet.kno_address or bot.kno_address
    bot.router_address = wallet.router_address or bot.router_address
    bot.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Wallet du bot {bot_id} mis à jour")
    return {"message": "Wallet mis à jour avec succès"}

@app.post("/bots/{bot_id}/start")
async def start_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Initialiser le prix de référence si pas déjà défini
    if not bot.reference_price or bot.reference_price == 0:
        try:
            # Tenter de récupérer le prix actuel de KNO
            price_data = await get_kno_price()
            current_price = price_data.get("price_eur", 0)
            bot.reference_price = current_price
        except:
            # Si échec, utiliser une valeur par défaut
            bot.reference_price = 0.001
    
    bot.is_active = True
    bot.status = "active"
    bot.updated_at = datetime.utcnow()
    db.commit()
    
    # Démarrer le bot via le bot manager
    await bot_manager.start_bot(bot)
    
    return {"message": "Bot démarré", "reference_price": bot.reference_price}

@app.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    bot.is_active = False
    bot.status = "paused"
    bot.updated_at = datetime.utcnow()
    db.commit()
    
    # Arrêter le bot via le bot manager
    await bot_manager.stop_bot(bot_id)
    
    return {"message": "Bot arrêté"}

# Route pour mettre à jour le statut du bot
@app.put("/bots/{bot_id}/status")
async def update_bot_status(
    bot_id: int, 
    status_data: dict, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    bot.status = status_data.get("status", bot.status)
    
    # Mettre à jour is_active en fonction du status
    if status_data.get("status") == "active":
        bot.is_active = True
    elif status_data.get("status") in ["paused", "error", "offline"]:
        bot.is_active = False
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Statut mis à jour: {bot.status}"}

@app.get("/bots/{bot_id}/heartbeat")
async def bot_heartbeat(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Mettre à jour le timestamp de dernière activité
    bot.last_heartbeat = datetime.utcnow()
    bot.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "alive", "timestamp": bot.last_heartbeat.isoformat()}

# Routes pour les transactions
@app.post("/transactions", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle transaction"""
    try:
        # Vérifier que le bot existe
        bot = db.query(Bot).filter(Bot.id == transaction.bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot non trouvé")
        
        # Créer la transaction
        db_transaction = Transaction(
            bot_id=transaction.bot_id,
            type=transaction.type,
            amount=transaction.amount,
            price=transaction.price,
            profit=transaction.profit,
            tx_hash=transaction.tx_hash
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        # Mettre à jour les stats du bot
        if transaction.type == 'buy':
            bot.last_buy_price = transaction.price
        elif transaction.type == 'sell':
            bot.last_sell_price = transaction.price
            
        if transaction.profit:
            bot.total_profit += transaction.profit
        
        bot.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Transaction enregistrée: {transaction.type} {transaction.amount} KNO à {transaction.price}€")
        return db_transaction
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur création transaction: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la transaction")

@app.get("/bots/{bot_id}/transactions", response_model=List[TransactionResponse])
async def get_transactions(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Vérifier que le bot appartient à l'utilisateur
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    transactions = db.query(Transaction).filter(Transaction.bot_id == bot_id).order_by(Transaction.timestamp.desc()).all()
    return transactions

@app.get("/transactions", response_model=List[TransactionResponse])
async def get_all_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Récupérer toutes les transactions des bots de l'utilisateur
    transactions = db.query(Transaction).join(Bot).filter(Bot.user_id == current_user.id).order_by(Transaction.timestamp.desc()).all()
    return transactions

# Route pour les statistiques
@app.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bots = db.query(Bot).filter(Bot.user_id == current_user.id).all()
    
    total_balance = sum(bot.balance for bot in bots)
    total_profit = sum(bot.total_profit for bot in bots)
    active_bots = sum(1 for bot in bots if bot.is_active)
    
    # PnL du jour
    today = datetime.utcnow().date()
    today_transactions = db.query(Transaction).join(Bot).filter(
        Bot.user_id == current_user.id,
        Transaction.timestamp >= today
    ).all()
    
    today_pnl = sum(t.profit for t in today_transactions if t.profit)
    
    # Statistiques KNO spécifiques
    kno_bots = [b for b in bots if "KNO" in b.token_pair]
    total_kno_trades = db.query(Transaction).join(Bot).filter(
        Bot.user_id == current_user.id,
        Bot.token_pair.like("%KNO%")
    ).count()
    
    return {
        "total_balance": total_balance,
        "total_profit": total_profit,
        "active_bots": active_bots,
        "total_bots": len(bots),
        "today_pnl": today_pnl,
        "kno_bots": len(kno_bots),
        "total_kno_trades": total_kno_trades,
        "avg_volatility": sum(b.volatility_percent for b in bots) / len(bots) if bots else 0
    }

# Routes KNO spécifiques
@app.get("/kno/price")
async def get_kno_price():
    """
    Récupère le prix actuel de KNO en EUR via GeckoTerminal
    """
    try:
        GECKO_TERMINAL_URL = "https://api.geckoterminal.com/api/v2/networks/polygon_pos/pools/0xdce471c5fc17879175966bea3c9fe0432f9b189e"
        
        response = requests.get(GECKO_TERMINAL_URL, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        price_usd = float(data["data"]["attributes"]["base_token_price_usd"])
        price_eur = price_usd * 0.87  # Conversion USD → EUR
        
        return {
            "price_eur": price_eur,
            "price_usd": price_usd,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "GeckoTerminal"
        }
    except Exception as e:
        logger.error(f"Erreur récupération prix KNO: {str(e)}")
        # Retourner une valeur par défaut en cas d'erreur
        return {
            "price_eur": 0.001,
            "price_usd": 0.00115,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "fallback",
            "error": str(e)
        }

@app.get("/bots/{bot_id}/dashboard-stats")
async def get_bot_dashboard_stats(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne les statistiques pour le dashboard spécifique au bot KNO
    """
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Récupérer les dernières transactions
    transactions = db.query(Transaction).filter(
        Transaction.bot_id == bot_id
    ).order_by(Transaction.timestamp.desc()).limit(10).all()
    
    # Calculer les stats
    today = datetime.utcnow().date()
    today_transactions = db.query(Transaction).filter(
        Transaction.bot_id == bot_id,
        Transaction.timestamp >= today
    ).all()
    
    today_trades = len(today_transactions)
    today_profit = sum(t.profit or 0 for t in today_transactions)
    
    # Total trades
    total_trades = db.query(Transaction).filter(Transaction.bot_id == bot_id).count()
    
    # Performance
    buy_trades = db.query(Transaction).filter(
        Transaction.bot_id == bot_id,
        Transaction.type == 'buy'
    ).count()
    
    sell_trades = db.query(Transaction).filter(
        Transaction.bot_id == bot_id,
        Transaction.type == 'sell'
    ).count()
    
    # Calculer le seuil d'achat et de vente
    buy_threshold = None
    sell_threshold = None
    if bot.reference_price:
        volatility = bot.volatility_percent / 100
        buy_threshold = bot.reference_price * (1 - volatility)
        sell_threshold = bot.reference_price * (1 + volatility)
    
    # Taux de succès
    success_rate = 0
    if buy_trades > 0:
        success_rate = (sell_trades / buy_trades * 100) if buy_trades > 0 else 0
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "status": bot.status,
        "is_active": bot.is_active,
        "volatility_percent": bot.volatility_percent,
        "reference_price": bot.reference_price,
        "buy_threshold": buy_threshold,
        "sell_threshold": sell_threshold,
        "current_balance": bot.balance,
        "total_profit": bot.total_profit,
        "stats": {
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "today_trades": today_trades,
            "today_profit": today_profit,
            "success_rate": round(success_rate, 1)
        },
        "configuration": {
            "buy_amount": bot.buy_amount,
            "sell_amount": bot.sell_amount,
            "min_swap_amount": bot.min_swap_amount,
            "slippage_tolerance": bot.slippage_tolerance,
            "gas_price": bot.gas_price,
            "wallet_configured": bool(bot.wallet_address)
        },
        "recent_transactions": [
            {
                "id": t.id,
                "type": t.type,
                "amount": t.amount,
                "price": t.price,
                "profit": t.profit,
                "timestamp": t.timestamp.isoformat()
            }
            for t in transactions
        ]
    }

# Endpoint pour tester la configuration KNO
@app.get("/kno/test-config/{bot_id}")
async def test_kno_config(bot_id: int, db: Session = Depends(get_db)):
    """
    Endpoint de test pour vérifier la configuration KNO
    (Pas besoin d'authentification pour les tests)
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Récupérer le prix KNO
    price_data = await get_kno_price()
    
    # Calculer les seuils
    buy_threshold = None
    sell_threshold = None
    if bot.reference_price:
        volatility = bot.volatility_percent / 100
        buy_threshold = bot.reference_price * (1 - volatility)
        sell_threshold = bot.reference_price * (1 + volatility)
    
    return {
        "bot": {
            "id": bot.id,
            "name": bot.name,
            "status": bot.status,
            "volatility_percent": bot.volatility_percent,
            "reference_price": bot.reference_price,
            "buy_amount": bot.buy_amount,
            "sell_amount": bot.sell_amount,
            "wallet_address": bot.wallet_address,
            "is_active": bot.is_active
        },
        "current_price": price_data.get("price_eur"),
        "thresholds": {
            "buy": buy_threshold,
            "sell": sell_threshold
        },
        "should_buy": buy_threshold and price_data.get("price_eur", 0) <= buy_threshold,
        "should_sell": sell_threshold and price_data.get("price_eur", 0) >= sell_threshold
    }

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Démarrage de l'API KNO Trading Bot")
    logger.info("📡 API accessible sur : http://0.0.0.0:8000")
    logger.info("🤖 Configuration KNO prête pour le bot sur Polygon")
    
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")