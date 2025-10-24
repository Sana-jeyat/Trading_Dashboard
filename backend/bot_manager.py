import asyncio
import subprocess
import signal
import os
from typing import Dict, Optional
from models import Bot
from database import SessionLocal
import json
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.running_bots: Dict[int, subprocess.Popen] = {}
        self.bot_configs_dir = "bot_configs"
        self.bot_info: Dict[int, dict] = {}
        
        os.makedirs(self.bot_configs_dir, exist_ok=True)
    
    async def start_bot(self, bot: Bot):
        """Démarre un bot de trading"""
        if bot.id in self.running_bots:
            logger.info(f"Bot {bot.id} déjà en cours d'exécution")
            return
        
        self.bot_info[bot.id] = {
            'id': bot.id,
            'name': bot.name,
            'pid': None
        }
        
        # Créer le fichier de configuration pour le bot
        config_file = self._create_bot_config(bot)
        
        command = ["python", "trading_bot.py"]
        
        try:
            env = os.environ.copy()
            env.update({
                'BOT_ID': str(bot.id),
                'API_URL': 'http://localhost:8000'
            })
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.running_bots[bot.id] = process
            self.bot_info[bot.id]['pid'] = process.pid
            
            logger.info(f"Bot {bot.id} ({bot.name}) démarré avec PID {process.pid}")
            
            def log_output(pipe, logger_func, bot_id):
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            # Utiliser le niveau INFO au lieu de ERROR pour les logs normaux
                            if "ERROR" in line:
                                logger_func(f"BOT_{bot_id}: {line.strip()}")
                            else:
                                logging.info(f"BOT_{bot_id}: {line.strip()}")
                except Exception as e:
                    logger.error(f"Erreur lecture sortie bot {bot_id}: {e}")
            
            threading.Thread(
                target=log_output, 
                args=(process.stdout, logger.info, bot.id),
                daemon=True
            ).start()
            
            threading.Thread(
                target=log_output, 
                args=(process.stderr, logger.error, bot.id),
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot {bot.id}: {str(e)}")
            if bot.id in self.bot_info:
                del self.bot_info[bot.id]
            raise
    
    async def stop_bot(self, bot_id: int):
        """Arrête un bot de trading"""
        if bot_id not in self.running_bots:
            logger.info(f"Bot {bot_id} non trouvé dans les processus en cours")
            return
        
        process = self.running_bots[bot_id]
        
        try:
            bot_name = self.bot_info.get(bot_id, {}).get('name', 'Unknown')
            logger.info(f"Arrêt du bot {bot_id} ({bot_name}) - PID: {process.pid}")
            
            process.terminate()
            
            try:
                process.wait(timeout=5)
                logger.info(f"Bot {bot_id} arrêté proprement")
            except subprocess.TimeoutExpired:
                logger.warning(f"Bot {bot_id} ne répond pas, kill forcé")
                process.kill()
                process.wait()
            
            del self.running_bots[bot_id]
            if bot_id in self.bot_info:
                del self.bot_info[bot_id]
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du bot {bot_id}: {str(e)}")
            raise
    
    def _create_bot_config(self, bot: Bot) -> str:
        """Crée un fichier de configuration JSON pour le bot"""
        config = {
            "bot_id": bot.id,
            "name": bot.name,
            "token_pair": bot.token_pair,
            "buy_price_threshold": bot.buy_price_threshold,
            "buy_percentage_drop": bot.buy_percentage_drop,
            "sell_price_threshold": bot.sell_price_threshold,
            "sell_percentage_gain": bot.sell_percentage_gain,
            # NOUVEAUX CHAMPS POUR LES MONTANTS
            "buy_amount": bot.buy_amount if hasattr(bot, 'buy_amount') else 0.1,
            "sell_amount": bot.sell_amount if hasattr(bot, 'sell_amount') else 0.1,
            "min_swap_amount": bot.min_swap_amount if hasattr(bot, 'min_swap_amount') else 0.01,
            "random_trades_count": bot.random_trades_count,
            "trading_duration_hours": bot.trading_duration_hours,
            "last_buy_price": bot.last_buy_price,
            "last_sell_price": bot.last_sell_price,
            "api_endpoint": "http://localhost:8000"
        }
        
        config_file = os.path.join(self.bot_configs_dir, f"bot_{bot.id}_config.json")
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Config créée: {config_file}")
        logger.info(f"Montants configurés - Achat: {config['buy_amount']}, Vente: {config['sell_amount']}, Min: {config['min_swap_amount']}")
        return config_file
    
    def get_bot_status(self, bot_id: int) -> str:
        """Retourne le statut d'un bot"""
        if bot_id not in self.running_bots:
            return "stopped"
        
        process = self.running_bots[bot_id]
        if process.poll() is None:
            return "running"
        else:
            del self.running_bots[bot_id]
            if bot_id in self.bot_info:
                del self.bot_info[bot_id]
            return "stopped"
    
    def stop_all_bots(self):
        """Arrête tous les bots en cours d'exécution"""
        for bot_id in list(self.running_bots.keys()):
            try:
                asyncio.run(self.stop_bot(bot_id))
            except Exception as e:
                logger.error(f"Erreur lors de l'arrêt du bot {bot_id}: {str(e)}")

# Instance globale
bot_manager = BotManager()

# Gestionnaire pour arrêter tous les bots à la fermeture
def signal_handler(signum, frame):
    logger.info("Arrêt de tous les bots...")
    bot_manager.stop_all_bots()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)