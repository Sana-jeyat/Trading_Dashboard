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
bot_id = int(os.getenv("BOT_ID", "1"))  # ID du bot dans le dashboard
API_URL = os.getenv("API_URL_LOCAL", "http://127.0.0.1:3000")  # FastAPI local

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
        self.last_rpc_call = 0
        self.rpc_min_interval = 0.25  # max 4 req/s

        self.cached_gas_price = None
        self.last_gas_update = 0

        self.last_trade_time = 0
        self.trade_cooldown = 300  # 5 min entre trades

        self.allowance_checked = False

        

        
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
                db_ref = bot_data.get("reference_price")
                if db_ref:
                    self.reference_price = float(db_ref)
                # Wallet
                self.wallets = bot_data.get("wallets", [])  # liste de dict {wallet_address, private_key, buy_amount, sell_amount, thresholds}
                
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
    def wait_receipt_slow(self, tx_hash, timeout=180):
        start = time.time()
        while time.time() - start < timeout:
            try:
                self.rpc_sleep()
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    return receipt
            except:
                pass
            time.sleep(5)  # 🔥 polling lent
        return None

    def rpc_sleep(self):
        now = time.time()
        diff = now - self.last_rpc_call
        if diff < self.rpc_min_interval:
            time.sleep(self.rpc_min_interval - diff)
        self.last_rpc_call = time.time()
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

        # ✅ allowance déjà validée → on skip
        if self.allowance_checked:
            return True

        # 🔥 throttle RPC
        self.rpc_sleep()
        current_allowance = token_contract.functions.allowance(
            self.wallet_address, spender
        ).call()

        self.logger.info(f"Allowance {token_name}: {current_allowance}")

        if current_allowance >= amount:
            self.allowance_checked = True
            return True

        # 🔥 approve une seule fois (max)
        self.rpc_sleep()
        tx = token_contract.functions.approve(
            spender,
            w3.to_wei(10**9, "ether")  # allowance quasi infinie
        ).build_transaction({
            "from": self.wallet_address,
            "nonce": self.get_nonce(),
            "gas": 200000,
            "gasPrice": self.get_dynamic_gas_price()
        })

        signed = w3.eth.account.sign_transaction(tx, self.private_key)

        self.rpc_sleep()
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        receipt = self.wait_receipt_slow(tx_hash)
        if not receipt or receipt.status != 1:
            self.logger.error("Approval échouée")
            return False

        self.allowance_checked = True
        self.logger.info("Approval réussie et mise en cache")
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
        if time.time() - self.last_gas_update > 30:
            self.rpc_sleep()
            self.cached_gas_price = w3.eth.gas_price
            self.last_gas_update = time.time()
        return int(self.cached_gas_price * 1.2)

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
        receipt = self.wait_receipt_slow(tx_hash)
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
        receipt = self.wait_receipt_slow(tx_hash)
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
    # def buy_kno(self, current_price):
    #     try:
    #         self.logger.info("Préparation de l'achat KNO...")

    #         # ⛔ évite spam si un trade vient d’être fait
    #         if time.time() - self.last_trade_time < self.trade_cooldown:
    #             self.logger.info("Cooldown actif, achat ignoré")
    #             return False

    #         amt = self.config["buy_amount"]
    #         amt_wei = self.to_wei(amt, 18)

    #         old_kno_balance = token_kno.functions.balanceOf(self.wallet_address).call()

    #         # 🔥 anti rate limit
    #         self.rpc_sleep()
    #         amounts = router.functions.getAmountsOut(amt_wei, [WPOL, KNO]).call()

    #         slippage = max(self.get_dynamic_slippage(current_price, self.reference_price), 3)
    #         min_out = int(amounts[-1] * (1 - slippage / 100))
    #         deadline = int(time.time()) + 600

    #         self.rpc_sleep()
    #         tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
    #             amt_wei,
    #             min_out,
    #             [WPOL, KNO],
    #             self.wallet_address,
    #             deadline
    #         ).build_transaction({
    #             "from": self.wallet_address,
    #             "nonce": self.get_nonce(),
    #             "gas": self.config["gas_limit"],
    #             "gasPrice": self.get_dynamic_gas_price()
    #         })

    #         signed = w3.eth.account.sign_transaction(tx, self.private_key)

    #         # 🔥 RPC limité
    #         self.rpc_sleep()
    #         tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    #         self.logger.info(f"Swap envoyé: {w3.to_hex(tx_hash)}")

    #         # 🔥 receipt lent (clé anti rate limit)
    #         receipt = None
    #         for _ in range(60):  # max 5 minutes
    #             try:
    #                 self.rpc_sleep()
    #                 receipt = w3.eth.get_transaction_receipt(tx_hash)
    #                 if receipt:
    #                     break
    #             except:
    #                 pass
    #             time.sleep(5)

    #         if not receipt:
    #             self.logger.error("Timeout receipt")
    #             return False

    #         if receipt.status != 1:
    #             self.logger.error("Achat échoué - receipt.status=0")
    #             return False

    #         new_kno_balance = token_kno.functions.balanceOf(self.wallet_address).call()
    #         received_wei = new_kno_balance - old_kno_balance
    #         received_kno = self.from_wei(received_wei, 18)

    #         self.logger.info(f"Achat réussi ! {received_kno:.6f} KNO reçus")
    #         self.report_trade("buy", received_kno, current_price)
    #         self.last_trade_time = time.time()
    #         return True

    #     except Exception as e:
    #         err = str(e)

    #         if "-32090" in err or "rate" in err.lower():
    #             delay = random.randint(20, 45)
    #             self.logger.warning(f"Rate limit RPC → pause {delay}s")
    #             time.sleep(delay)
    #             return False

    #         self.logger.error(f"Erreur buy_kno: {e}")
    #         return False

    # --- BUY KNO MODIFIÉ ---
    def buy_kno(self, current_price):
        """Exécute un achat KNO avec protections et reporting"""
        if not hasattr(self, "wallet_last_trade"):
            self.wallet_last_trade = {}
        if not hasattr(self, "allowance_checked"):
            self.allowance_checked = {}  # dict wallet_address -> bool

        wallet_id = self.wallet_address
        last_trade = self.wallet_last_trade.get(wallet_id, 0)

        # Cooldown
        if time.time() - last_trade < self.trade_cooldown:
            self.logger.info(f"Cooldown actif pour {wallet_id}, achat ignoré")
            return False

        try:
            if not self.wallet_address or not self.private_key:
                self.logger.error("Wallet non configuré")
                return False

            self.logger.info(f"Préparation de l'achat KNO pour wallet {wallet_id}...")

            amt = self.config.get("buy_amount", 0.05)
            amt_wei = self.to_wei(amt, 18)

            # Balance WPOL suffisante
            self.rpc_sleep()
            wpol_balance = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)
            self.logger.info(f"WPOL balance wallet {wallet_id}: {wpol_balance:.6f}")
            if wpol_balance < amt:
                self.logger.warning(f"Balance WPOL insuffisante ({wpol_balance:.6f} < {amt})")
                return False

            # Approval par wallet
            if not self.allowance_checked.get(wallet_id, False):
                if not self.approve_token(token_wpol, ROUTER, amt_wei, "WPOL"):
                    return False
                self.allowance_checked[wallet_id] = True

            # Estimation sortie
            self.rpc_sleep()
            amounts = router.functions.getAmountsOut(amt_wei, [WPOL, KNO]).call()
            slippage = max(self.get_dynamic_slippage(current_price, self.reference_price), 3)
            min_out = int(amounts[-1] * (1 - slippage / 100))
            self.logger.info(f"Slippage appliqué: {slippage:.2f}%, min_out: {self.from_wei(min_out, 18):.6f} KNO")

            deadline = int(time.time()) + 600
            nonce = w3.eth.get_transaction_count(self.wallet_address, "pending")
            self.logger.info(f"Nonce utilisé pour swap : {nonce}")

            # Build transaction
            tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                amt_wei, min_out, [WPOL, KNO], self.wallet_address, deadline
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": self.config.get("gas_limit", 500000),
                "gasPrice": self.get_dynamic_gas_price()
            })

            signed = w3.eth.account.sign_transaction(tx, self.private_key)

            # Retry intelligent
            receipt = None
            for attempt in range(5):
                try:
                    self.rpc_sleep()
                    old_balance_kno = token_kno.functions.balanceOf(self.wallet_address).call()
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                    self.logger.info(f"Swap WPOL → KNO envoyé: {w3.to_hex(tx_hash)}")
                    receipt = self.wait_receipt_slow(tx_hash)
                    if receipt and receipt.status == 1:
                        break
                    else:
                        self.logger.warning("Transaction échouée, retry possible...")
                except Exception as e:
                    err_str = str(e).lower()
                    if "-32090" in err_str or "rate" in err_str:
                        delay = random.randint(10, 20)
                        self.logger.warning(f"Rate limit RPC → pause {delay}s")
                        time.sleep(delay)
                    else:
                        self.logger.error(traceback.format_exc())
                        return False

            if not receipt or receipt.status != 1:
                self.logger.error("Achat échoué après retries")
                return False

            # Calcul quantité reçue
            self.rpc_sleep()
            new_balance_kno = token_kno.functions.balanceOf(self.wallet_address).call()
            received_kno = self.from_wei(new_balance_kno - old_balance_kno, 18)
            self.logger.info(f"Achat réussi → {received_kno:.6f} KNO")

            # Report
            self.report_trade("buy", received_kno, current_price)
            self.wallet_last_trade[wallet_id] = time.time()

            return True

        except Exception as e:
            self.logger.error(traceback.format_exc())
            return False


    # def sell_kno(self, current_price):
    #     """Exécute une vente KNO avec protections contre rate-limit et cooldown"""
    #     ref_price = self.reference_price

    #     # Cooldown entre ventes
    #     if time.time() - self.last_trade_time < 60:  # 1 min
    #         self.logger.info("Cooldown actif, vente ignorée")
    #         return False

    #     # Annulation des transactions pending
    #     # if not self.cancel_pending_transactions():
    #     #     self.logger.warning("Impossible d'annuler les transactions en attente, attente 1 min...")
    #     #     time.sleep(60)

    #     try:
    #         if not self.wallet_address or not self.private_key:
    #             self.logger.error("Wallet non configuré pour la vente")
    #             return False

    #         self.logger.info("Début de la vente KNO...")

    #         # Montants configurables
    #         sell_amount = self.config.get("sell_amount", 0.01)
    #         min_swap_amount = self.config.get("min_swap_amount", 0.01)

    #         # Vérifier le montant minimum
    #         if sell_amount < min_swap_amount:
    #             self.logger.warning(f"Montant de vente {sell_amount} inférieur au minimum {min_swap_amount}")
    #             return False

    #         # Check POL pour le gas
    #         self.rpc_sleep()
    #         # pol_balance = self.from_wei(w3.eth.get_balance(self.wallet_address), 18)
    #         # gas_reserve = 0.05
    #         # if pol_balance < gas_reserve:
    #         #     self.logger.warning(f"Pas assez de POL pour le gas ({pol_balance:.4f} POL)")
    #         #     return False

    #         # Balance KNO
    #         self.rpc_sleep()
    #         balance_kno = self.from_wei(token_kno.functions.balanceOf(self.wallet_address).call(), 18)
    #         self.logger.info(f"Balance KNO: {balance_kno:.6f}")
    #         if balance_kno < min_swap_amount:
    #             self.logger.warning("Balance KNO insuffisante pour vendre")
    #             return False

    #         # Montant à vendre
    #         amt_decimal = min(sell_amount, balance_kno)
    #         amt_wei = self.to_wei(amt_decimal, 18)
    #         self.logger.info(f"Montant KNO à vendre: {amt_decimal:.6f} (configuré: {sell_amount})")

    #         # Approval
    #         if not self.approve_token(token_kno, ROUTER, amt_wei, "KNO"):
    #             return False

    #         # Balance WPOL avant swap
    #         self.rpc_sleep()
    #         # old_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()

    #         # Slippage et min_out
    #         self.rpc_sleep()
    #         amounts = router.functions.getAmountsOut(amt_wei, [KNO, WPOL]).call()
    #         slippage = max(self.get_dynamic_slippage(current_price, ref_price), 3)
    #         min_out = int(amounts[-1] * (1 - slippage / 100))
    #         self.logger.info(f"Slippage appliqué: {slippage:.2f}%")

    #         deadline = int(time.time()) + 600

    #         # Build transaction swap
    #        # Avant d'envoyer le swap
    #         nonce = w3.eth.get_transaction_count(self.wallet_address, 'pending')

    #         self.rpc_sleep()
    #         tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
    #             amt_wei,
    #             min_out,
    #             [KNO, WPOL],
    #             self.wallet_address,
    #             deadline
    #         ).build_transaction({
    #             "from": self.wallet_address,
    #             "nonce": nonce,
    #             "gas": self.config["gas_limit"],
    #             "gasPrice": self.get_dynamic_gas_price()
    #         })

    #         signed = w3.eth.account.sign_transaction(tx, self.private_key)

    #         # Retry intelligent sur RPC limit
    #         receipt = None
    #         for attempt in range(5):
    #             try:
    #                 self.rpc_sleep()
    #                 tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    #                 self.logger.info(f"Swap KNO → WPOL envoyé: {w3.to_hex(tx_hash)}")
    #                 receipt = self.wait_receipt_slow(tx_hash)
    #                 if receipt.status == 1:
    #                     break
    #                 else:
    #                     self.logger.warning("Transaction échouée, retry possible...")
    #             except Exception as e:
    #                 if "-32090" in str(e) or "rate" in str(e).lower():
    #                     delay = random.randint(10, 20)
    #                     self.logger.warning(f"Rate limit RPC → pause {delay}s")
    #                     time.sleep(delay)
    #                 else:
    #                     raise

    #         if not receipt or receipt.status != 1:
    #             self.logger.error("Vente échouée après retries")
    #             return False

    #         # Calcul gain réel
    #         self.rpc_sleep()
    #         new_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()
    #         gained_wei = new_balance_wpol - old_balance_wpol
    #         gained_wpol = self.from_wei(gained_wei, 18)

    #         self.logger.info(f"Vente réussie ! {amt_decimal:.6f} KNO vendus")
    #         self.logger.info(f"WPOL réellement reçus: {gained_wpol:.6f}")

    #         # Unwrap WPOL si besoin
    #         if not self.unwrap_wpol(gained_wei):
    #             self.logger.warning("Unwrap WPOL échoué")

    #         # Stocker prix de vente
    #         self.write_price(SELL_PRICE_FILE, current_price)

    #         # Report au backend
    #         self.report_trade("sell", gained_wpol, current_price)

    #         # Update cooldown
    #         self.last_trade_time = time.time()

    #         return True

    #     except Exception as e:
    #         self.logger.error(f"Erreur lors de la vente KNO: {e}")
    #         return False

    def sell_kno(self, current_price):
        """Exécute une vente KNO avec protections et unwrap automatique"""
        ref_price = self.reference_price

        # Cooldown par wallet
        if not hasattr(self, "wallet_last_trade"):
            self.wallet_last_trade = {}
        wallet_id = self.wallet_address
        last_trade = self.wallet_last_trade.get(wallet_id, 0)
        if time.time() - last_trade < self.trade_cooldown:
            self.logger.info(f"Cooldown actif pour {wallet_id}, vente ignorée")
            return False

        try:
            if not self.wallet_address or not self.private_key:
                self.logger.error("Wallet non configuré")
                return False

            self.logger.info(f"Début de la vente KNO pour wallet {wallet_id}...")

            sell_amount = self.config.get("sell_amount", 0.01)
            min_swap_amount = self.config.get("min_swap_amount", 0.01)

            # Balance KNO
            self.rpc_sleep()
            balance_kno = self.from_wei(token_kno.functions.balanceOf(self.wallet_address).call(), 18)
            if balance_kno < min_swap_amount:
                self.logger.warning("Balance KNO insuffisante pour vendre")
                return False

            amt_decimal = min(sell_amount, balance_kno)
            amt_wei = self.to_wei(amt_decimal, 18)
            self.logger.info(f"Vente de {amt_decimal:.6f} KNO")

            # Approval
            if not self.approve_token(token_kno, ROUTER, amt_wei, "KNO"):
                return False

            # Estimation sortie
            self.rpc_sleep()
            amounts = router.functions.getAmountsOut(amt_wei, [KNO, WPOL]).call()
            slippage = max(self.get_dynamic_slippage(current_price, ref_price), 3)
            min_out = int(amounts[-1] * (1 - slippage / 100))

            deadline = int(time.time()) + 600
            nonce = w3.eth.get_transaction_count(self.wallet_address, "pending")

            # Build transaction swap
            tx = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                amt_wei, min_out, [KNO, WPOL], self.wallet_address, deadline
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": nonce,
                "gas": self.config["gas_limit"],
                "gasPrice": self.get_dynamic_gas_price()
            })

            signed = w3.eth.account.sign_transaction(tx, self.private_key)

            # Retry intelligent sur RPC limit
            receipt = None
            for attempt in range(5):
                try:
                    self.rpc_sleep()
                    old_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                    self.logger.info(f"Swap KNO → WPOL envoyé: {w3.to_hex(tx_hash)}")
                    receipt = self.wait_receipt_slow(tx_hash)
                    if receipt and receipt.status == 1:
                        break
                    else:
                        self.logger.warning("Transaction échouée, retry possible...")
                except Exception as e:
                    err_str = str(e).lower()
                    if "-32090" in err_str or "rate" in err_str:
                        delay = random.randint(10, 20)
                        self.logger.warning(f"Rate limit RPC → pause {delay}s")
                        time.sleep(delay)
                    else:
                        raise

            if not receipt or receipt.status != 1:
                self.logger.error("Vente échouée après retries")
                return False

            # Balance WPOL après swap
            self.rpc_sleep()
            new_balance_wpol = token_wpol.functions.balanceOf(self.wallet_address).call()
            gained_wpol = self.from_wei(new_balance_wpol - old_balance_wpol, 18)

            self.logger.info(f"Vente réussie → {gained_wpol:.6f} WPOL")

            # Unwrap automatique
            if gained_wpol > 0:
                amt_wei = self.to_wei(gained_wpol, 18)
                if self.unwrap_wpol(amt_wei):
                    self.logger.info(f"Unwrap réussi → {gained_wpol:.6f} POL")
                else:
                    self.logger.warning("Unwrap échoué")

            # Report au dashboard
            self.report_trade("sell", gained_wpol, current_price)

            # Update cooldown
            self.wallet_last_trade[wallet_id] = time.time()

            # Stocker dernier prix de vente
            self.write_price(SELL_PRICE_FILE, current_price)

            return True

        except Exception as e:
            self.logger.error(f"Erreur vente KNO: {e}")
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
        """Démarre le bot de trading multi-wallets"""
        self.is_running = True

        # Charger la config principale
        if not await self.load_config():
            self.logger.error("Impossible de charger la configuration")
            return

        # Charger les wallets depuis le dashboard
        self.wallets = await self.get_wallet_config()
        if not self.wallets:
            self.logger.warning("Aucun wallet configuré, utilisation du wallet unique")
            self.wallets = [{"wallet_address": self.wallet_address, "private_key": self.private_key}]

        self.update_status("active")
        self.logger.info(f"Bot trading KNO démarré avec {len(self.wallets)} wallet(s)")

        try:
            while self.is_running:
                # Recharger config pour avoir les derniers montants
                await self.load_config()

                # Récupérer prix actuel
                price = self.get_price_kno_eur() or 1.23
                if not price:
                    self.logger.warning("Impossible de récupérer le prix, attente 1 min...")
                    await asyncio.sleep(60)
                    continue

                # Initialisation de la référence si elle n'existe pas
                if not self.reference_price:
                    self.logger.info("Aucune référence définie, initialisation avec le prix actuel")
                    self.reference_price = price
                    try:
                        requests.put(f"{self.api_url}/bots/{self.bot_id}/reference-price", json={"price": price})
                    except Exception as e:
                        self.logger.warning(f"Impossible d'initialiser reference_price: {e}")

                ref_price = self.reference_price
                volatility = float(self.config.get("volatility_percent", 0.5)) / 100
                delta_percent = (price - ref_price) / ref_price * 100
                self.logger.info(f"Prix actuel: {price:.6f}€, Référence: {ref_price:.6f}€, Delta: {delta_percent:.4f}%")

                # --- Boucle sur tous les wallets ---
                for wallet in self.wallets:
                    wallet_address = wallet["wallet_address"]
                    private_key = wallet["private_key"]

                    # Mettre à jour temporairement pour utiliser buy_kno / sell_kno
                    self.wallet_address = wallet_address
                    self.private_key = private_key

                    # Montants spécifiques par wallet
                    if "buy_amount" in wallet:
                        self.config["buy_amount"] = wallet["buy_amount"]
                    if "sell_amount" in wallet:
                        self.config["sell_amount"] = wallet["sell_amount"]

                    # Conditions trading
                    # buy_condition = price <= ref_price * (1 - volatility)
                    # sell_condition = price >= ref_price * (1 + volatility)
                    buy_condition = True
                    sell_condition = False

                    for wallet in self.wallets:
                        self.wallet_address = wallet["wallet_address"]
                        self.private_key = wallet["private_key"]

                        if "buy_amount" in wallet:
                            self.config["buy_amount"] = wallet["buy_amount"]
                        if "sell_amount" in wallet:
                            self.config["sell_amount"] = wallet["sell_amount"]

                        self.logger.info(f"Wallet prêt pour trading: {self.wallet_address}")
                        wpol_balance = self.from_wei(token_wpol.functions.balanceOf(self.wallet_address).call(), 18)
                        kno_balance = self.from_wei(token_kno.functions.balanceOf(self.wallet_address).call(), 18)
                        self.logger.info(f"Balances: WPOL={wpol_balance:.6f}, KNO={kno_balance:.6f}")


                    # --- Achat ---
                    if buy_condition:
                        self.logger.info(f"Achat pour wallet {wallet_address}")
                        if self.buy_kno(price):
                            # Mise à jour référence après achat
                            self.reference_price = price
                            try:
                                requests.put(f"{self.api_url}/bots/{self.bot_id}/reference-price", json={"price": price})
                            except Exception as e:
                                self.logger.warning(f"Impossible de mettre à jour reference_price: {e}")

                    # --- Vente ---
                    elif sell_condition:
                        self.logger.info(f"Vente pour wallet {wallet_address}")
                        if self.sell_kno(price):
                            # Mise à jour référence après vente
                            self.reference_price = price
                            try:
                                requests.put(f"{self.api_url}/bots/{self.bot_id}/reference-price", json={"price": price})
                            except Exception as e:
                                self.logger.warning(f"Impossible de mettre à jour reference_price: {e}")

                # Stocker prix pour debug / historique
                self.write_price("last_price.txt", price)

                # Envoyer heartbeat au dashboard
                self.send_heartbeat()

                # Pause avant prochain cycle (5 à 10 minutes aléatoire)
                delay = random.randint(5, 10)
                self.logger.info(f"Prochain cycle dans {delay} minutes...")
                await asyncio.sleep(delay * 60)

        except KeyboardInterrupt:
            self.logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"Erreur boucle principale: {e}")
        finally:
            self.update_status("offline")
            self.logger.info("Bot KNO multi-wallet arrêté")


    def stop(self):
        """Arrête le bot"""
        self.is_running = False
        self.logger.info("Arrêt du bot demandé")

async def main():
    bot_id = int(os.getenv('BOT_ID', '1'))
    API_URL = os.getenv("API_URL", "http://127.0.0.1:3000")
    api_url = API_URL
    
    bot = KNOTradingBot(bot_id, api_url)
    bot.logger.info(f"Démarrage du bot KNO avec ID {bot_id} et API_URL {api_url}")

    try:
        await bot.start()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        logging.error(f"Erreur critique: {e}")

if __name__ == "__main__":
    asyncio.run(main())