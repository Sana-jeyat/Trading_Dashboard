#!/usr/bin/env python3
"""
Exemple d'intégration de votre script de trading avec l'API
Ce fichier montre comment adapter votre script existant pour communiquer avec le backend
"""

import json
import requests
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingBotClient:
    def __init__(self, config_file: str):
        self.config = self._load_config(config_file)
        self.api_base = self.config.get("api_endpoint", "http://localhost:8000")
        self.bot_id = self.config["bot_id"]
        self.running = True
        
        logger.info(f"Bot {self.bot_id} initialisé avec la config: {config_file}")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Charge la configuration du bot depuis le fichier JSON"""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def _send_transaction(self, transaction_type: str, amount: float, price: float, profit: float = None, tx_hash: str = None):
        """Envoie une transaction à l'API"""
        try:
            data = {
                "bot_id": self.bot_id,
                "type": transaction_type,
                "amount": amount,
                "price": price,
                "profit": profit,
                "tx_hash": tx_hash
            }
            
            response = requests.post(f"{self.api_base}/transactions", json=data)
            if response.status_code == 200:
                logger.info(f"Transaction {transaction_type} enregistrée: {amount} à {price}€")
            else:
                logger.error(f"Erreur lors de l'enregistrement de la transaction: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la transaction: {str(e)}")
    
    def _update_bot_metrics(self, balance: float = None, total_profit: float = None, 
                           last_buy_price: float = None, last_sell_price: float = None):
        """Met à jour les métriques du bot"""
        try:
            data = {}
            if balance is not None:
                data["balance"] = balance
            if total_profit is not None:
                data["total_profit"] = total_profit
            if last_buy_price is not None:
                data["last_buy_price"] = last_buy_price
            if last_sell_price is not None:
                data["last_sell_price"] = last_sell_price
            
            if data:
                response = requests.put(f"{self.api_base}/bots/{self.bot_id}", json=data)
                if response.status_code == 200:
                    logger.info("Métriques du bot mises à jour")
                else:
                    logger.error(f"Erreur lors de la mise à jour: {response.text}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des métriques: {str(e)}")
    
    def should_buy(self, current_price: float) -> bool:
        """Logique d'achat basée sur la configuration"""
        # Condition 1: Prix < seuil d'achat
        if current_price < self.config["buy_price_threshold"]:
            return True
        
        # Condition 2: Baisse de X% depuis le dernier achat
        last_buy = self.config.get("last_buy_price")
        if last_buy:
            drop_threshold = last_buy * (1 - self.config["buy_percentage_drop"] / 100)
            if current_price <= drop_threshold:
                return True
        
        return False
    
    def should_sell(self, current_price: float) -> bool:
        """Logique de vente basée sur la configuration"""
        # Condition 1: Prix > seuil de vente
        if current_price > self.config["sell_price_threshold"]:
            return True
        
        # Condition 2: Hausse de X% depuis la dernière vente
        last_sell = self.config.get("last_sell_price")
        if last_sell:
            gain_threshold = last_sell * (1 + self.config["sell_percentage_gain"] / 100)
            if current_price >= gain_threshold:
                return True
        
        return False
    
    def get_current_price(self) -> float:
        """
        Récupère le prix actuel du token
        Remplacez cette fonction par votre logique de récupération de prix
        (API exchange, Web3, etc.)
        """
        # EXEMPLE - Remplacez par votre logique
        # Pour WPOL/KNO, vous pourriez utiliser:
        # - API de votre exchange
        # - Appel Web3 à un contrat de pool
        # - API de prix comme CoinGecko
        
        # Simulation pour l'exemple
        import random
        base_price = 0.008
        variation = random.uniform(-0.001, 0.001)
        return base_price + variation
    
    def execute_buy(self, price: float, amount: float) -> str:
        """
        Exécute un ordre d'achat
        Remplacez par votre logique d'achat réelle
        """
        # VOTRE LOGIQUE D'ACHAT ICI
        # Exemple: appel à l'exchange, transaction Web3, etc.
        
        logger.info(f"Exécution achat: {amount} WPOL/KNO à {price}€")
        
        # Simulation d'un hash de transaction
        tx_hash = f"0x{''.join([f'{i:02x}' for i in range(32)])}"
        
        return tx_hash
    
    def execute_sell(self, price: float, amount: float) -> str:
        """
        Exécute un ordre de vente
        Remplacez par votre logique de vente réelle
        """
        # VOTRE LOGIQUE DE VENTE ICI
        
        logger.info(f"Exécution vente: {amount} WPOL/KNO à {price}€")
        
        # Simulation d'un hash de transaction
        tx_hash = f"0x{''.join([f'{i:02x}' for i in range(32)])}"
        
        return tx_hash
    
    def run(self):
        """Boucle principale du bot"""
        logger.info(f"Démarrage du bot {self.config['name']}")
        
        # Calculer l'intervalle entre les trades aléatoires
        total_trades = self.config.get("random_trades_count", 20)
        duration_hours = self.config.get("trading_duration_hours", 24)
        interval_seconds = (duration_hours * 3600) / total_trades
        
        logger.info(f"Configuration aléatoire: {total_trades} trades sur {duration_hours}h")
        logger.info(f"Intervalle moyen: {interval_seconds/60:.1f} minutes entre les trades")
        
        trades_executed = 0
        import random
        
        while self.running:
            try:
                # Récupérer le prix actuel
                current_price = self.get_current_price()
                logger.info(f"Prix actuel: {current_price}€")
                
                # Ajouter de l'aléa dans le timing (±30% de l'intervalle)
                random_interval = interval_seconds * random.uniform(0.7, 1.3)
                
                # Vérifier les conditions d'achat
                if trades_executed < total_trades and self.should_buy(current_price):
                    amount = 1000  # Quantité à acheter (à adapter selon votre logique)
                    tx_hash = self.execute_buy(current_price, amount)
                    
                    # Enregistrer la transaction
                    self._send_transaction("buy", amount, current_price, tx_hash=tx_hash)
                    
                    # Mettre à jour le dernier prix d'achat
                    self._update_bot_metrics(last_buy_price=current_price)
                    self.config["last_buy_price"] = current_price
                    trades_executed += 1
                
                # Vérifier les conditions de vente
                elif trades_executed < total_trades and self.should_sell(current_price):
                    amount = 500  # Quantité à vendre (à adapter selon votre logique)
                    tx_hash = self.execute_sell(current_price, amount)
                    
                    # Calculer le profit (simplifié)
                    last_buy = self.config.get("last_buy_price", current_price)
                    profit = (current_price - last_buy) * amount
                    
                    # Enregistrer la transaction
                    self._send_transaction("sell", amount, current_price, profit=profit, tx_hash=tx_hash)
                    
                    # Mettre à jour le dernier prix de vente
                    self._update_bot_metrics(last_sell_price=current_price)
                    self.config["last_sell_price"] = current_price
                    trades_executed += 1
                
                # Vérifier si tous les trades ont été exécutés
                if trades_executed >= total_trades:
                    logger.info(f"Tous les {total_trades} trades ont été exécutés. Arrêt du bot.")
                    self.running = False
                    break
                
                # Attendre avant la prochaine vérification
                time.sleep(min(random_interval, 300))  # Max 5 minutes entre vérifications
                
            except KeyboardInterrupt:
                logger.info("Arrêt du bot demandé")
                self.running = False
            except Exception as e:
                logger.error(f"Erreur dans la boucle principale: {str(e)}")
                time.sleep(60)  # Attendre 1 minute en cas d'erreur

def main():
    parser = argparse.ArgumentParser(description="Bot de trading automatique")
    parser.add_argument("--config", required=True, help="Fichier de configuration JSON")
    parser.add_argument("--bot-id", required=True, help="ID du bot")
    
    args = parser.parse_args()
    
    # Créer et lancer le bot
    bot = TradingBotClient(args.config)
    bot.run()

if __name__ == "__main__":
    main()