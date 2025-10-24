"""Backend principal pour l'API FastAPI du tableau de bord de trading.
Gestion des utilisateurs (register/login + token JWT) → OK

CRUD des bots (/bots, /bots/{id}, /bots/{id}/update) → OK

Gestion des wallets sécurisée (clé privée chiffrée) → OK

Transactions et stats consolidées → OK

Endpoints pour le monitoring (/status, /heartbeat) → OK"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import asyncio
import json
import logging

from database import SessionLocal, engine, Base
from models import Bot, Transaction, User
from schemas import BotCreate, BotUpdate, BotResponse, TransactionResponse,TransactionCreate, UserCreate, UserResponse
from auth import create_access_token, verify_token, get_password_hash, verify_password
from bot_manager import BotManager
from wallet_security import wallet_security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trading Bot API", version="1.0.0")

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
        "message": "Trading Bot API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Route pour télécharger le client Python
# @app.get("/download/remote_bot_client.py")
# async def download_client():
#     """Télécharge le client Python pour connecter un bot distant"""
#     from fastapi.responses import FileResponse
#     try:
#         return FileResponse(
#             path="remote_bot_client.py",
#             filename="remote_bot_client.py",
#             media_type="text/plain"
#         )
#     except FileNotFoundError:
#         # Si le fichier n'existe pas, retourner le contenu directement
#         from fastapi.responses import PlainTextResponse
#         with open("remote_bot_client.py", "r", encoding="utf-8") as f:
#             content = f.read()
#         return PlainTextResponse(content, headers={"Content-Disposition": "attachment; filename=remote_bot_client.py"})

# Dependency pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

# Dependency pour l'authentification
# async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
#     token = credentials.credentials
#     user_id = verify_token(token)
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Token invalide")
    
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
#     return user

# async def get_current_user(db: Session = Depends(get_db)):
#     # ⚠️ TEMPORAIRE : Ignorer le token et retourner un user par défaut
#     user = db.query(User).first()
#     if not user:
#         from auth import get_password_hash
#         user = User(email="test@example.com", hashed_password=get_password_hash("password123"))
#         db.add(user)
#         db.commit()
#         db.refresh(user)
#     return user

async def get_current_user(db: Session = Depends(get_db)):  # ← Enlevez le token!
    # Retourne toujours le premier utilisateur (pour les tests)
    user = db.query(User).first()
    if not user:
        # Crée un utilisateur par défaut si aucun n'existe
        from auth import get_password_hash
        user = User(email="test@example.com", hashed_password=get_password_hash("password123"))
        db.add(user)
        db.commit()
        db.refresh(user)
        print("✅ Utilisateur test créé automatiquement")
    return user

@app.get("/")
async def root():
    return {"message": "Trading Bot API is running"}

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
    return bots

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
    
    # Créer le bot avec les données wallet
    bot_data = bot.dict()
    bot_data['wallet_private_key_encrypted'] = encrypted_private_key
    bot_data.pop('wallet_private_key', None)  # Supprimer la clé en clair
    
    # db_bot = Bot(**bot_data, user_id=current_user.id)
    user = await get_current_user(db)  # ← Récupère l'user ici
    db_bot = Bot(**bot_data, user_id=user.id)  # ← Utilise user.id
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot

@app.get("/bots/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    return bot

@app.get("/bots/{bot_id}/wallet-config")
async def get_bot_wallet_config(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
            raise HTTPException(status_code=500, detail="Erreur lors du déchiffrement")
    
    return {
        "wallet_address": bot.wallet_address,
        "wallet_private_key": private_key,
        "rpc_endpoint": bot.rpc_endpoint,
        "wpol_address": bot.wpol_address,
        "kno_address": bot.kno_address,
        "router_address": bot.router_address,
        "quoter_address": bot.quoter_address,
        "slippage_tolerance": bot.slippage_tolerance,
        "gas_limit": bot.gas_limit,
        "gas_price": bot.gas_price
    }

@app.put("/bots/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: int, bot_update: BotUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
        setattr(bot, field, value)
    
    bot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot)
    
    # Notifier le bot distant que la config a changé (optionnel)
    logger.info(f"Configuration du bot {bot_id} mise à jour")
    
    return bot

@app.delete("/bots/{bot_id}")
async def delete_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Arrêter le bot s'il est actif
    #if bot.is_active:
    #    await bot_manager.stop_bot(bot_id)
    
    db.delete(bot)
    db.commit()
    return {"message": "Bot supprimé avec succès"}

@app.post("/bots/{bot_id}/start")
async def start_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    await bot_manager.start_bot(bot)
    bot.is_active = True
    bot.status = "active"
    db.commit()
    return {"message": "Instruction envoyée au bot (il doit s'activer)"}
    
@app.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    await bot_manager.stop_bot(bot_id)
    bot.is_active = False
    bot.status = "paused"
    db.commit()
    return {"message": "Instruction envoyée au bot (il doit s’arrêter)"}
    
# Route pour mettre à jour le statut du bot (online/offline) et son état (active/paused) 
# via le heartbeat
# Le bot distant appelle cette route périodiquement pour indiquer qu'il est en ligne et actif ou en pause. 
@app.put("/bots/{bot_id}/status")
async def update_bot_status(bot_id: int, status_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    bot.status = status_data.get("status", bot.status)
    if status_data.get("status") == "online":
        bot.is_active = True
    elif status_data.get("status") == "offline":
        bot.is_active = False
    
    db.commit()
    return {"message": "Statut mis à jour"}

@app.get("/bots/{bot_id}/heartbeat")
async def bot_heartbeat(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot non trouvé")
    
    # Mettre à jour le timestamp de dernière activité
    bot.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "alive"}

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
            
        db.commit()
        
        logger.info(f"Transaction enregistrée: {transaction.type} {transaction.amount} pour bot {transaction.bot_id}")
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
    
    return {
        "total_balance": total_balance,
        "total_profit": total_profit,
        "active_bots": active_bots,
        "total_bots": len(bots),
        "today_pnl": today_pnl
    }

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Démarrage de l'API Trading Bot")
    logger.info("📡 API accessible sur : http://0.0.0.0:8000")
    logger.info("📊 Dashboard sur : http://localhost:5173")
    logger.info("🔗 Client Python : http://localhost:8000/download/remote_bot_client.py")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")