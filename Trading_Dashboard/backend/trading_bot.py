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
print("PYTHON USED BY BOT:", sys.executable)

# Configuration logging pour le dashboard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- CONFIGURATION DE BASE ---
load_dotenv()
bot_id = int(os.getenv("BOT_ID", "2"))  # ID du bot dans le dashboard
API_URL = os.getenv("API_URL", "http://mmk.knocoin.com/")  # FastAPI local

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
        "name": "swapExactTokensForTokensSupportingFeeOnTransferTokens", 
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
        self.reference_price = None
        self.logger = logging.getLogger(f"kno_bot_{bot_id}")
        

        
    async def load_config(self):
        """Charge la configuration depuis le dashboard"""
        try:
            response = requests.get(f"{self.api_url}/bots/{self.bot_id}/kno-config")
            if response.status_code == 200:
                bot_data = response.json()
                
                # Configuration KNO spécifique
                self.config = {
                    "volatility_percent": bot_data.get("volatility_percent", 50),
                    "buy_amount": bot_data.get("buy_amount", 0.05),
                    "sell_amount": bot_data.get("sell_amount", 0.05),
                    "min_swap_amount": bot_data.get("min_swap_amount", 0.01),
                    "reference_price": bot_data.get("reference_price"),
                    "slippage": bot_data.get("slippage_tolerance", 1),
                    "gas_limit": bot_data.get("gas_limit", 500000),
                    "gas_price": bot_data.get("gas_price", 40)
                }
                
                # Wallet
                self.wallet_address = bot_data.get("wallet_address")
                self.private_key = bot_data.get("wallet_private_key")
                
                # Adresses des contrats
                self.wpol_address = bot_data.get("wpol_address", "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270")
                self.kno_address = bot_data.get("kno_address", "0x236fbfAa3Ec9E0B9BA013Df370c098bAd85aD631")
                self.router_address = bot_data.get("router_address", "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")
                
                self.logger.info(f"Configuration KNO chargée - {bot_data.get('name', 'Unknown')}")
                self.logger.info(f"Volatilité: {self.config['volatility_percent']}%")
                self.logger.info(f"Achat: {self.config['buy_amount']} WPOL, Vente: {self.config['sell_amount']} KNO")
                
                return True
            else:
                self.logger.error(f"Erreur API: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Erreur chargement config KNO: {e}")
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
        self.logger.info(f"Allowance KNO: {current_allowance}")
        if current_allowance >= amount:
            return True
            
        tx = token_contract.functions.approve(spender, amount).build_transaction({
            "from": self.wallet_address,
            "nonce": self.get_nonce(),
            "gas": 200000,
            "gasPrice": self.get_dynamic_gas_price()
        })
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return True

    def cancel_pending_transactions(self):
        """Annule toutes les transactions en attente en les écrasant avec un gas élevé"""
        if not self.wallet_address or not self.private_key:
            self.logger.warning("Wallet non configuré - annulation impossible")
            return False

        try:
            latest_nonce = w3.eth.get_transaction_count(self.wallet_address, 'latest')
            pending_nonce = w3.eth.get_transaction_count(self.wallet_address, 'pending')

            if pending_nonce <= latest_nonce:
                self.logger.info("Aucune transaction en attente")
                return True

            self.logger.info(f"{pending_nonce - latest_nonce} transaction(s) en attente détectée(s)")

            for nonce in range(latest_nonce, pending_nonce):
                cancel_tx = {
                    'to': self.wallet_address,
                    'value': 0,
                    'gas': 21000,
                    'gasPrice': max(self.get_dynamic_gas_price(), w3.to_wei(200, 'gwei')),
                    'nonce': nonce,
                    'chainId': 137
                }

                signed = w3.eth.account.sign_transaction(cancel_tx, self.private_key)
                try:
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                    self.logger.info(f"Transaction d'annulation envoyée pour nonce {nonce}: {w3.to_hex(tx_hash)}")
                except Exception as e:
                    self.logger.warning(f"Impossible d'annuler la transaction nonce {nonce}: {e}")

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
        
    # --- GAS PRICE DYNAMIQUE SELON RÉSEAU ---
    def get_dynamic_gas_price(self):
        try:
            return w3.eth.gas_price  # en wei
        except:
            return w3.to_wei(self.config.get("gas_price", 40), "gwei")

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
            "gasPrice": self.get_dynamic_gas_price()
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
            "gasPrice": self.get_dynamic_gas_price()
        })
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.status == 1
    
    # --- SLIPPAGE DYNAMIQUE SELON VOLATILITÉ ---
    def get_dynamic_slippage(self, price, ref_price):
        """Retourne un slippage ajusté en % selon volatilité"""
        vol_percent = self.config.get("volatility_percent", 10)
        # Plus le prix s'éloigne de la référence, plus on tolère de slippage
        diff = abs(price - ref_price) / ref_price
        slippage = max(1, min(5, vol_percent * diff * 10))  # 1% min, 5% max
        return slippage

    
    # --- TRADING AVEC MONTANTS VARIABLES ---
    def buy_kno(self, current_price):
        # ref_price = self.config["reference_price"]
        ref_price = self.reference_price
        """Exécute un achat avec le montant configuré dans le dashboard"""

         # 1️⃣ Annulation des transactions pending
        if not self.cancel_pending_transactions():
            self.logger.warning("Impossible d'annuler les transactions en attente, attente 1 min...")
            time.sleep(60)  # ou return False

        try:
            if not self.wallet_address or not self.private_key:
                self.logger.error("Wallet non configuré pour l'achat")
                return False

            self.logger.info("Préparation de l'achat KNO...")

            # Récupérer le montant d'achat CONFIGURABLE
            buy_amount = self.config.get("buy_amount", 0.01)
            min_swap_amount = self.config.get("min_swap_amount", 0.01)

            # Vérifier le montant minimum
            if buy_amount < min_swap_amount:
                self.logger.warning(f"Montant d'achat {buy_amount} inférieur au minimum {min_swap_amount}")
                return False


            pol_balance = self.from_wei(w3.eth.get_balance(self.wallet_address), 18)
            gas_reserve = 0.05  # POL à garder pour les fees

            if pol_balance < gas_reserve:
                self.logger.warning(f"Pas assez de POL pour le gas ({pol_balance:.4f} POL)")
                return False
            # Balance WPOL
            balance_wpol = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)
            
            # Vérifier si assez de WPOL, sinon wrap automatiquement
            balance_wpol = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)
            if balance_wpol < buy_amount:
                wrap_needed = buy_amount - balance_wpol
                self.logger.info(f"Pas assez de WPOL, wrapping {wrap_needed:.4f} POL...")
                if not self.wrap_pol(wrap_needed):
                    self.logger.error("Wrap échoué")
                    return False
                balance_wpol = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)

            # Utiliser le montant configuré ou la balance disponible (le plus petit)
            amt_decimal = min(buy_amount, balance_wpol)
            amt_wei = self.to_wei(amt_decimal, 18)
            
            self.logger.info(f"Montant WPOL à swap: {amt_decimal:.6f} (configuré: {buy_amount})")

            if not self.approve_token(token_wpol, ROUTER, amt_wei, "WPOL"):
                return False


            # Balance KNO avant achat
            old_kno_balance = token_kno.functions.balanceOf(self.wallet_address).call()

            amounts = router.functions.getAmountsOut(amt_wei, [WPOL, KNO]).call()
            slippage = max(self.get_dynamic_slippage(current_price, ref_price),3)
            min_out = int(amounts[-1] * (1 - slippage / 100))
            deadline = int(time.time()) + 600

            # router.functions.swapExactTokensForTokens(
            tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                amt_wei,
                min_out,
                [WPOL, KNO],
                self.wallet_address,
                deadline
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": self.get_nonce(),
                "gas": self.config["gas_limit"],
                "gasPrice": self.get_dynamic_gas_price()
            })

            signed = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            self.logger.info(f"Swap envoyé: {w3.to_hex(tx_hash)}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            success = receipt.status == 1
            if success:
                # Balance KNO après achat
                new_kno_balance = token_kno.functions.balanceOf(self.wallet_address).call()

                received_wei = new_kno_balance - old_kno_balance
                received_kno = self.from_wei(received_wei, 18)

                self.logger.info(f"Achat réussi ! {received_kno:.6f} KNO reçus")
                self.report_trade("buy", received_kno, current_price)
            else:
                self.logger.error("Achat échoué - receipt.status=0")
            return success
        except Exception as e:
            self.logger.error(f"Erreur achat: {e}")
            return False

    def sell_kno(self, current_price):
        """Exécute une vente avec le montant configuré dans le dashboard"""
        ref_price = self.reference_price

        # Annulation des transactions pending
        if not self.cancel_pending_transactions():
            self.logger.warning("Impossible d'annuler les transactions en attente, attente 1 min...")
            time.sleep(60)

        try:
            if not self.wallet_address or not self.private_key:
                self.logger.error("Wallet non configuré pour la vente")
                return False

            self.logger.info("Début de la vente KNO...")

            # Montants configurables
            sell_amount = self.config.get("sell_amount", 0.01)
            min_swap_amount = self.config.get("min_swap_amount", 0.01)

            # Vérifier le montant minimum
            if sell_amount < min_swap_amount:
                self.logger.warning(f"Montant de vente {sell_amount} inférieur au minimum {min_swap_amount}")
                return False

            # Check POL pour le gas
            pol_balance = self.from_wei(w3.eth.get_balance(self.wallet_address), 18)
            gas_reserve = 0.05
            if pol_balance < gas_reserve:
                self.logger.warning(f"Pas assez de POL pour le gas ({pol_balance:.4f} POL)")
                return False

            # Balance KNO
            balance_kno = self.from_wei(token_kno.functions.balanceOf(self.wallet_address).call(), 18)
            self.logger.info(f"Balance KNO: {balance_kno:.6f}")
            if balance_kno < min_swap_amount:
                self.logger.warning("Balance KNO insuffisante pour vendre")
                return False

            # Montant à vendre
            amt_decimal = min(sell_amount, balance_kno)
            amt_wei = self.to_wei(amt_decimal, 18)
            self.logger.info(f"Montant KNO à vendre: {amt_decimal:.6f} (configuré: {sell_amount})")

            # Approval
            if not self.approve_token(token_kno, ROUTER, amt_wei, "KNO"):
                return False

            # Balance WPOL avant swap
            old_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()

            # Slippage et min_out
            amounts = router.functions.getAmountsOut(amt_wei, [KNO, WPOL]).call()
            slippage = max(self.get_dynamic_slippage(current_price, ref_price), 3)
            min_out = int(amounts[-1] * (1 - slippage / 100))
            self.logger.info(f"Slippage appliqué: {slippage:.2f}%")

            deadline = int(time.time()) + 600

            # Build transaction swap
            tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                amt_wei,
                min_out,
                [KNO, WPOL],
                self.wallet_address,
                deadline
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": self.get_nonce(),
                "gas": self.config["gas_limit"],
                "gasPrice": self.get_dynamic_gas_price()
            })

            signed = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            self.logger.info(f"Swap KNO → WPOL envoyé: {w3.to_hex(tx_hash)}")

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            success = receipt.status == 1

            if success:
                # Calcul gain réel
                new_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()
                gained_wei = new_balance_wpol - old_balance_wpol
                gained_wpol = self.from_wei(gained_wei, 18)

                self.logger.info(f"Vente réussie ! {amt_decimal:.6f} KNO vendus")
                self.logger.info(f"WPOL réellement reçus: {gained_wpol:.6f}")

                # Unwrap WPOL si besoin
                if not self.unwrap_wpol(gained_wei):
                    self.logger.warning("Unwrap WPOL échoué")

                self.write_price(SELL_PRICE_FILE, current_price)

                # Report au backend
                self.report_trade("sell", gained_wpol, current_price)

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

                # --- Initialisation de la référence de prix si elle n'existe pas ---
                # ref_price = self.config.get("reference_price")

                if self.reference_price is None:
                    self.reference_price = price
                    try:
                        requests.put(
                            f"{self.api_url}/bots/{self.bot_id}/reference-price",
                            json={"price": price}
                        )
                    except:
                        pass

                ref_price = self.reference_price

                    # try:
                    #     self.reference_price = price
                    #     requests.put(f"{self.api_url}/bots/{self.bot_id}/reference-price", json={"price": ref_price})
                    # except Exception as e:
                    #     self.logger.warning(f"Impossible de mettre à jour reference_price: {e}")

                # --- Calcul des conditions de trading basées sur la volatilité ---
                try:
                    volatility = float(self.config.get("volatility_percent", 0.5)) / 100
                except:
                    volatility = 0.001  # fallback 10%
                
                # --- AJOUT DEBUG ---
                delta_percent = (price - ref_price) / ref_price * 100
                self.logger.info(f"Delta % par rapport à référence: {delta_percent:.4f}%")
                
                buy_condition = price <= ref_price * (1 - volatility)
                # buy_condition = True
                sell_condition = price >= ref_price * (1 + volatility)
                # sell_condition = True

                self.logger.info(f"Prix actuel: {price:.6f}€, Référence: {ref_price:.6f}€, Volatilité: {volatility*100:.1f}%")
                self.logger.info(f"Buy condition: {buy_condition}, Sell condition: {sell_condition}")

                # --- Achats ---
                if buy_condition:
                    self.logger.info("Condition d'achat remplie")
                    if self.buy_kno(price):
                        trade_count += 1
                        self.logger.info(f"Achat effectué à {price:.6f}€")
                        # Mise à jour référence après achat
                        try:
                            self.reference_price = price
                            requests.put(f"{self.api_url}/bots/{self.bot_id}/reference-price", json={"price": price})
                        except Exception as e:
                            self.logger.warning(f"Impossible de mettre à jour reference_price: {e}")

                # --- Ventes ---
                elif sell_condition:
                    self.logger.info("Condition de vente remplie")
                    if self.sell_kno(price):
                        trade_count += 1
                        self.logger.info(f"Vente effectuée à {price:.6f}€")
                        # Mise à jour référence après vente
                        try:
                            self.reference_price = price
                            requests.put(f"{self.api_url}/bots/{self.bot_id}/reference-price", json={"price": price})
                        except Exception as e:
                            self.logger.warning(f"Impossible de mettre à jour reference_price: {e}")

                self.write_price(PRICE_FILE, price)
                self.send_heartbeat()
                
                delay = random.randint(30, 50)
                self.logger.info(f"Prochain cycle dans {delay} secondes...")
                await asyncio.sleep(delay)

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
    api_url = os.getenv('API_URL', 'http://mmk.knocoin.com/')
    
    bot = KNOTradingBot(bot_id, api_url)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        logging.error(f"Erreur critique: {e}")

if __name__ == "__main__":
    asyncio.run(main())