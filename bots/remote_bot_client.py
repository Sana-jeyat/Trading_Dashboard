#!/usr/bin/env python3
"""
Client Python pour connecter votre bot de trading au Dashboard
À utiliser sur votre PC distant où tourne votre script de trading
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardClient:
    def __init__(self, api_url: str, bot_token: str, bot_id: str):
        """
        Client pour connecter votre bot au Dashboard
        
        Args:
            api_url: URL de votre Dashboard API (ex: http://192.168.1.100:8000)
            bot_token: Token d'authentification du bot
            bot_id: ID de votre bot dans le Dashboard
        """
        self.api_url = api_url.rstrip('/')
        self.bot_token = bot_token
        self.bot_id = bot_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        })
        self.is_connected = False
        self._heartbeat_thread = None
        self._stop_heartbeat = False
        
        logger.info(f"Client initialisé pour bot {bot_id}")
    
    def connect(self) -> bool:
        """Établit la connexion avec le Dashboard"""
        try:
            # Test de connexion
            response = self.session.get(f"{self.api_url}/bots/{self.bot_id}")
            if response.status_code == 200:
                self.is_connected = True
                logger.info("✅ Connexion établie avec le Dashboard")
                
                # Marquer le bot comme en ligne
                self.update_bot_status("online")
                
                # Démarrer le heartbeat
                self._start_heartbeat()
                return True
            else:
                logger.error(f"❌ Erreur de connexion: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter: {str(e)}")
            return False
    
    def disconnect(self):
        """Ferme la connexion proprement"""
        self._stop_heartbeat = True
        if self._heartbeat_thread:
            self._heartbeat_thread.join()
        
        if self.is_connected:
            self.update_bot_status("offline")
        
        self.is_connected = False
        logger.info("🔌 Déconnexion du Dashboard")
    
    def _start_heartbeat(self):
        """Démarre le heartbeat pour maintenir la connexion"""
        def heartbeat():
            while not self._stop_heartbeat and self.is_connected:
                try:
                    self.session.get(f"{self.api_url}/bots/{self.bot_id}/heartbeat")
                    time.sleep(30)  # Heartbeat toutes les 30 secondes
                except:
                    pass
        
        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self._heartbeat_thread.start()
    
    def send_transaction(self, transaction_type: str, amount: float, price: float, 
                        profit: Optional[float] = None, tx_hash: Optional[str] = None) -> bool:
        """
        Envoie une transaction au Dashboard
        
        Args:
            transaction_type: 'buy' ou 'sell'
            amount: Quantité tradée
            price: Prix en euros
            profit: Profit réalisé (pour les ventes)
            tx_hash: Hash de transaction blockchain (optionnel)
        """
        if not self.is_connected:
            logger.warning("⚠️ Pas de connexion au Dashboard")
            return False
        
        try:
            data = {
                "bot_id": self.bot_id,
                "type": transaction_type,
                "amount": amount,
                "price": price,
                "profit": profit,
                "tx_hash": tx_hash,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{self.api_url}/transactions", json=data)
            
            if response.status_code in [200, 201]:
                action = "Achat" if transaction_type == "buy" else "Vente"
                logger.info(f"📊 {action} envoyé: {amount} à {price}€")
                return True
            else:
                logger.error(f"❌ Erreur envoi transaction: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi: {str(e)}")
            return False
    
    def update_bot_metrics(self, balance: Optional[float] = None, 
                          total_profit: Optional[float] = None,
                          last_buy_price: Optional[float] = None,
                          last_sell_price: Optional[float] = None) -> bool:
        """Met à jour les métriques du bot"""
        if not self.is_connected:
            return False
        
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
                response = self.session.put(f"{self.api_url}/bots/{self.bot_id}", json=data)
                if response.status_code == 200:
                    logger.info("📈 Métriques mises à jour")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour métriques: {str(e)}")
            return False
    
    def update_bot_status(self, status: str) -> bool:
        """Met à jour le statut du bot (online/offline/error)"""
        try:
            data = {"status": status}
            response = self.session.put(f"{self.api_url}/bots/{self.bot_id}/status", json=data)
            return response.status_code == 200
        except:
            return False
    
    def get_bot_config(self) -> Optional[Dict[str, Any]]:
        """Récupère la configuration du bot depuis le Dashboard"""
        if not self.is_connected:
            return None
        
        try:
            response = self.session.get(f"{self.api_url}/bots/{self.bot_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"❌ Erreur récupération config: {str(e)}")
            return None

# Exemple d'utilisation dans votre script de trading
class MonBotDeTrading:
    def __init__(self):
        # Configuration de connexion au Dashboard
        self.dashboard = DashboardClient(
            api_url="http://192.168.1.100:8000",  # IP de votre PC avec le Dashboard
            bot_token="votre_token_ici",          # Token depuis le Dashboard
            bot_id="bot-1"                        # ID de votre bot
        )
        
        # Vos variables de trading
        self.balance = 10000.0
        self.total_profit = 0.0
        self.last_buy_price = None
        self.last_sell_price = None
    
    def start(self):
        """Démarre le bot avec connexion Dashboard"""
        logger.info("🚀 Démarrage du bot de trading")
        
        # Se connecter au Dashboard
        if not self.dashboard.connect():
            logger.error("❌ Impossible de se connecter au Dashboard")
            return
        
        try:
            # Votre logique de trading ici
            self.run_trading_loop()
        finally:
            # Déconnexion propre
            self.dashboard.disconnect()
    
    def run_trading_loop(self):
        """Votre boucle de trading principale"""
        last_config_check = 0
        config_check_interval = 60  # Vérifier la config toutes les 60 secondes
        
        while True:
            try:
                current_time = time.time()
                
                # Vérifier la config périodiquement
                if current_time - last_config_check > config_check_interval:
                    config = self.dashboard.get_bot_config()
                    if config:
                        # Mettre à jour les paramètres du bot
                        self.buy_threshold = config.get('buy_price_threshold', 0.007)
                        self.sell_threshold = config.get('sell_price_threshold', 0.009)
                        self.buy_percentage_drop = config.get('buy_percentage_drop', 10)
                        self.sell_percentage_gain = config.get('sell_percentage_gain', 10)
                        self.random_trades_count = config.get('random_trades_count', 20)
                        self.trading_duration_hours = config.get('trading_duration_hours', 24)
                        
                        logger.info("🔄 Configuration mise à jour depuis le Dashboard")
                        last_config_check = current_time
                
                # Votre logique de trading
                current_price = self.get_current_price()  # Votre fonction
                
                if self.should_buy(current_price, self.buy_threshold):
                    amount = 1000
                    success = self.execute_buy(current_price, amount)  # Votre fonction
                    
                    if success:
                        # Envoyer au Dashboard
                        self.dashboard.send_transaction("buy", amount, current_price)
                        self.last_buy_price = current_price
                        self.dashboard.update_bot_metrics(
                            balance=self.balance,
                            last_buy_price=current_price
                        )
                
                elif self.should_sell(current_price, self.sell_threshold):
                    amount = 500
                    success = self.execute_sell(current_price, amount)  # Votre fonction
                    
                    if success:
                        # Calculer le profit
                        profit = (current_price - self.last_buy_price) * amount if self.last_buy_price else 0
                        self.total_profit += profit
                        
                        # Envoyer au Dashboard
                        self.dashboard.send_transaction("sell", amount, current_price, profit)
                        self.last_sell_price = current_price
                        self.dashboard.update_bot_metrics(
                            balance=self.balance,
                            total_profit=self.total_profit,
                            last_sell_price=current_price
                        )
                
                time.sleep(60)  # Attendre 1 minute
                
            except KeyboardInterrupt:
                logger.info("🛑 Arrêt demandé")
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle: {str(e)}")
                self.dashboard.update_bot_status("error")
                time.sleep(30)
    
    def get_current_price(self) -> float:
        """Votre fonction pour récupérer le prix actuel"""
        # Remplacez par votre logique
        return 0.008
    
    def should_buy(self, price: float, threshold: float) -> bool:
        """Votre logique d'achat"""
        return price < threshold
    
    def should_sell(self, price: float, threshold: float) -> bool:
        """Votre logique de vente"""
        return price > threshold
    
    def execute_buy(self, price: float, amount: float) -> bool:
        """Votre fonction d'achat"""
        # Votre logique d'achat réelle
        logger.info(f"💰 Achat: {amount} à {price}€")
        return True
    
    def execute_sell(self, price: float, amount: float) -> bool:
        """Votre fonction de vente"""
        # Votre logique de vente réelle
        logger.info(f"💸 Vente: {amount} à {price}€")
        return True

if __name__ == "__main__":
    bot = MonBotDeTrading()
    bot.start()