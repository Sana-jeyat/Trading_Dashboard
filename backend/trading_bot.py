"""Bot de trading automatique pour le token KNO sur le réseau Polygon.
Connecté au dashboard FastAPI en local.
"""

from web3 import Web3
import json, time, os, sys, random
from dotenv import load_dotenv
from datetime import datetime, timezone
import requests
import logging
import asyncio
import sys


# Configuration logging pour le dashboard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- CONFIGURATION DE BASE ---
load_dotenv()
BOT_ID = int(os.getenv("BOT_ID", "1"))  # ID du bot dans le dashboard
API_URL = os.getenv("API_URL", "http://localhost:8000")  # FastAPI local

# Initialisation Web3 (sans wallet pour l'instant)
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
if not w3.is_connected():
    print(">>> Erreur de connexion à Polygon")
    sys.exit(1)

# --- ADRESSES FIXES (NE CHANGENT PAS) ---
WPOL = w3.to_checksum_address("0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270")
KNO  = w3.to_checksum_address("0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631")
ROUTER = w3.to_checksum_address("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")  # Quickswap

# --- ABIs (gardez les mêmes) ---
erc20_abi = json.loads("""[
    {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},
    {"constant":false,"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},
    {"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}
]""")
router_abi = json.loads("""[
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable"
    },
    {
        "name": "getAmountsOut",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "outputs": [
            {"name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "view"
    }
]""")

# --- CONTRATS ---
token_wpol = w3.eth.contract(address=WPOL, abi=erc20_abi)
token_kno = w3.eth.contract(address=KNO, abi=erc20_abi)
router = w3.eth.contract(address=ROUTER, abi=router_abi)

# --- CONSTANTES ---
GECKO_TERMINAL_POOL_URL = "https://api.geckoterminal.com/api/v2/networks/polygon_pos/pools/0xdce471c5fc17879175966bea3c9fe0432f9b189e"
PRICE_FILE = "last_price.txt"
SELL_PRICE_FILE = "last_sell_price.txt"

class KNOTradingBot:
    def __init__(self, bot_id: int, api_url: str):
        self.bot_id = bot_id
        self.api_url = api_url
        self.config = {}
        self.wallet_address = None
        self.private_key = None
        self.is_running = False
        self.logger = logging.getLogger(f"kno_bot_{bot_id}")
        
    async def load_config(self):
        """Charge la configuration depuis le dashboard"""
        try:
            response = requests.get(f"{self.api_url}/bots/{self.bot_id}")
            if response.status_code == 200:
                bot_data = response.json()
                
                # Configuration de base AVEC MONTANTS VARIABLES
                self.config = {
                    "buy_price_threshold": bot_data.get("buy_price_threshold", 0.001),
                    "sell_price_threshold": bot_data.get("sell_price_threshold", 0.0016),
                    # MONTANTS VARIABLES depuis le dashboard
                    "buy_amount": bot_data.get("buy_amount", 0.05),        # Montant d'achat configurable
                    "sell_amount": bot_data.get("sell_amount", 0.05),      # Montant de vente configurable
                    "min_swap_amount": bot_data.get("min_swap_amount", 0.01),  # Minimum configurable
                    "slippage": bot_data.get("slippage", 1),
                    "gas_limit": bot_data.get("gas_limit", 500000),
                    "gas_price": bot_data.get("gas_price", 40)
                }
                
                # Wallet configuration (depuis le dashboard)
                self.wallet_address = bot_data.get("wallet_address")
                # Pour la private key, on utilise l'endpoint sécurisé
                if self.wallet_address:
                    wallet_config = await self.get_wallet_config()
                    if wallet_config:
                        self.private_key = wallet_config.get("wallet_private_key")
                
                self.logger.info(f"Configuration chargée - {bot_data.get('name', 'Unknown')}")
                self.logger.info(f"Wallet: {self.wallet_address}")
                self.logger.info(f"Seuils - Achat: {self.config['buy_price_threshold']}, Vente: {self.config['sell_price_threshold']}")
                self.logger.info(f"Montants - Achat: {self.config['buy_amount']}, Vente: {self.config['sell_amount']}, Min: {self.config['min_swap_amount']}")
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erreur chargement config: {e}")
            return False
    
    async def get_wallet_config(self):
        """Récupère la configuration wallet sécurisée"""
        try:
            response = requests.get(f"{self.api_url}/bots/{self.bot_id}/wallet-config")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Erreur récupération wallet: {e}")
        return None
    
    # --- OUTILS WEB3 ---
    def to_wei(self, amount, decimals):
        return int(float(amount) * 10**decimals)

    def from_wei(self, amount, decimals):
        return float(amount) / 10**decimals

    def get_nonce(self):
        if not self.wallet_address:
            raise Exception("Wallet non configuré")
        
        # ⚠️ TRÈS IMPORTANT : Ajouter 'pending' pour voir les transactions en attente
        return w3.eth.get_transaction_count(self.wallet_address, 'pending')

    def approve_token(self, token_contract, spender, amount, token_name="Token"):
        if not self.wallet_address or not self.private_key:
            self.logger.error("Wallet non configuré pour l'approval")
            return False
            
        current_allowance = token_contract.functions.allowance(self.wallet_address, spender).call()
        if current_allowance >= amount:
            return True
            
        tx = token_contract.functions.approve(spender, amount).build_transaction({
            "from": self.wallet_address,
            "nonce": self.get_nonce(),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price
        })
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return True

    def cancel_pending_transactions(self):
        """Annule les transactions en attente"""
        try:
            if not self.wallet_address or not self.private_key:
                self.logger.warning("Wallet non configuré - annulation impossible")
                return False
                
            current_nonce = w3.eth.get_transaction_count(self.wallet_address, 'pending')
            latest_nonce = w3.eth.get_transaction_count(self.wallet_address, 'latest')
            
            if current_nonce > latest_nonce:
                pending_txs = current_nonce - latest_nonce
                self.logger.info(f"{pending_txs} transaction(s) en attente détectée(s)")
                
                cancel_tx = {
                    'to': self.wallet_address,
                    'value': 0,
                    'gas': 21000,
                    'gasPrice': w3.to_wei(200, 'gwei'),
                    'nonce': latest_nonce,
                    'chainId': 137
                }
                
                signed = w3.eth.account.sign_transaction(cancel_tx, self.private_key)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                self.logger.info(f"Transaction d'annulation envoyée: {w3.to_hex(tx_hash)}")
                
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                if receipt.status == 1:
                    self.logger.info("Transactions en attente annulées avec succès!")
                    return True
            else:
                self.logger.info("Aucune transaction en attente")
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation: {e}")
            return False

    # --- PRICE MANAGEMENT ---
    def read_price(self, file):
        try:
            with open(file, "r") as f:
                return float(f.read())
        except:
            return None

    def write_price(self, file, price):
        with open(file, "w") as f:
            f.write(str(float(price)))

    def get_price_kno_eur(self):
        try:
            response = requests.get(GECKO_TERMINAL_POOL_URL)
            response.raise_for_status()
            data = response.json()
            price_usd = float(data["data"]["attributes"]["base_token_price_usd"])
            return price_usd * 0.87
        except Exception as e:
            self.logger.error(f"Erreur récupération prix: {e}")
            return None

    # --- WRAP/UNWRAP ---
    def wrap_pol(self, amount_pol):
        if not self.wallet_address or not self.private_key:
            self.logger.error("Wallet non configuré pour wrap")
            return False
            
        tx = token_wpol.functions.deposit().build_transaction({
            "from": self.wallet_address,
            "value": w3.to_wei(amount_pol, "ether"),
            "nonce": self.get_nonce(),
            "gas": 150000,
            "gasPrice": w3.eth.gas_price
        })
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.status == 1

    def unwrap_wpol(self, amount_wei):
        if not self.wallet_address or not self.private_key:
            self.logger.error("Wallet non configuré pour unwrap")
            return False
            
        tx = token_wpol.functions.withdraw(amount_wei).build_transaction({
            "from": self.wallet_address,
            "nonce": self.get_nonce(),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price
        })
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.status == 1

    # --- TRADING AVEC MONTANTS VARIABLES ---
    def buy_kno(self, current_price):
        """Exécute un achat avec le montant configuré dans le dashboard"""
        try:
            if not self.wallet_address or not self.private_key:
                self.logger.error("Wallet non configuré pour l'achat")
                return False

            self.logger.info("Préparation de l'achat KNO...")

            # Récupérer le montant d'achat CONFIGURABLE
            buy_amount = self.config["buy_amount"]
            min_swap_amount = self.config["min_swap_amount"]
            
            # Vérifier le montant minimum
            if buy_amount < min_swap_amount:
                self.logger.warning(f"Montant d'achat {buy_amount} inférieur au minimum {min_swap_amount}")
                return False

            # Balance WPOL
            balance_wpol = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)
            
            # Vérifier si assez de WPOL, sinon wrap automatiquement
            if balance_wpol < buy_amount:
                wrap_needed = max(buy_amount - balance_wpol, 0.1)  # Au moins 0.1 POL
                self.logger.info(f"Pas assez de WPOL, wrapping {wrap_needed} POL...")
                if not self.wrap_pol(wrap_needed):
                    return False
                balance_wpol = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)

            # Utiliser le montant configuré ou la balance disponible (le plus petit)
            amt_decimal = min(buy_amount, balance_wpol)
            amt_wei = self.to_wei(amt_decimal, 18)
            
            self.logger.info(f"Montant WPOL à swap: {amt_decimal:.6f} (configuré: {buy_amount})")

            if not self.approve_token(token_wpol, ROUTER, amt_wei, "WPOL"):
                return False

            amounts = router.functions.getAmountsOut(amt_wei, [WPOL, KNO]).call()
            min_out = int(amounts[-1] * (1 - self.config["slippage"]/100))
            deadline = int(time.time()) + 600

            tx = router.functions.swapExactTokensForTokens(
                amt_wei,
                min_out,
                [WPOL, KNO],
                self.wallet_address,
                deadline
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": self.get_nonce(),
                "gas": self.config["gas_limit"],
                "gasPrice": w3.to_wei(self.config["gas_price"], "gwei")
            })

            signed = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            self.logger.info(f"Swap envoyé: {w3.to_hex(tx_hash)}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            success = receipt.status == 1
            if success:
                self.logger.info(f"Achat réussi ! {amt_decimal} KNO achetés")
                self.report_trade("buy", amt_decimal, current_price)
            else:
                self.logger.error("Achat échoué - receipt.status=0")
            return success
        except Exception as e:
            self.logger.error(f"Erreur achat: {e}")
            return False

    def sell_kno(self, current_price):
        """Exécute une vente avec le montant configuré dans le dashboard"""
        try:
            if not self.wallet_address or not self.private_key:
                self.logger.error("Wallet non configuré pour la vente")
                return False

            self.logger.info("Début de la vente KNO...")

            # Récupérer le montant de vente CONFIGURABLE
            sell_amount = self.config["sell_amount"]
            min_swap_amount = self.config["min_swap_amount"]
            
            # Vérifier le montant minimum
            if sell_amount < min_swap_amount:
                self.logger.warning(f"Montant de vente {sell_amount} inférieur au minimum {min_swap_amount}")
                return False

            old_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()
            balance_kno = token_kno.functions.balanceOf(self.wallet_address).call()
            balance_kno_decimal = self.from_wei(balance_kno, 18)

            self.logger.info(f"Balance KNO: {balance_kno_decimal:.6f}")
            if balance_kno_decimal < min_swap_amount:
                self.logger.warning("Balance KNO insuffisante pour vendre")
                return False

            # Utiliser le montant configuré ou la balance disponible (le plus petit)
            amt_decimal = min(sell_amount, balance_kno_decimal)
            amt_wei = self.to_wei(amt_decimal, 18)

            self.logger.info(f"Montant KNO à vendre: {amt_decimal:.6f} (configuré: {sell_amount})")

            if not self.approve_token(token_kno, ROUTER, amt_wei, "KNO"):
                return False

            amounts = router.functions.getAmountsOut(amt_wei, [KNO, WPOL]).call()
            min_out = int(amounts[-1] * (1 - self.config["slippage"]/100))
            deadline = int(time.time()) + 600

            tx = router.functions.swapExactTokensForTokens(
                amt_wei,
                min_out,
                [KNO, WPOL],
                self.wallet_address,
                deadline
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": self.get_nonce(),
                "gas": self.config["gas_limit"],
                "gasPrice": w3.to_wei(self.config["gas_price"], "gwei")
            })

            signed = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            self.logger.info(f"Swap KNO → WPOL envoyé: {w3.to_hex(tx_hash)}")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            success = receipt.status == 1

            if success:
                self.logger.info(f"Vente réussie ! {amt_decimal} KNO vendus")
                new_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()
                gained_wpol = new_balance_wpol - old_balance_wpol
                self.logger.info(f"WPOL reçus: {self.from_wei(gained_wpol,18):.6f}")
                self.unwrap_wpol(gained_wpol)
                self.write_price(SELL_PRICE_FILE, current_price)
                self.report_trade("sell", amt_decimal, current_price)
            return success
        except Exception as e:
            self.logger.error(f"Erreur lors de la vente KNO: {e}")
            return False

    # --- DASHBOARD COMMUNICATION ---
    def report_trade(self, action, amount, price, profit=None):
        try:
            data = {
                "bot_id": self.bot_id,
                "type": action,
                "amount": amount,
                "price": price,
                "profit": profit,
                "tx_hash": f"real_{int(time.time())}"
            }

            self.logger.info(f"Envoi transaction: {action} {amount} KNO à {price}€")
            response = requests.post(f"{self.api_url}/transactions", json=data)
            
            if response.status_code in [200, 201]:
                self.logger.info("Transaction enregistrée dans le dashboard")
                return True
            else:
                self.logger.error(f"Erreur API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Impossible d'envoyer la transaction: {e}")
            return False

    def update_status(self, status):
        try:
            requests.put(f"{self.api_url}/bots/{self.bot_id}/status", json={"status": status})
        except Exception as e:
            self.logger.error(f"Erreur mise à jour statut: {e}")

    def send_heartbeat(self):
        try:
            requests.get(f"{self.api_url}/bots/{self.bot_id}/heartbeat")
        except:
            pass

    # --- MAIN LOOP ---
    async def start(self):
        """Démarre le bot de trading"""
        self.is_running = True
        
        if not await self.load_config():
            self.logger.error("Impossible de charger la configuration")
            return

        if not self.wallet_address or not self.private_key:
            self.logger.error("Configuration wallet manquante - vérifiez le dashboard")
            return

        self.update_status("online")
        self.logger.info("Bot trading KNO démarré")

        # Annulation des transactions en attente
        self.logger.info("Vérification des transactions en attente...")
        self.cancel_pending_transactions()

        trade_count = 0
        try:
            while self.is_running:
                # Recharger la configuration (pour avoir les derniers montants)
                await self.load_config()
                
                price = self.get_price_kno_eur()
                if not price:
                    await asyncio.sleep(60)
                    continue
                    
                last_price = self.read_price(PRICE_FILE)
                last_sell  = self.read_price(SELL_PRICE_FILE)

                # Conditions de trading
                buy_condition = price <= self.config["buy_price_threshold"] or (last_price and price <= last_price * 0.9)
                if buy_condition:
                    if self.buy_kno(price):
                        trade_count += 1

                sell_condition = price >= self.config["sell_price_threshold"] or (last_sell and price >= last_sell * 1.1)
                if sell_condition:
                    if self.sell_kno(price):
                        trade_count += 1

                self.write_price(PRICE_FILE, price)
                self.send_heartbeat()
                
                delay = random.randint(2, 5)
                self.logger.info(f"Prochain cycle dans {delay} minutes...")
                await asyncio.sleep(delay * 60)
                
        except KeyboardInterrupt:
            self.logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"Erreur boucle principale: {e}")
        finally:
            self.update_status("offline")
            self.logger.info("Bot KNO arrêté")

    def stop(self):
        """Arrête le bot"""
        self.is_running = False
        self.logger.info("Arrêt du bot demandé")

async def main():
    bot_id = int(os.getenv('BOT_ID', 1))
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    bot = KNOTradingBot(bot_id, api_url)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        logging.error(f"Erreur critique: {e}")

if __name__ == "__main__":
    asyncio.run(main())