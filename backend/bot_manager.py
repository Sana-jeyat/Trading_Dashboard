"""Gestionnaire de processus pour les bots de trading
Gestion locale uniquement

Quand tu fais "start_bot", il lance un script Python (your_trading_script.py) via "subprocess.Popen".

Il garde une référence du process dans "self.running_bots" → dictionnaire "{bot_id: process}".
"stop_bot" envoie SIGTERM pour arrêter le process.

"get_bot_status" regarde si le process est encore actif.

Les configs de chaque bot sont sauvegardées en JSON dans bot_configs/.

Limite actuelle
👉 Cela ne fonctionne que si le bot est sur la même machine que le dashboard.
Impossible d’aller démarrer/arrêter un bot qui est sur un autre PC."""

import asyncio
import subprocess
import signal
import os
from typing import Dict, Optional
from models import Bot
from database import SessionLocal
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.running_bots: Dict[int, subprocess.Popen] = {}
        self.bot_configs_dir = "bot_configs"
        
        # Créer le dossier des configurations si il n'existe pas
        os.makedirs(self.bot_configs_dir, exist_ok=True)
    
    async def start_bot(self, bot: Bot):
        """Démarre un bot de trading"""
        if bot.id in self.running_bots:
            raise Exception("Le bot est déjà en cours d'exécution")
        
        # Créer le fichier de configuration pour le bot
        config_file = self._create_bot_config(bot)
        
        # Commande pour lancer votre script Python de trading
        # Adaptez cette commande selon votre script
        command = [
            "python", 
            "your_trading_script.py",  # Remplacez par le nom de votre script
            "--config", config_file,
            "--bot-id", str(bot.id)
        ]
        
        try:
            # Lancer le processus
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=".",  # Répertoire de vos scripts de trading
            )
            
            self.running_bots[bot.id] = process
            logger.info(f"Bot {bot.id} ({bot.name}) démarré avec PID {process.pid}")
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot {bot.id}: {str(e)}")
            raise
    
    async def stop_bot(self, bot_id: int):
        """Arrête un bot de trading"""
        if bot_id not in self.running_bots:
            raise Exception("Le bot n'est pas en cours d'exécution")
        
        process = self.running_bots[bot_id]
        
        try:
            # Envoyer SIGTERM pour arrêt propre
            process.terminate()
            
            # Attendre 10 secondes pour l'arrêt propre
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Forcer l'arrêt si nécessaire
                process.kill()
                process.wait()
            
            del self.running_bots[bot_id]
            logger.info(f"Bot {bot_id} arrêté")
            
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
            "last_buy_price": bot.last_buy_price,
            "last_sell_price": bot.last_sell_price,
            "api_endpoint": "http://localhost:8000"  # Pour que le bot puisse communiquer avec l'API
        }
        
        config_file = os.path.join(self.bot_configs_dir, f"bot_{bot.id}_config.json")
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_file
    
    def get_bot_status(self, bot_id: int) -> str:
        """Retourne le statut d'un bot"""
        if bot_id not in self.running_bots:
            return "stopped"
        
        process = self.running_bots[bot_id]
        if process.poll() is None:
            return "running"
        else:
            # Le processus s'est arrêté
            del self.running_bots[bot_id]
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