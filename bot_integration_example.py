#!/usr/bin/env python3
"""
Exemple d'intégration de votre bot WPOL/KNO avec le Dashboard
Adaptez ce code à votre script existant
"""

import time
import logging
from datetime import datetime
from web3 import Web3
from remote_bot_client import DashboardClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonBotWPOLAvecDashboard:
    def __init__(self):
        # ========== CONNEXION DASHBOARD ==========
        self.dashboard = DashboardClient(
            api_url="http://192.168.1.100:8000",  # ⚠️ CHANGEZ par l'IP de votre PC Dashboard
            bot_token="bot_bot-1_xxxxx",          # ⚠️ CHANGEZ par votre token depuis Dashboard
            bot_id="bot-1"                        # ⚠️ CHANGEZ par l'ID de votre bot
        )
        
        # ========== VOS VARIABLES EXISTANTES ==========
        self.balance = 10000.0
        self.total_profit = 0.0
        self.last_buy_price = None
        self.last_sell_price = None
        
        # Configuration par défaut (sera mise à jour depuis Dashboard)
        self.buy_threshold = 0.007
        self.sell_threshold = 0.009
        self.buy_percentage_drop = 10
        self.sell_percentage_gain = 10
        self.random_trades_count = 20
        self.trading_duration_hours = 24
        
        # Variables Web3 (seront mises à jour depuis Dashboard)
        self.web3 = None
        self.account = None
        self.wpol_contract = None
        self.kno_contract = None
        self.router_contract = None
        self.quoter_contract = None
        
        logger.info("🤖 Bot WPOL/KNO initialisé")
    
    def setup_web3_from_dashboard(self):
        """Configure Web3 avec les paramètres du Dashboard"""
        try:
            # Récupérer la configuration wallet depuis le Dashboard
            wallet_config = self.dashboard.get_wallet_config()
            if not wallet_config:
                logger.error("❌ Impossible de récupérer la config wallet")
                return False
            
            # Initialiser Web3
            self.web3 = Web3(Web3.HTTPProvider(wallet_config['rpc_endpoint']))
            if not self.web3.is_connected():
                logger.error("❌ Impossible de se connecter au RPC")
                return False
            
            # Configurer le compte
            self.account = self.web3.eth.account.from_key(wallet_config['wallet_private_key'])
            logger.info(f"✅ Wallet configuré : {self.account.address}")
            
            # Configurer les contrats (vous devez avoir les ABI)
            if wallet_config['wpol_address']:
                self.wpol_contract = self.web3.eth.contract(
                    address=wallet_config['wpol_address'],
                    abi=self.get_erc20_abi()  # Votre fonction pour récupérer l'ABI
                )
                logger.info(f"✅ Contrat WPOL : {wallet_config['wpol_address']}")
            
            if wallet_config['kno_address']:
                self.kno_contract = self.web3.eth.contract(
                    address=wallet_config['kno_address'],
                    abi=self.get_erc20_abi()
                )
                logger.info(f"✅ Contrat KNO : {wallet_config['kno_address']}")
            
            if wallet_config['router_address']:
                self.router_contract = self.web3.eth.contract(
                    address=wallet_config['router_address'],
                    abi=self.get_router_abi()  # Votre fonction pour récupérer l'ABI
                )
                logger.info(f"✅ Router : {wallet_config['router_address']}")
            
            if wallet_config['quoter_address']:
                self.quoter_contract = self.web3.eth.contract(
                    address=wallet_config['quoter_address'],
                    abi=self.get_quoter_abi()  # Votre fonction pour récupérer l'ABI
                )
                logger.info(f"✅ Quoter : {wallet_config['quoter_address']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration Web3 : {str(e)}")
            return False
    
    def update_config_from_dashboard(self):
        """Met à jour la configuration depuis le Dashboard"""
        try:
            config = self.dashboard.get_bot_config()
            if config:
                self.buy_threshold = config.get('buy_price_threshold', self.buy_threshold)
                self.sell_threshold = config.get('sell_price_threshold', self.sell_threshold)
                self.buy_percentage_drop = config.get('buy_percentage_drop', self.buy_percentage_drop)
                self.sell_percentage_gain = config.get('sell_percentage_gain', self.sell_percentage_gain)
                self.random_trades_count = config.get('random_trades_count', self.random_trades_count)
                self.trading_duration_hours = config.get('trading_duration_hours', self.trading_duration_hours)
                
                logger.info("🔄 Configuration mise à jour depuis Dashboard")
                return True
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour config : {str(e)}")
        return False
    
    def start(self):
        """Démarre le bot avec connexion Dashboard"""
        logger.info("🚀 Démarrage du bot WPOL/KNO")
        
        # 1. Se connecter au Dashboard
        if not self.dashboard.connect():
            logger.error("❌ Impossible de se connecter au Dashboard")
            return
        
        # 2. Configurer Web3 avec les paramètres Dashboard
        if not self.setup_web3_from_dashboard():
            logger.error("❌ Impossible de configurer Web3")
            return
        
        # 3. Lancer la boucle de trading
        try:
            self.run_trading_loop()
        finally:
            # Déconnexion propre
            self.dashboard.disconnect()
    
    def run_trading_loop(self):
        """Votre boucle de trading principale"""
        last_config_check = 0
        config_check_interval = 60  # Vérifier la config toutes les 60 secondes
        trades_executed = 0
        
        logger.info("🔄 Démarrage de la boucle de trading")
        
        while trades_executed < self.random_trades_count:
            try:
                current_time = time.time()
                
                # Vérifier la config périodiquement
                if current_time - last_config_check > config_check_interval:
                    self.update_config_from_dashboard()
                    last_config_check = current_time
                
                # ========== VOTRE LOGIQUE DE PRIX ==========
                current_price = self.get_wpol_kno_price()  # Votre fonction existante
                if current_price is None:
                    logger.warning("⚠️ Impossible de récupérer le prix")
                    time.sleep(30)
                    continue
                
                logger.info(f"💰 Prix actuel WPOL/KNO : {current_price:.6f}€")
                
                # ========== CONDITIONS D'ACHAT ==========
                if self.should_buy(current_price):
                    amount = 1000  # Votre logique de quantité
                    success = self.execute_buy_wpol(current_price, amount)
                    
                    if success:
                        # Envoyer au Dashboard
                        self.dashboard.send_transaction("buy", amount, current_price)
                        self.last_buy_price = current_price
                        self.dashboard.update_bot_metrics(
                            balance=self.balance,
                            last_buy_price=current_price
                        )
                        trades_executed += 1
                        logger.info(f"✅ Achat exécuté : {amount} WPOL à {current_price:.6f}€")
                
                # ========== CONDITIONS DE VENTE ==========
                elif self.should_sell(current_price):
                    amount = 500  # Votre logique de quantité
                    success = self.execute_sell_wpol(current_price, amount)
                    
                    if success:
                        # Calculer le profit
                        profit = self.calculate_profit(amount, current_price)
                        self.total_profit += profit
                        
                        # Envoyer au Dashboard
                        self.dashboard.send_transaction("sell", amount, current_price, profit)
                        self.last_sell_price = current_price
                        self.dashboard.update_bot_metrics(
                            balance=self.balance,
                            total_profit=self.total_profit,
                            last_sell_price=current_price
                        )
                        trades_executed += 1
                        logger.info(f"✅ Vente exécutée : {amount} WPOL à {current_price:.6f}€ (Profit: {profit:.2f}€)")
                
                # Calculer l'intervalle aléatoire
                interval = (self.trading_duration_hours * 3600) / self.random_trades_count
                import random
                sleep_time = interval * random.uniform(0.7, 1.3)
                
                logger.info(f"⏳ Attente {sleep_time/60:.1f} minutes... ({trades_executed}/{self.random_trades_count} trades)")
                time.sleep(min(sleep_time, 300))  # Max 5 minutes entre vérifications
                
            except KeyboardInterrupt:
                logger.info("🛑 Arrêt demandé")
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle : {str(e)}")
                self.dashboard.update_bot_status("error")
                time.sleep(30)
        
        logger.info(f"🏁 Trading terminé : {trades_executed} trades exécutés")
    
    # ========== VOS FONCTIONS EXISTANTES ==========
    # Gardez toutes vos fonctions existantes et adaptez-les si nécessaire
    
    def get_wpol_kno_price(self) -> float:
        """Votre fonction pour récupérer le prix WPOL/KNO"""
        try:
            # Utilisez votre logique existante avec self.quoter_contract
            # Exemple avec quoter :
            if self.quoter_contract:
                # Votre logique de récupération de prix
                pass
            
            # Pour l'exemple, retournons un prix simulé
            import random
            base_price = 0.008
            variation = random.uniform(-0.001, 0.001)
            return base_price + variation
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération prix : {str(e)}")
            return None
    
    def should_buy(self, price: float) -> bool:
        """Votre logique d'achat"""
        # Condition 1: Prix < seuil d'achat
        if price < self.buy_threshold:
            logger.info(f"🟢 Condition achat : Prix {price:.6f} < seuil {self.buy_threshold:.6f}")
            return True
        
        # Condition 2: Baisse de X% depuis le dernier achat
        if self.last_buy_price:
            drop_threshold = self.last_buy_price * (1 - self.buy_percentage_drop / 100)
            if price <= drop_threshold:
                logger.info(f"🟢 Condition achat : Baisse {self.buy_percentage_drop}% depuis dernier achat")
                return True
        
        return False
    
    def should_sell(self, price: float) -> bool:
        """Votre logique de vente"""
        # Condition 1: Prix > seuil de vente
        if price > self.sell_threshold:
            logger.info(f"🟢 Condition vente : Prix {price:.6f} > seuil {self.sell_threshold:.6f}")
            return True
        
        # Condition 2: Hausse de X% depuis la dernière vente
        if self.last_sell_price:
            gain_threshold = self.last_sell_price * (1 + self.sell_percentage_gain / 100)
            if price >= gain_threshold:
                logger.info(f"🟢 Condition vente : Hausse {self.sell_percentage_gain}% depuis dernière vente")
                return True
        
        return False
    
    def execute_buy_wpol(self, price: float, amount: float) -> bool:
        """Votre fonction d'achat WPOL"""
        try:
            # ========== VOTRE LOGIQUE D'ACHAT EXISTANTE ==========
            # Utilisez self.router_contract, self.web3, self.account, etc.
            
            logger.info(f"💰 Exécution achat : {amount} WPOL à {price:.6f}€")
            
            # Exemple de transaction (adaptez à votre logique) :
            # tx = self.router_contract.functions.swapExactETHForTokens(
            #     0,  # amountOutMin
            #     [WETH_ADDRESS, self.wpol_contract.address],
            #     self.account.address,
            #     int(time.time()) + 300  # deadline
            # ).build_transaction({
            #     'from': self.account.address,
            #     'value': self.web3.to_wei(amount * price, 'ether'),
            #     'gas': 300000,
            #     'gasPrice': self.web3.to_wei('30', 'gwei'),
            #     'nonce': self.web3.eth.get_transaction_count(self.account.address)
            # })
            # 
            # signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
            # tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            # receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Pour l'exemple, simulons un succès
            self.balance -= amount * price  # Déduire le coût
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur achat : {str(e)}")
            return False
    
    def execute_sell_wpol(self, price: float, amount: float) -> bool:
        """Votre fonction de vente WPOL"""
        try:
            # ========== VOTRE LOGIQUE DE VENTE EXISTANTE ==========
            
            logger.info(f"💸 Exécution vente : {amount} WPOL à {price:.6f}€")
            
            # Votre logique de vente avec self.router_contract
            
            # Pour l'exemple, simulons un succès
            self.balance += amount * price  # Ajouter le gain
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vente : {str(e)}")
            return False
    
    def calculate_profit(self, amount: float, sell_price: float) -> float:
        """Calcule le profit d'une vente"""
        if self.last_buy_price:
            return (sell_price - self.last_buy_price) * amount
        return 0.0
    
    # ========== ABI FUNCTIONS (vos fonctions existantes) ==========
    def get_erc20_abi(self):
        """Retourne l'ABI ERC20 (votre fonction existante)"""
        return []  # Votre ABI ERC20
    
    def get_router_abi(self):
        """Retourne l'ABI du Router (votre fonction existante)"""
        return []  # Votre ABI Router
    
    def get_quoter_abi(self):
        """Retourne l'ABI du Quoter (votre fonction existante)"""
        return []  # Votre ABI Quoter

# ========== LANCEMENT ==========
if __name__ == "__main__":
    bot = MonBotWPOLAvecDashboard()
    bot.start()